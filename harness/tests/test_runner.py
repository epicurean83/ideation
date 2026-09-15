"""러너·승인 페이지 테스트. 실제 SDK 대신 가짜 클라이언트를 쓰므로 API를 부르지 않는다."""

import fcntl
import socket
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import anyio
import pytest
from claude_agent_sdk import RateLimitEvent, RateLimitInfo, ResultMessage

import nightshift.approval as A
import nightshift.runner as R
from nightshift.policy import Action, Config

CFG = Config.load(Path(__file__).parents[1] / "nightshift.toml")
NIGHT = datetime(2026, 9, 15, 22, 30, tzinfo=CFG.tz)  # 화요일 밤
WEEK_RESET = int(datetime(2026, 9, 22, 4, tzinfo=CFG.tz).timestamp())


def event(util: float) -> RateLimitEvent:
    raw = {"status": "allowed", "unifiedWindows": {"seven_day": {"utilization": util, "resetsAt": WEEK_RESET}}}
    return RateLimitEvent(rate_limit_info=RateLimitInfo(status="allowed", raw=raw), uuid="u", session_id="s")


def result(is_error: bool = False) -> ResultMessage:
    return ResultMessage(subtype="success", duration_ms=1000, duration_api_ms=900, is_error=is_error, num_turns=1,
                         session_id="s")


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class FakeClient:
    """job 세션: script의 메시지를 delay 간격으로 흘린다. probe 세션(max_turns=1): 현재 probe_util을 이벤트로 준다."""

    probe_util = 0.30
    job_script: list = []
    job_delay = 0.0
    interrupt_raises = False
    interrupted = False
    probes = 0
    jobs = 0

    def __init__(self, options):
        self.is_probe = options.max_turns == 1

    async def __aenter__(self):
        if not self.is_probe:
            FakeClient.jobs += 1
        return self

    async def __aexit__(self, *exc):
        return False

    async def query(self, prompt):
        pass

    async def interrupt(self):
        FakeClient.interrupted = True
        if FakeClient.interrupt_raises:
            raise Exception("Control request timeout: interrupt")

    async def receive_response(self):
        if self.is_probe:
            FakeClient.probes += 1
            yield event(FakeClient.probe_util)
            yield result()
            return
        for msg in FakeClient.job_script:
            await anyio.sleep(FakeClient.job_delay)
            if FakeClient.interrupted and not FakeClient.interrupt_raises:
                yield result(is_error=True)
                return
            yield msg


@pytest.fixture
def night(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "STATE_DIR", tmp_path)
    monkeypatch.setattr(R, "EVENTS_FILE", tmp_path / "events.jsonl")
    monkeypatch.setattr(R, "LOCK_FILE", tmp_path / "nightshift.lock")
    monkeypatch.setattr(R, "TOKEN_FILE", tmp_path / "approval-token")
    monkeypatch.setattr(R, "PIPELINE", tmp_path / "ideas" / "PIPELINE.md")
    monkeypatch.setattr(R, "now_in", lambda cfg: NIGHT)
    monkeypatch.setattr(R, "ClaudeSDKClient", FakeClient)
    monkeypatch.setattr(R, "CHECK_EVERY_S", 0.01)
    monkeypatch.setattr(R, "INTERRUPT_GRACE_S", 0.2)
    monkeypatch.setattr(R, "FAILURE_BACKOFF_S", 0.01)
    monkeypatch.setattr(R, "APPROVAL_POLL_S", 0.01)
    monkeypatch.setattr(A, "tailscale_ip", lambda: "127.0.0.1")
    (tmp_path / "ideas").mkdir()
    (tmp_path / "prompt.md").write_text("job")
    cfg = Config(**{**CFG.__dict__, "prompt_file": str(tmp_path / "prompt.md"), "approval_port": free_port()})
    FakeClient.probe_util, FakeClient.job_script, FakeClient.job_delay = 0.30, [], 0.0
    FakeClient.interrupt_raises = FakeClient.interrupted = False
    FakeClient.probes = FakeClient.jobs = 0
    n = R.Night(cfg)
    yield n
    n.close()


