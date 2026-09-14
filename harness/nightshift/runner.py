"""야간 루프 러너.

한 번 실행되면 policy.decide가 STOP을 낼 때까지 작업을 하나씩 돌린다.
작업 1건 = Agent SDK 세션 1개.

한도 정보의 출처는 RateLimitEvent 하나뿐이다. 이 이벤트는 세션 시작과 상태 변화 때만 오므로,
작업 중에는 probe_every 간격으로 Haiku 최소 호출(probe)을 따로 보내 주간 사용률을 새로 읽는다.
판정은 이벤트·probe를 받을 때, 메시지를 받을 때, 그리고 CHECK_EVERY_S마다 다시 한다.
RUN이 아니면 interrupt하고, INTERRUPT_GRACE_S 안에 끝나지 않거나 interrupt가 실패하면 세션을 끊는다.
"""

from __future__ import annotations

import fcntl
import json
import logging
import os
import re
import signal
import traceback
from datetime import datetime
from pathlib import Path

import anyio
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    HookMatcher,
    RateLimitEvent,
    ResultMessage,
    TextBlock,
)

from .policy import (Action, Config, Decision, Usage, count_starts, daily_usage, decide, is_work_time, learned, night_start,
                     reset_key, spend_until)

HARNESS = Path(__file__).resolve().parents[1]
REPO = HARNESS.parent
STATE_DIR = HARNESS / "state"
STATE_FILE = STATE_DIR / "nightshift.json"
EVENTS_FILE = STATE_DIR / "events.jsonl"
LOCK_FILE = STATE_DIR / "nightshift.lock"
PIPELINE = REPO / "ideas" / "PIPELINE.md"
PASSED_LABEL = "통과(실증 대기)"

CHECK_EVERY_S = 30
INTERRUPT_GRACE_S = 120
MAX_CONSECUTIVE_FAILURES = 3
FAILURE_BACKOFF_S = 60
MAX_IDLE_JOBS = 2  # 산출물이 하나도 안 바뀐 작업이 연속 이만큼이면 그날 밤 종료
EVENTS_MAX_BYTES = 2_000_000

log = logging.getLogger("nightshift")


def now_in(cfg: Config) -> datetime:
    return datetime.now(cfg.tz)


def passed_count(pipeline: Path | None = None) -> int:
    """PIPELINE.md 판정 칸이 `통과(실증 대기)`인 행 수. 공백 차이는 무시한다."""
    pipeline = pipeline or PIPELINE  # 기본값을 호출 시점에 읽는다 (테스트 monkeypatch 대상)
    if not pipeline.exists():
        return 0
    target = re.sub(r"\s", "", PASSED_LABEL)
    rows = [line.split("|") for line in pipeline.read_text().splitlines() if line.lstrip().startswith("|")]
    # | slug | 문제 | 단계 | 게이트 | 판정 | ... → split 결과의 5번째 칸이 판정
    return sum(1 for cells in rows if len(cells) > 5 and re.sub(r"\s", "", cells[5]) == target)


def ideas_fingerprint() -> frozenset:
    """ideas/ 아래 파일의 (경로, 크기, mtime). 작업이 진전을 만들었는지 본다."""
    root = PIPELINE.parent
    if not root.exists():
        return frozenset()
    entries = set()
    for p in root.rglob("*"):
        try:
            if p.is_file():
                st = p.stat()
                entries.add((str(p), st.st_size, st.st_mtime_ns))
        except FileNotFoundError:  # 훑는 사이 지워진 파일
            continue
    return frozenset(entries)


# ── 상태 ─────────────────────────────────────────────────────────────────────


def load_state(path: Path | None = None) -> dict:
    path = path or STATE_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError):
        broken = path.with_name(f"{path.name}.corrupt-{datetime.now():%Y%m%d-%H%M%S}")
        path.rename(broken)
        log.error("상태 파일이 손상돼 %s로 옮기고 새로 시작한다 (학습값은 기본값으로 돌아간다)", broken.name)
        return {}


def save_state(state: dict, path: Path | None = None) -> None:
    path = path or STATE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


