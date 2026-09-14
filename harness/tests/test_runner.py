"""러너 테스트. 실제 SDK 대신 가짜 클라이언트를 쓰므로 API를 부르지 않는다."""

from datetime import datetime, timedelta
from pathlib import Path

import anyio
import pytest
from claude_agent_sdk import RateLimitEvent, RateLimitInfo, ResultMessage

import nightshift.runner as R
from nightshift.policy import Action, Config

CFG = Config.load(Path(__file__).parents[1] / "nightshift.toml")
NIGHT = datetime(2026, 9, 20, 22, 30, tzinfo=CFG.tz)  # 일요일 밤, 주간 초기화 화 04:00
WEEK_RESET = int(datetime(2026, 9, 22, 4, tzinfo=CFG.tz).timestamp())


def event(util: float) -> RateLimitEvent:
    raw = {"status": "allowed", "unifiedWindows": {"seven_day": {"utilization": util, "resetsAt": WEEK_RESET}}}
    return RateLimitEvent(rate_limit_info=RateLimitInfo(status="allowed", raw=raw), uuid="u", session_id="s")


def result(is_error: bool = False) -> ResultMessage:
    return ResultMessage(subtype="success", duration_ms=1000, duration_api_ms=900, is_error=is_error, num_turns=1,
                         session_id="s")


class FakeClient:
    """job 세션: script의 메시지를 delay 간격으로 흘린다. probe 세션(max_turns=1): 현재 probe_util을 이벤트로 준다."""

    probe_util = 0.80
    job_script: list = []
    job_delay = 0.0
    interrupt_raises = False
    interrupted = False
    probes = 0

    def __init__(self, options):
        self.is_probe = options.max_turns == 1

    async def __aenter__(self):
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
    monkeypatch.setattr(R, "STATE_FILE", tmp_path / "nightshift.json")
    monkeypatch.setattr(R, "EVENTS_FILE", tmp_path / "events.jsonl")
    monkeypatch.setattr(R, "LOCK_FILE", tmp_path / "nightshift.lock")
    monkeypatch.setattr(R, "PIPELINE", tmp_path / "PIPELINE.md")
    monkeypatch.setattr(R, "now_in", lambda cfg: NIGHT)
    monkeypatch.setattr(R, "ClaudeSDKClient", FakeClient)
    monkeypatch.setattr(R, "CHECK_EVERY_S", 0.01)
    monkeypatch.setattr(R, "INTERRUPT_GRACE_S", 0.2)
    monkeypatch.setattr(R, "FAILURE_BACKOFF_S", 0.01)
    (tmp_path / "prompt.md").write_text("job")
    cfg = Config(**{**CFG.__dict__, "prompt_file": str(tmp_path / "prompt.md"), "probe_every": timedelta(seconds=0.05)})
    FakeClient.probe_util, FakeClient.job_script, FakeClient.job_delay = 0.80, [], 0.0
    FakeClient.interrupt_raises = FakeClient.interrupted = False
    FakeClient.probes = 0
    return R.Night(cfg)


def run(coro_fn, *args):
    return anyio.run(coro_fn, *args)


# ── B1: 작업 도중 주간 사용률이 상한에 닿으면 멈춘다 ─────────────────────────────


def test_running_job_is_interrupted_when_probe_sees_weekly_ceiling(night):
    async def main():
        assert await R.probe(night)
        d = night.decision(starting_job=True)
        assert d.action is Action.RUN        # W=1, N=2, base 0.80 → 상한 0.83
        FakeClient.job_script = [event(0.80)] * 200
        FakeClient.job_delay = 0.01

        async def burn():                      # 작업이 도는 사이 사용률이 오른다
            await anyio.sleep(0.1)
            FakeClient.probe_util = 0.83

        async with anyio.create_task_group() as tg:
            tg.start_soon(burn)
            status = await R.run_job(night, d, anyio.Event())
        return status

    assert run(main) == "stopped"
    assert FakeClient.interrupted
    assert night.state["job_cost_samples"] == [pytest.approx(0.03)]


# ── S2: interrupt가 예외를 던져도 러너가 죽지 않는다 ─────────────────────────────


def test_interrupt_exception_does_not_kill_runner(night):
    async def main():
        await R.probe(night)
        d = night.decision(starting_job=True)
        FakeClient.job_script = [event(0.80)] * 1000
        FakeClient.job_delay = 0.01
        FakeClient.interrupt_raises = True
        shutdown = anyio.Event()
        shutdown.set()                         # 즉시 종료 신호 → stop → interrupt 예외
        return await R.run_job(night, d, shutdown)

    assert run(main) == "stopped"