def run(coro_fn, *args):
    return anyio.run(coro_fn, *args)


def productive_job_factory(calls, stop_after=None):
    async def job(n, d, sd):
        calls.append(d.action)
        (R.PIPELINE.parent / f"out-{len(calls)}.md").write_text("x")
        if stop_after and len(calls) >= stop_after:
            sd.set()
        return "done"
    return job


# ── 70% 승인 흐름 ──────────────────────────────────────────────────────────────


def test_below_threshold_runs_without_asking(night, monkeypatch):
    calls = []
    monkeypatch.setattr(R, "run_job", productive_job_factory(calls, stop_after=3))
    run(R.loop, night, anyio.Event(), False)
    assert len(calls) == 3 and night.gate is None


def approve_when_pending(gate_holder, choice, times=1):
    """백그라운드에서 대기 요청이 뜨면 choice로 답한다."""
    async def answer():
        answered = 0
        while answered < times:
            await anyio.sleep(0.01)
            gate = gate_holder.gate
            if gate and gate.pending:
                gate.decide(gate.pending.id, choice)
                answered += 1
    return answer


def test_above_threshold_asks_before_every_job(night, monkeypatch):
    FakeClient.probe_util = 0.75
    calls = []
    monkeypatch.setattr(R, "run_job", productive_job_factory(calls, stop_after=2))

    async def main():
        shutdown = anyio.Event()
        async with anyio.create_task_group() as tg:
            tg.start_soon(approve_when_pending(night, "approve", times=2))
            await R.loop(night, shutdown, False)
            tg.cancel_scope.cancel()

    run(main)
    assert len(calls) == 2
    assert [r.choice for r in night.gate.history] == ["approve", "approve"]  # 작업마다 한 번씩 물었다


def test_deny_ends_the_night(night, monkeypatch):
    FakeClient.probe_util = 0.75
    calls = []
    monkeypatch.setattr(R, "run_job", productive_job_factory(calls))

    async def main():
        async with anyio.create_task_group() as tg:
            tg.start_soon(approve_when_pending(night, "deny"))
            await R.loop(night, anyio.Event(), False)
            tg.cancel_scope.cancel()

    run(main)
    assert calls == []


def test_no_answer_until_deadline_ends_the_night(night, monkeypatch):
    FakeClient.probe_util = 0.75
    ticks = {"n": 0}

    def clock(cfg):
        ticks["n"] += 1
        return NIGHT if ticks["n"] < 40 else datetime(2026, 9, 16, 3, 56, tzinfo=CFG.tz)  # 응답 기한 03:55 지남

    monkeypatch.setattr(R, "now_in", clock)
    calls = []
    monkeypatch.setattr(R, "run_job", productive_job_factory(calls))
    run(R.loop, night, anyio.Event(), False)
    assert calls == [] and night.gate.history[-1].choice == "expired"


def test_missing_tailscale_ends_the_night(night, monkeypatch):
    FakeClient.probe_util = 0.75
    monkeypatch.setattr(A, "tailscale_ip", lambda: None)
    calls = []
    monkeypatch.setattr(R, "run_job", productive_job_factory(calls))
    run(R.loop, night, anyio.Event(), False)
    assert calls == []


def test_approval_page_roundtrip_over_http(tmp_path):
    token = A.load_token(tmp_path / "tok")
    assert (tmp_path / "tok").stat().st_mode & 0o777 == 0o600
    gate = A.ApprovalGate(host="127.0.0.1", port=free_port(), token=token)
    gate.start()
    try:
        req = gate.open_request({"주간 사용률": "75% (기준 70%)"})
        base = f"http://127.0.0.1:{gate.port}"
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(f"{base}/?t=wrong")
        assert e.value.code == 403
        page = urllib.request.urlopen(gate.url).read().decode()
        assert "75% (기준 70%)" in page and req.id in page
        body = urllib.parse.urlencode({"t": token, "id": req.id, "choice": "approve"}).encode()
        urllib.request.urlopen(urllib.request.Request(f"{base}/", data=body, method="POST"))
        assert req.choice == "approve"
        # 이미 결정된 요청은 다시 바꿀 수 없다
        assert not gate.decide(req.id, "deny") and req.choice == "approve"
    finally:
        gate.stop()