class Night:
    """이번 야간의 한도 상태와 영속 기록."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.usage = Usage()
        self.state = load_state()
        self.state.setdefault("daytime_samples", [])
        self.state.setdefault("job_cost_samples", [])
        key = night_start(now_in(cfg), cfg).isoformat()
        if self.state.get("night", {}).get("start") != key:
            self.state["night"] = {"start": key, "base": {}}  # 재시작해도 같은 야간이면 기준을 유지한다

    @property
    def base(self) -> dict[str, float]:
        return self.state["night"]["base"]

    def save(self) -> None:
        save_state(self.state)

    def observe(self, raw: dict, source: str) -> None:
        now = now_in(self.cfg)
        self.usage.update(raw, now)
        u = self.usage
        if u.seven_reset and u.seven_util is not None and reset_key(u.seven_reset) not in self.base:
            self.base[reset_key(u.seven_reset)] = u.seven_util
            self.save()
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        if EVENTS_FILE.exists() and EVENTS_FILE.stat().st_size > EVENTS_MAX_BYTES:
            os.replace(EVENTS_FILE, EVENTS_FILE.with_name(EVENTS_FILE.name + ".1"))
        with EVENTS_FILE.open("a") as f:
            f.write(json.dumps({"at": now.isoformat(), "source": source, "raw": raw}, ensure_ascii=False) + "\n")

    def decision(self, *, starting_job: bool) -> Decision:
        u = self.usage
        base = self.base.get(reset_key(u.seven_reset)) if u.seven_reset else None
        return decide(now_in(self.cfg), u, base, self.cfg, daytime_samples=self.state["daytime_samples"],
                      job_cost_samples=self.state["job_cost_samples"], starting_job=starting_job)

    def may_request(self) -> bool:
        """5시간 창·근무 시간 규칙만 봤을 때 요청 하나를 보내도 되는가 (probe 허용 여부)."""
        now = now_in(self.cfg)
        return not is_work_time(now, self.cfg) and now < spend_until(now, self.usage, self.cfg)[0]

    def record_daytime_sample(self) -> None:
        """지난 야간 종료 ~ 지금 사이 주간 사용률 증가분 = 사용자 근무 시간 사용량."""
        prev, u = self.state.get("last_night_end"), self.usage
        if not prev or u.seven_util is None or not u.seven_reset or prev.get("seven_reset_key") != reset_key(u.seven_reset):
            return  # 첫 야간이거나 사이에 주간 초기화가 끼었다
        workdays = count_starts(self.cfg.work_start, datetime.fromisoformat(prev["at"]), now_in(self.cfg), self.cfg, True)
        if workdays >= 1:
            sample = max(0.0, u.seven_util - prev["seven_util"]) / workdays
            self.state["daytime_samples"] = (self.state["daytime_samples"] + [round(sample, 4)])[-14:]
            self.save()
            log.info("근무 시간 사용량 표본 %.1f%%/일 (누적 %d개, 적용값 %.1f%%)", sample * 100,
                     len(self.state["daytime_samples"]), daily_usage(self.state["daytime_samples"], self.cfg) * 100)

    def record_job_cost(self, util_before: float | None, reset_before: datetime | None) -> None:
        u = self.usage
        if util_before is None or reset_before is None or u.seven_util is None or u.seven_reset is None:
            return
        if reset_key(reset_before) != reset_key(u.seven_reset):
            return  # 작업 중 주간 초기화
        cost = max(0.0, u.seven_util - util_before)
        self.state["job_cost_samples"] = (self.state["job_cost_samples"] + [round(cost, 4)])[-20:]
        self.save()
        log.info("작업 비용 표본 %.1f%%p (적용 예상치 %.1f%%p)", cost * 100,
                 learned(self.state["job_cost_samples"], self.cfg.job_cost_default, self.cfg) * 100)

    def record_end(self) -> None:
        u = self.usage
        if u.seven_util is not None and u.seven_reset:
            self.state["last_night_end"] = {"at": (u.observed_at or now_in(self.cfg)).isoformat(),
                                            "seven_util": u.seven_util, "seven_reset_key": reset_key(u.seven_reset)}
        self.save()


# ── 작업 세션 보호 ────────────────────────────────────────────────────────────

PROTECTED_DIRS = [HARNESS / "nightshift", HARNESS / "state", HARNESS / ".venv", Path.home() / ".config" / "systemd"]
PROTECTED_FILES = [
    HARNESS / "nightshift.toml", HARNESS / "install-systemd.sh", HARNESS / "pyproject.toml", HARNESS / "uv.lock",
    HARNESS / "prompts" / "night-job.md",
    # settings의 hooks는 다음 세션에서 PreToolUse 필터 밖에서 실행된다
    REPO / ".claude" / "settings.json", REPO / ".claude" / "settings.local.json",
    Path.home() / ".claude" / "settings.json", Path.home() / ".claude" / "settings.local.json",
    Path.home() / ".claude" / ".credentials.json",
]
BASH_FORBIDDEN = re.compile(
    # push는 git 서브커맨드 자리에서만 잡는다 (git -C . push, git --no-pager push). slug·커밋 메시지 속 push는 허용
    r"\bgit\b(?:\s+-\S+(?:\s+[^-\s]\S*)?)*\s+push\b"
    r"|\bsystemctl\b|\bcrontab\b|\bloginctl\b|\.credentials|\.config/systemd"
    r"|harness/(nightshift|state|prompts|install-systemd|pyproject|uv\.lock|\.venv)|nightshift\.toml"
    r"|\.claude/settings(\.local)?\.json"
)


def _is_protected(path_str: str) -> bool:
    if not path_str:
        return False
    p = Path(os.path.expanduser(path_str))
    p = (REPO / p if not p.is_absolute() else p).resolve()
    return p in PROTECTED_FILES or any(p == d or d in p.parents for d in PROTECTED_DIRS)


def deny_reason(tool_name: str, tool_input: dict, heavy_allowed: bool) -> str | None:
    """야간 작업 세션에서 막을 도구 호출이면 이유를, 아니면 None."""
    if tool_name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        if _is_protected(path):
            return "야간 루프는 자기 감시 코드·설정·systemd·자격증명을 수정할 수 없다"
    elif tool_name == "Read":
        if _is_protected(tool_input.get("file_path", "")) and ".credentials" in tool_input.get("file_path", ""):
            return "야간 루프는 자격증명 파일을 읽을 수 없다"
    elif tool_name == "Bash":
        if BASH_FORBIDDEN.search(tool_input.get("command", "")):
            return "야간 루프에서 금지된 명령 (git push, systemctl, 감시 코드·설정·자격증명 접근)"
    elif tool_name == "Skill" and not heavy_allowed:
        skill = tool_input.get("skill", "").split(":")[-1]
        args = tool_input.get("args", "") or ""
        # 한글 조사가 붙어도 잡도록 단어 경계 없이 본다. deep·medium이 함께 있으면 무거운 쪽으로 친다
        shallow_only = "shallow" in args.lower() and not re.search(r"deep|medium", args, re.IGNORECASE)
        heavy = (skill == "deepdive" and not shallow_only) or \
                (skill == "crucible" and not re.search(r"--(council|solo)\b", args))
        if heavy:
            return ("이번 야간 주간 여유가 작아 무거운 스킬(crucible Decision, deepdive medium·deep)을 쓸 수 없다. "
                    "이 아이디어는 `PROGRESS.md`에 「무거운 스킬 대기」로 적고 다른 아이디어나 가벼운 단계를 진행하라")
    return None


def guard_hook(night: Night):
    async def hook(input_data, tool_use_id, context):
        heavy = night.decision(starting_job=False).heavy_allowed
        reason = deny_reason(input_data.get("tool_name", ""), input_data.get("tool_input") or {}, heavy)
        if reason:
            log.warning("도구 차단 %s: %s", input_data.get("tool_name"), reason)
            return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                           "permissionDecisionReason": reason}}
        return {}

    return hook


def night_append(d: Decision) -> str:
    heavy = "허용" if d.heavy_allowed else "금지 (hook이 차단한다)"
    return f"""