def test_loop_survives_job_exceptions_and_stops_after_repeated_failures(night, monkeypatch):
    calls = []

    async def failing_job(n, d, shutdown):
        calls.append(1)
        return "error"

    monkeypatch.setattr(R, "run_job", failing_job)
    run(R.loop, night, anyio.Event(), False)
    assert len(calls) == R.MAX_CONSECUTIVE_FAILURES


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


# ── B2: probe가 실패하면 fail-closed ────────────────────────────────────────────


def test_loop_stops_when_usage_cannot_be_read(night, monkeypatch):
    class Silent(FakeClient):
        async def receive_response(self):
            yield result()

    started = []

    async def job(*a):
        started.append(1)
        return "done"

    monkeypatch.setattr(R, "ClaudeSDKClient", Silent)
    monkeypatch.setattr(R, "run_job", job)
    run(R.loop, night, anyio.Event(), False)
    assert started == []


# ── S3·S4·S5 ─────────────────────────────────────────────────────────────────


def test_corrupt_state_file_is_moved_aside(tmp_path):
    f = tmp_path / "nightshift.json"
    f.write_text('{"daytime_samples": [0.1')
    assert R.load_state(f) == {}
    assert list(tmp_path.glob("nightshift.json.corrupt-*"))


def test_state_defaults_follow_patched_paths(night):
    # 기본 경로를 import 시점에 묶으면 테스트가 실제 harness/state를 오염시킨다 (실제로 한 번 그랬다)
    R.save_state({"x": 1})
    assert R.STATE_FILE.parent != R.HARNESS / "state"
    assert R.load_state() == {"x": 1}


def test_state_is_written_atomically(tmp_path):
    f = tmp_path / "nightshift.json"
    R.save_state({"a": 1}, f)
    assert R.load_state(f) == {"a": 1}
    assert not (tmp_path / "nightshift.json.tmp").exists()


def test_night_base_survives_restart(night):
    run(R.probe, night)
    assert list(night.base.values()) == [0.80]
    FakeClient.probe_util = 0.82
    again = R.Night(night.cfg)
    run(R.probe, again)
    assert list(again.base.values()) == [0.80]  # 재시작해도 야간 기준은 첫 관측값


def test_second_runner_exits_when_lock_is_held(night, monkeypatch):
    import fcntl

    ran = []

    async def fake_loop(*a):
        ran.append(1)

    monkeypatch.setattr(R, "loop", fake_loop)
    with R.LOCK_FILE.open("w") as held:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run(R.run, night.cfg, False)
    assert ran == []


def test_passed_count_ignores_spacing(tmp_path):
    p = tmp_path / "PIPELINE.md"
    p.write_text(
        "| slug | 문제 | 단계 | 게이트 | 판정 | 다음 | 날짜 |\n|---|---|---|---|---|---|---|\n"
        "| a | x | S5 | G4 | 통과(실증 대기) | - | - |\n"
        "| b | x | S5 | G4 | 통과 (실증 대기) | - | - |\n"
        "| c | x | S3 | G2 | 통과 (조건부) | - | - |\n"
    )
    assert R.passed_count(p) == 2


# ── S6: 감시 대상이 감시 장치를 못 건드린다 ─────────────────────────────────────