def test_approval_page_escapes_html(tmp_path):
    gate = A.ApprovalGate(host="127.0.0.1", port=0, token="t")
    gate.open_request({"<script>": "<img src=x onerror=1>"})
    page = A.render(gate)
    assert "<script>" not in page and "&lt;img" in page


# ── 작업 세션 ─────────────────────────────────────────────────────────────────


def test_running_job_is_interrupted_by_time_rule(night, monkeypatch):
    ticks = {"n": 0}

    def clock(cfg):
        ticks["n"] += 1
        return NIGHT if ticks["n"] < 5 else datetime(2026, 9, 16, 3, 56, tzinfo=CFG.tz)

    async def main():
        await R.probe(night)
        d = night.decision(starting_job=True)
        assert d.action is Action.RUN
        monkeypatch.setattr(R, "now_in", clock)
        FakeClient.job_script = [object()] * 200
        FakeClient.job_delay = 0.01
        return await R.run_job(night, d, anyio.Event())

    assert run(main) == "stopped" and FakeClient.interrupted


def test_job_crossing_threshold_is_finished(night):
    async def main():
        await R.probe(night)
        d = night.decision(starting_job=True)
        FakeClient.job_script = [event(0.72), event(0.90), result()]
        return await R.run_job(night, d, anyio.Event())

    assert run(main) == "done" and not FakeClient.interrupted


def test_interrupt_exception_does_not_kill_runner(night):
    async def main():
        await R.probe(night)
        d = night.decision(starting_job=True)
        FakeClient.job_script = [object()] * 1000
        FakeClient.job_delay = 0.01
        FakeClient.interrupt_raises = True
        shutdown = anyio.Event()
        shutdown.set()
        return await R.run_job(night, d, shutdown)

    assert run(main) == "stopped"


def test_run_job_catches_session_exceptions(night, monkeypatch):
    class Boom(FakeClient):
        async def query(self, prompt):
            if not self.is_probe:
                raise RuntimeError("CLI died")

    monkeypatch.setattr(R, "ClaudeSDKClient", Boom)

    async def main():
        await R.probe(night)
        return await R.run_job(night, night.decision(starting_job=True), anyio.Event())

    assert run(main) == "error"


# ── 루프 ─────────────────────────────────────────────────────────────────────


def test_loop_stops_after_repeated_failures(night, monkeypatch):
    calls = []

    async def failing_job(n, d, shutdown):
        calls.append(1)
        return "error"

    monkeypatch.setattr(R, "run_job", failing_job)
    run(R.loop, night, anyio.Event(), False)
    assert len(calls) == R.MAX_CONSECUTIVE_FAILURES


def test_loop_stops_after_consecutive_idle_jobs(night, monkeypatch):
    calls = []

    async def idle_job(n, d, shutdown):
        calls.append(1)
        return "done"

    monkeypatch.setattr(R, "run_job", idle_job)
    run(R.loop, night, anyio.Event(), False)
    assert len(calls) == R.MAX_IDLE_JOBS


def test_loop_stops_when_usage_cannot_be_read(night, monkeypatch):
    class Silent(FakeClient):
        async def receive_response(self):
            yield result()

    calls = []
    monkeypatch.setattr(R, "ClaudeSDKClient", Silent)
    monkeypatch.setattr(R, "run_job", productive_job_factory(calls))
    run(R.loop, night, anyio.Event(), False)
    assert calls == []