# 야간 자동 루프 모드
- 사용자는 퇴근해서 자리에 없다. 질문하지 말고, 필요한 판단은 가정을 세워 진행한 뒤 `PROGRESS.md`의 「야간 가정」에 적는다.
- CLAUDE.md의 비싼 스킬은 이 모드에서 사전 승인되어 있다. `deepdive` deep의 Plan-review gate는 사용자 대신 독립 서브에이전트가 검토한다(CLAUDE.md 「야간 자동 루프」 절).
- 이번 작업 예산: 이번 야간 주간 한도 여유 약 {d.detail.get('headroom', 0):.1%}. crucible Decision·deepdive medium·deep: {heavy}.
- 러너가 한도·시간 규칙에 따라 언제든 작업을 중단시킬 수 있다. 산출물은 자주 파일로 쓰고 `PROGRESS.md`를 갱신해 끊겨도 이어갈 수 있게 한다.
- S5(실증: 프로토타입·인터뷰)는 실행하지 않는다. `git push`는 하지 않는다.
"""


def job_options(night: Night, d: Decision) -> ClaudeAgentOptions:
    cfg = night.cfg
    deny_rules = [f"{tool}(/{p}/**)" for p in PROTECTED_DIRS for tool in ("Edit", "Write")]
    deny_rules += [f"{tool}(/{p})" for p in PROTECTED_FILES for tool in ("Edit", "Write")]
    deny_rules += ["Bash(git push *)", "Bash(systemctl *)", f"Read(/{Path.home() / '.claude' / '.credentials.json'})"]
    return ClaudeAgentOptions(
        cwd=str(REPO),
        setting_sources=["user", "project", "local"],
        permission_mode="bypassPermissions",
        disallowed_tools=deny_rules,
        hooks={"PreToolUse": [HookMatcher(matcher="Write|Edit|MultiEdit|NotebookEdit|Read|Bash|Skill",
                                          hooks=[guard_hook(night)])]},
        system_prompt={"type": "preset", "preset": "claude_code", "append": night_append(d)},
        model=cfg.model,
    )


# ── SDK 호출 ─────────────────────────────────────────────────────────────────


async def probe(night: Night) -> bool:
    """가장 싼 호출 하나로 한도 상태를 읽는다. 호출 자체가 5시간 창을 열 수 있으므로 시간 규칙 안에서만 부른다."""
    if not night.may_request():
        return False
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    opts = ClaudeAgentOptions(cwd=str(STATE_DIR), setting_sources=[], max_turns=1, tools=[], model=night.cfg.probe_model)
    got = False
    try:
        with anyio.fail_after(120):
            async with ClaudeSDKClient(opts) as client:
                await client.query("Reply with the single word: ok")
                async for msg in client.receive_response():
                    if isinstance(msg, RateLimitEvent):
                        night.observe(msg.rate_limit_info.raw, "probe")
                        got = True
    except Exception:
        log.exception("probe 실패")
    if not got:
        log.warning("probe에서 한도 이벤트를 받지 못함")
    return got


async def run_job(night: Night, d: Decision, shutdown: anyio.Event) -> str:
    """'done' | 'stopped'(러너가 규칙대로 끊음) | 'error'."""
    cfg = night.cfg
    started = now_in(cfg)
    job_deadline = min(d.until, started + cfg.job_max)
    prompt = (REPO / cfg.prompt_file).read_text()
    util_before, reset_before = night.usage.seven_util, night.usage.seven_reset
    log.info("작업 시작 (최대 %s까지, 여유 %.1f%%, 무거운 스킬 %s)", job_deadline.strftime("%H:%M"),
             d.detail.get("headroom", 0) * 100, "허용" if d.heavy_allowed else "금지")

    status = "error"
    stop_reason: str | None = None

    try:
        async with ClaudeSDKClient(job_options(night, d)) as client:
            await client.query(prompt)
            async with anyio.create_task_group() as tg:

                async def stop(reason: str) -> None:
                    nonlocal stop_reason
                    if stop_reason:
                        return
                    stop_reason = reason
                    log.warning("작업 중단: %s", reason)
                    try:
                        with anyio.fail_after(INTERRUPT_GRACE_S):
                            await client.interrupt()
                        await anyio.sleep(INTERRUPT_GRACE_S)
                        log.error("interrupt 후 %ds 안에 끝나지 않아 세션을 끊는다", INTERRUPT_GRACE_S)
                    except Exception:
                        log.exception("interrupt 실패, 세션을 끊는다")
                    tg.cancel_scope.cancel()

                probing = False

                async def probe_then_check() -> None:
                    nonlocal probing
                    probing = True
                    try:
                        await probe(night)
                    finally:
                        probing = False
                    check(allow_probe=False)

                def check(allow_probe: bool = True) -> None:
                    if stop_reason:
                        return
                    cur = night.decision(starting_job=False)
                    if shutdown.is_set():
                        reason = "종료 신호"
                    elif cur.action is Action.PROBE and allow_probe:
                        # 주간 정보가 오래됐거나 주간 초기화가 지남 → 끊기 전에 한 번 읽어 본다
                        if not probing:
                            tg.start_soon(probe_then_check)
                        return
                    elif cur.action is not Action.RUN:
                        reason = cur.reason
                    elif now_in(cfg) >= job_deadline:
                        reason = "작업 최대 길이 도달"
                    else:
                        return
                    tg.start_soon(stop, reason)

                async def watchdog() -> None:
                    while True:
                        await anyio.sleep(CHECK_EVERY_S)
                        check()

                async def prober() -> None:
                    while True:
                        await anyio.sleep(cfg.probe_every.total_seconds())
                        await probe(night)
                        check()

                tg.start_soon(watchdog)
                tg.start_soon(prober)
                async for msg in client.receive_response():
                    if isinstance(msg, RateLimitEvent):
                        night.observe(msg.rate_limit_info.raw, "job")
                    elif isinstance(msg, AssistantMessage):
                        for block in msg.content:
                            if isinstance(block, TextBlock) and block.text.startswith("JOB:"):
                                log.info(block.text.splitlines()[0])
                    elif isinstance(msg, ResultMessage):
                        status = "error" if msg.is_error else "done"
                        log.info("작업 종료: %s, %d턴, %.0f분, 추정 $%.2f", msg.subtype, msg.num_turns,
                                 msg.duration_ms / 60000, msg.total_cost_usd or 0)
                        continue
                    check()
                tg.cancel_scope.cancel()
    except Exception:
        if not stop_reason:
            log.error("작업 세션 예외\n%s", traceback.format_exc())
            status = "error"

    if not shutdown.is_set() and await probe(night):
        night.record_job_cost(util_before, reset_before)
    return "stopped" if stop_reason else status


# ── 루프 ─────────────────────────────────────────────────────────────────────


async def run(cfg: Config, dry_run: bool) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK_FILE.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log.error("다른 nightshift가 이미 실행 중이라 종료한다")
            return

        night = Night(cfg)
        shutdown = anyio.Event()

        async def on_signal() -> None:
            with anyio.open_signal_receiver(signal.SIGTERM, signal.SIGINT) as signals:
                async for _ in signals:
                    log.warning("종료 신호 수신")
                    shutdown.set()
                    return

        try:
            async with anyio.create_task_group() as tg:
                tg.start_soon(on_signal)
                try:
                    await loop(night, shutdown, dry_run)
                finally:
                    tg.cancel_scope.cancel()
        except Exception:
            log.error("러너 예외로 종료\n%s", traceback.format_exc())
            raise
        finally:
            night.record_end()


async def loop(night: Night, shutdown: anyio.Event, dry_run: bool) -> None:
    cfg = night.cfg

    first = night.decision(starting_job=True)  # 한도 정보가 없으므로 시간 규칙만 STOP을 낼 수 있다
    if first.action is Action.STOP:
        log.info("시작하지 않음: %s", first.reason)
        return
    if passed_count() >= cfg.target_passed:
        log.info("목표 달성: %s %d개", PASSED_LABEL, passed_count())
        return

    if await probe(night):
        night.record_daytime_sample()
    failures = idle = 0

    while not shutdown.is_set():
        if (n := passed_count()) >= cfg.target_passed:
            log.info("목표 달성: %s %d개", PASSED_LABEL, n)
            return
        d = night.decision(starting_job=True)
        if d.action is Action.PROBE:
            log.info("판정 probe — %s", d.reason)
            await probe(night)
            d = night.decision(starting_job=True)
            if d.action is Action.PROBE:
                log.error("한도 정보를 읽지 못해 종료 (fail-closed): %s", d.reason)
                return
        log.info("판정 %s until=%s — %s %s", d.action.value, d.until.strftime("%m-%d %H:%M"), d.reason,
                 {k: round(v, 4) if isinstance(v, float) else v for k, v in d.detail.items()})
        if d.action is Action.STOP:
            return
        if d.action is Action.WAIT:
            with anyio.move_on_after(max(1.0, (d.until - now_in(cfg)).total_seconds() + 30)):
                await shutdown.wait()
            continue
        if d.until - now_in(cfg) < cfg.min_job:
            log.info("남은 시간이 min_job보다 짧아 종료")
            return
        if dry_run:
            log.info("[dry-run] 여기서 작업을 시작했을 것")
            return

        before = ideas_fingerprint()
        result = await run_job(night, d, shutdown)
        if result == "done" and ideas_fingerprint() == before:
            idle += 1
            log.warning("작업이 ideas/ 아래 아무것도 바꾸지 않음 (%d/%d)", idle, MAX_IDLE_JOBS)
            if idle >= MAX_IDLE_JOBS:
                log.error("진전 없는 작업이 연속돼 오늘 밤은 종료 (진행 가능한 아이디어가 모두 막혔을 수 있음)")
                return
        elif result != "error":
            idle = 0
        if result != "error":
            failures = 0
            continue
        failures += 1
        if failures >= MAX_CONSECUTIVE_FAILURES:
            log.error("작업이 %d번 연속 실패해 오늘 밤은 종료", failures)
            return
        with anyio.move_on_after(FAILURE_BACKOFF_S):
            await shutdown.wait()