@pytest.mark.parametrize("tool,inp", [
    ("Write", {"file_path": str(R.HARNESS / "nightshift" / "policy.py")}),
    ("Edit", {"file_path": "harness/nightshift.toml"}),
    ("Write", {"file_path": "~/.config/systemd/user/ideation-nightshift.timer"}),
    ("Read", {"file_path": "~/.claude/.credentials.json"}),
    ("Bash", {"command": "git push origin HEAD"}),
    ("Bash", {"command": "systemctl --user stop ideation-nightshift-kill.timer"}),
    ("Bash", {"command": "sed -i s/22/09/ harness/nightshift.toml"}),
    # 2차 리뷰 R2-3에서 찾은 우회 경로
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
    assert R.deny_reason(tool, inp, heavy_allowed=True)


@pytest.mark.parametrize("tool,inp", [
    ("Write", {"file_path": "ideas/ai-care/PROGRESS.md"}),
    ("Read", {"file_path": "harness/recipes/pain.yaml"}),
    ("Bash", {"command": "git commit -m 'x: G0 통과'"}),
    ("Write", {"file_path": "ideas/x/research/t/plan.md", "content": "plan\n승인\n"}),
    ("Skill", {"skill": "deepdive", "args": "shallow 카페 원두 찌꺼기 처리 방식"}),
    ("Bash", {"command": "git log --oneline | head"}),
    # 3차 리뷰 R3-1 오탐: slug·커밋 메시지·리서치 원자료 속 push / settings.json
    ("Bash", {"command": "git add ideas/smart-push-notify/ ideas/PIPELINE.md"}),
    ("Bash", {"command": "git commit -m 'smart-push-notify: G0 통과 — push 알림 피로도'"}),
    ("Bash", {"command": "jq . ideas/x/research/t/sources/settings.json"}),
    ("Skill", {"skill": "deepdive", "args": "깊이 shallow로 카페 원두"}),
    ("Skill", {"skill": "crucible", "args": "--council 아이디어"}),
])
def test_guard_allows_normal_work(tool, inp):
    assert R.deny_reason(tool, inp, heavy_allowed=False) is None


def test_guard_blocks_heavy_skills_only_when_headroom_is_small():
    assert R.deny_reason("Skill", {"skill": "crucible", "args": "Decision 모드"}, heavy_allowed=False)
    assert R.deny_reason("Skill", {"skill": "deepdive", "args": "q"}, heavy_allowed=False)
    assert R.deny_reason("Skill", {"skill": "deepdive", "args": "deep q"}, heavy_allowed=False)
    assert R.deny_reason("Skill", {"skill": "deepdive", "args": "deep q"}, heavy_allowed=True) is None
    assert R.deny_reason("Skill", {"skill": "deepdive", "args": "'shallow' vs deep 비교 (deep)"}, heavy_allowed=False)
    assert R.deny_reason("Skill", {"skill": "crucible", "args": "Decision 모드"}, heavy_allowed=True) is None


# ── R2-2: 진전 없는 작업이 이어지면 그날 밤을 끝낸다 ─────────────────────────────


def test_loop_stops_after_consecutive_idle_jobs(night, monkeypatch):
    calls = []

    async def idle_job(n, d, shutdown):
        calls.append(1)
        return "done"

    monkeypatch.setattr(R, "run_job", idle_job)
    run(R.loop, night, anyio.Event(), False)
    assert len(calls) == R.MAX_IDLE_JOBS


def test_loop_keeps_going_while_jobs_make_progress(night, monkeypatch):
    calls = []
    (R.PIPELINE.parent / "idea").mkdir()

    async def productive_job(n, d, shutdown):
        calls.append(1)
        (R.PIPELINE.parent / "idea" / f"out-{len(calls)}.md").write_text("x")
        if len(calls) == 5:
            shutdown.set()
        return "done"

    monkeypatch.setattr(R, "run_job", productive_job)
    shutdown = anyio.Event()
    run(R.loop, night, shutdown, False)
    assert len(calls) == 5


# ── R2-4: 작업 중 정보가 오래되면 끊기 전에 먼저 다시 읽는다 ──────────────────────


def test_stale_usage_mid_job_triggers_probe_not_stop(night, monkeypatch):
    clock = {"now": NIGHT}
    monkeypatch.setattr(R, "now_in", lambda cfg: clock["now"])
    cfg = Config(**{**night.cfg.__dict__, "probe_every": timedelta(hours=1)})  # 주기 probe는 끈다
    night.cfg = cfg

    async def main():
        await R.probe(night)
        d = night.decision(starting_job=True)
        FakeClient.job_script = [object()] * 3 + [result()]  # 한도 이벤트 없는 메시지만 → 정보가 실제로 낡는다
        FakeClient.job_delay = 0.05

        async def age():
            await anyio.sleep(0.02)
            clock["now"] = NIGHT + cfg.usage_max_age + timedelta(minutes=1)  # 사용률이 오래됨

        async with anyio.create_task_group() as tg:
            tg.start_soon(age)
            return await R.run_job(night, d, anyio.Event())

    assert run(main) == "done"                 # 예전 동작이면 PROBE를 멈춤 사유로 보고 "stopped"
    assert FakeClient.probes >= 3              # 시작 전 + 작업 중(재확인) + 작업 후