def test_loop_stops_at_target(night, monkeypatch):
    rows = "".join(f"| i{i} | x | S5 | G4 | 통과(실증 대기) | - | - |\n" for i in range(CFG.target_passed))
    R.PIPELINE.write_text("| slug | 문제 | 단계 | 게이트 | 판정 | 다음 | 날짜 |\n|---|---|---|---|---|---|---|\n" + rows)
    calls = []
    monkeypatch.setattr(R, "run_job", productive_job_factory(calls))
    run(R.loop, night, anyio.Event(), False)
    assert calls == []


def test_second_runner_exits_when_lock_is_held(night, monkeypatch):
    ran = []

    async def fake_loop(*a):
        ran.append(1)

    monkeypatch.setattr(R, "loop", fake_loop)
    with R.LOCK_FILE.open("w") as held:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run(R.run, night.cfg, False)
    assert ran == []


def test_tests_do_not_touch_real_state(night):
    assert R.STATE_DIR != R.HARNESS / "state" and R.TOKEN_FILE.parent == R.STATE_DIR


def test_passed_count_ignores_spacing(tmp_path):
    p = tmp_path / "PIPELINE.md"
    p.write_text(
        "| slug | 문제 | 단계 | 게이트 | 판정 | 다음 | 날짜 |\n|---|---|---|---|---|---|---|\n"
        "| a | x | S5 | G4 | 통과(실증 대기) | - | - |\n"
        "| b | x | S5 | G4 | 통과 (실증 대기) | - | - |\n"
        "| c | x | S3 | G2 | 통과 (조건부) | - | - |\n"
    )
    assert R.passed_count(p) == 2


# ── 자기 보호 ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("tool,inp", [
    ("Write", {"file_path": str(R.HARNESS / "nightshift" / "policy.py")}),
    ("Edit", {"file_path": "harness/nightshift.toml"}),
    ("Write", {"file_path": "~/.config/systemd/user/ideation-nightshift.timer"}),
    ("Read", {"file_path": "~/.claude/.credentials.json"}),
    ("Read", {"file_path": str(R.HARNESS / "state" / "approval-token")}),
    ("Bash", {"command": "cat harness/state/approval-token"}),
    ("Bash", {"command": "git push origin HEAD"}),
    ("Bash", {"command": "systemctl --user stop ideation-nightshift-kill.timer"}),
    ("Bash", {"command": "sed -i s/0.70/0.99/ harness/nightshift.toml"}),
    ("Write", {"file_path": str(R.HARNESS / ".venv" / "lib" / "python3.12" / "site-packages" / "evil.pth")}),
    ("Write", {"file_path": ".claude/settings.json"}),
    ("Edit", {"file_path": "~/.claude/settings.json"}),
    ("Write", {"file_path": "harness/uv.lock"}),
    ("Bash", {"command": "git -C . push"}),
    ("Bash", {"command": "cd ideas && git --no-pager push origin HEAD"}),
    ("Bash", {"command": "git -c core.x=y push"}),
    ("Bash", {"command": "echo '{}' > .claude/settings.local.json"}),
])
def test_guard_denies_tampering(tool, inp):
    assert R.deny_reason(tool, inp)


@pytest.mark.parametrize("tool,inp", [
    ("Write", {"file_path": "ideas/ai-care/PROGRESS.md"}),
    ("Read", {"file_path": "harness/recipes/pain.yaml"}),
    ("Bash", {"command": "git commit -m 'x: G0 통과'"}),
    ("Bash", {"command": "git log --oneline | head"}),
    ("Bash", {"command": "git add ideas/smart-push-notify/ ideas/PIPELINE.md"}),
    ("Bash", {"command": "git commit -m 'smart-push-notify: G0 통과 — push 알림 피로도'"}),
    ("Bash", {"command": "jq . ideas/x/research/t/sources/settings.json"}),
    ("Skill", {"skill": "crucible", "args": "Decision 모드"}),
    ("Skill", {"skill": "deepdive", "args": "deep q"}),
])
def test_guard_allows_normal_work(tool, inp):
    assert R.deny_reason(tool, inp) is None
