"""자동 루프 러너. 사용자가 `python -m autoloop run`으로 직접 띄운다(스케줄링 없음).

한 번 실행되면 policy.decide가 STOP을 낼 때까지 작업을 하나씩 돌린다. 작업 1건 = Agent SDK 세션 1개.

- 작업을 시작하기 전에 한도 정보가 없거나 오래됐으면 Haiku 최소 호출(probe)로 새로 읽는다.
- 주간 사용률이 approval_threshold 이상이면 승인 페이지에 요청을 올리고 사용자 답을 기다린다.
  승인하면 작업 1건을 돌리고, 거절하면 루프를 끝낸다. 답이 올 때까지(또는 러너를 멈출 때까지) 기다린다.
- 작업 중에는 한도 소진(rejected)과 작업 최대 길이만 본다. 도중에 주간 기준을 넘어도 그 작업은 끝낸다.
  판정은 한도 이벤트·메시지 수신 때와 CHECK_EVERY_S마다 다시 하고, RUN이 아니면 interrupt한다.
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

from . import approval, board
from .policy import Action, Config, Decision, Usage, decide

HARNESS = Path(__file__).resolve().parents[1]
REPO = HARNESS.parent
STATE_DIR = HARNESS / "state"
EVENTS_FILE = STATE_DIR / "events.jsonl"
LOCK_FILE = STATE_DIR / "autoloop.lock"
TOKEN_FILE = STATE_DIR / "approval-token"
PIPELINE = REPO / "ideas" / "PIPELINE.md"
PASSED_LABEL = "통과(실증 대기)"

CHECK_EVERY_S = 30
INTERRUPT_GRACE_S = 120
APPROVAL_POLL_S = 2
MAX_CONSECUTIVE_FAILURES = 3
FAILURE_BACKOFF_S = 60
MAX_IDLE_JOBS = 2  # 산출물이 하나도 안 바뀐 작업이 연속 이만큼이면 루프 종료
EVENTS_MAX_BYTES = 2_000_000

log = logging.getLogger("autoloop")


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


class LoopState:
    """이번 실행의 한도 상태와 승인 페이지."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.usage = Usage()
        self.gate: approval.ApprovalGate | None = None
        self.board: board.Board | None = None

    def observe(self, raw: dict, source: str) -> None:
        now = now_in(self.cfg)
        self.usage.update(raw, now)
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        if EVENTS_FILE.exists() and EVENTS_FILE.stat().st_size > EVENTS_MAX_BYTES:
            os.replace(EVENTS_FILE, EVENTS_FILE.with_name(EVENTS_FILE.name + ".1"))
        with EVENTS_FILE.open("a") as f:
            f.write(json.dumps({"at": now.isoformat(), "source": source, "raw": raw}, ensure_ascii=False) + "\n")

    def decision(self, *, starting_job: bool, approved: bool = False) -> Decision:
        return decide(now_in(self.cfg), self.usage, self.cfg, starting_job=starting_job, approved=approved)

    def close(self) -> None:
        if self.gate:
            self.gate.stop()
            self.gate = None
        if self.board:
            self.board.stop()
            self.board = None


def start_board(cfg: Config) -> board.Board | None:
    """아이디어 보드를 띄운다. Tailscale이 없거나 포트가 이미 쓰이면(따로 띄운 보드) 조용히 건너뛴다."""
    host = approval.tailscale_ip()
    if host is None:
        return None
    b = board.Board(host=host, port=cfg.board_port, token=approval.load_token(TOKEN_FILE), ideas_root=PIPELINE.parent,
                    target=cfg.target_passed, approval_port=cfg.approval_port)
    try:
        b.start()
    except OSError:
        log.info("보드 포트 %d가 이미 쓰이고 있어 루프에서는 띄우지 않는다", cfg.board_port)
        return None
    log.info("아이디어 보드: %s", b.url.split("?")[0])
    return b


# ── 작업 세션 보호 ────────────────────────────────────────────────────────────

PROTECTED_DIRS = [HARNESS / "autoloop", HARNESS / "state", HARNESS / ".venv", Path.home() / ".config" / "systemd"]
PROTECTED_FILES = [
    HARNESS / "autoloop.toml", HARNESS / "pyproject.toml", HARNESS / "uv.lock", HARNESS / "prompts" / "job.md",
    # settings의 hooks는 다음 세션에서 PreToolUse 필터 밖에서 실행된다
    REPO / ".claude" / "settings.json", REPO / ".claude" / "settings.local.json",
    Path.home() / ".claude" / "settings.json", Path.home() / ".claude" / "settings.local.json",
    Path.home() / ".claude" / ".credentials.json",
]
BASH_FORBIDDEN = re.compile(
    # push는 git 서브커맨드 자리에서만 잡는다 (git -C . push, git --no-pager push). slug·커밋 메시지 속 push는 허용
    r"\bgit\b(?:\s+-\S+(?:\s+[^-\s]\S*)?)*\s+push\b"
    r"|\bsystemctl\b|\bcrontab\b|\bloginctl\b|\.credentials|\.config/systemd"
    r"|harness/(autoloop|state|prompts|pyproject|uv\.lock|\.venv)|autoloop\.toml"
    r"|\.claude/settings(\.local)?\.json|approval-token"
)


def _is_protected(path_str: str) -> bool:
    if not path_str:
        return False
    p = Path(os.path.expanduser(path_str))
    p = (REPO / p if not p.is_absolute() else p).resolve()
    return p in PROTECTED_FILES or any(p == d or d in p.parents for d in PROTECTED_DIRS)


def deny_reason(tool_name: str, tool_input: dict) -> str | None:
    """자동 루프 작업 세션에서 막을 도구 호출이면 이유를, 아니면 None."""
    if tool_name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        if _is_protected(tool_input.get("file_path") or tool_input.get("notebook_path") or ""):
            return "자동 루프는 자기 감시 코드·설정·승인 토큰·systemd·자격증명을 수정할 수 없다"
    elif tool_name == "Read":
        path = tool_input.get("file_path", "")
        if _is_protected(path) and (".credentials" in path or "approval-token" in path):
            return "자동 루프는 자격증명·승인 토큰을 읽을 수 없다"
    elif tool_name == "Bash":
        if BASH_FORBIDDEN.search(tool_input.get("command", "")):
            return "자동 루프에서 금지된 명령 (git push, systemctl, 감시 코드·설정·자격증명·승인 토큰 접근)"
    return None


async def guard_hook(input_data, tool_use_id, context):
    reason = deny_reason(input_data.get("tool_name", ""), input_data.get("tool_input") or {})
    if reason:
        log.warning("도구 차단 %s: %s", input_data.get("tool_name"), reason)
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                       "permissionDecisionReason": reason}}
    return {}


LOOP_APPEND = """
# 자동 루프 모드
- 무인 실행이다. 질문하지 말고, 필요한 판단은 가정을 세워 진행한 뒤 `PROGRESS.md`의 「자동 루프 가정」에 적는다.
- CLAUDE.md의 비싼 스킬은 이 모드에서 사전 승인되어 있다. `deepdive` deep의 Plan-review gate는 사용자 대신 독립 서브에이전트가 검토한다(CLAUDE.md 「자동 루프」 절).
- 러너가 한도 소진·작업 최대 길이에 따라 언제든 작업을 중단시킬 수 있다. 산출물은 자주 파일로 쓰고 `PROGRESS.md`를 갱신해 끊겨도 이어갈 수 있게 한다.
- S5(실증: 프로토타입·인터뷰)는 실행하지 않는다. `git push`는 하지 않는다.
"""


def job_options(cfg: Config) -> ClaudeAgentOptions:
    deny_rules = [f"{tool}(/{p}/**)" for p in PROTECTED_DIRS for tool in ("Edit", "Write")]
    deny_rules += [f"{tool}(/{p})" for p in PROTECTED_FILES for tool in ("Edit", "Write")]
    deny_rules += ["Bash(git push *)", "Bash(systemctl *)",
                   f"Read(/{Path.home() / '.claude' / '.credentials.json'})", f"Read(/{TOKEN_FILE})"]
    return ClaudeAgentOptions(
        cwd=str(REPO),
        setting_sources=["user", "project", "local"],
        permission_mode="bypassPermissions",
        disallowed_tools=deny_rules,
        hooks={"PreToolUse": [HookMatcher(matcher="Write|Edit|MultiEdit|NotebookEdit|Read|Bash", hooks=[guard_hook])]},
        system_prompt={"type": "preset", "preset": "claude_code", "append": LOOP_APPEND},
        model=cfg.model,
    )


# ── SDK 호출 ─────────────────────────────────────────────────────────────────


async def probe(night: LoopState) -> bool:
    """가장 싼 호출 하나로 한도 상태를 읽는다."""
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


async def run_job(night: LoopState, d: Decision, shutdown: anyio.Event) -> str:
    """'done' | 'stopped'(러너가 규칙대로 끊음) | 'error'."""
    cfg = night.cfg
    job_deadline = now_in(cfg) + cfg.job_max
    prompt = (REPO / cfg.prompt_file).read_text()
    u = night.usage
    log.info("작업 시작 (최대 %s까지, 주간 %s)", job_deadline.strftime("%H:%M"),
             f"{u.seven_util:.0%}" if u.seven_util is not None else "?")

    status = "error"
    stop_reason: str | None = None

    try:
        async with ClaudeSDKClient(job_options(cfg)) as client:
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

                def check() -> None:
                    if stop_reason:
                        return
                    if shutdown.is_set():
                        reason = "종료 신호"
                    elif (cur := night.decision(starting_job=False)).action is not Action.RUN:
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

                tg.start_soon(watchdog)
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

    return "stopped" if stop_reason else status


async def ask_approval(night: LoopState, d: Decision, shutdown: anyio.Event) -> bool:
    """승인 페이지에 요청을 올리고 답이 올 때까지 기다린다. 승인이면 True. 거절·종료 신호·페이지 불가는 False."""
    cfg = night.cfg
    if night.gate is None:
        host = approval.tailscale_ip()
        if host is None:
            log.error("Tailscale IP를 얻지 못해 승인 페이지를 열 수 없다. 루프를 끝낸다")
            return False
        gate = approval.ApprovalGate(host=host, port=cfg.approval_port, token=approval.load_token(TOKEN_FILE))
        try:
            gate.start()
        except OSError:
            log.exception("승인 페이지를 열지 못함. 루프를 끝낸다")
            return False
        night.gate = gate

    u = night.usage
    req = night.gate.open_request({
        "주간 사용률": f"{u.seven_util:.0%} (기준 {cfg.approval_threshold:.0%})" if u.seven_util is not None else "?",
        "주간 초기화": f"{u.seven_reset:%m-%d %a %H:%M}" if u.seven_reset else "?",
        "5시간 창": f"{u.five_util:.0%}, {u.five_reset:%H:%M} 종료" if u.five_util is not None and u.five_reset else "?",
        "통과(실증 대기)": f"{passed_count()} / {cfg.target_passed}",
        "작업 1건": f"최대 {int(cfg.job_max.total_seconds() // 60)}분",
    })
    log.warning("승인 대기: %s", night.gate.url.split("?")[0])

    while not shutdown.is_set():
        if req.choice in ("approve", "deny"):
            log.info("승인 요청 %s: %s", req.id, approval.LABEL[req.choice])
            return req.choice == "approve"
        with anyio.move_on_after(APPROVAL_POLL_S):
            await shutdown.wait()
    night.gate.expire(req)
    log.info("승인 요청 %s: 답을 받기 전에 러너가 멈춤", req.id)
    return False


# ── 루프 ─────────────────────────────────────────────────────────────────────


async def run(cfg: Config, dry_run: bool) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK_FILE.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log.error("다른 autoloop가 이미 실행 중이라 종료한다")
            return

        night = LoopState(cfg)
        night.board = start_board(cfg)
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
            night.close()


async def loop(night: LoopState, shutdown: anyio.Event, dry_run: bool) -> None:
    cfg = night.cfg

    failures = idle = 0
    approved = False  # 다음 작업 1건에 대한 사용자 승인

    while not shutdown.is_set():
        if (n := passed_count()) >= cfg.target_passed:
            log.info("목표 달성: %s %d개", PASSED_LABEL, n)
            return
        d = night.decision(starting_job=True, approved=approved)
        if d.action is Action.PROBE:
            await probe(night)
            d = night.decision(starting_job=True, approved=approved)
            if d.action is Action.PROBE:
                log.error("한도 정보를 읽지 못해 종료 (fail-closed): %s", d.reason)
                return
        log.info("판정 %s — %s", d.action.value, d.reason)
        if d.action is Action.STOP:
            return
        if d.action is Action.WAIT:
            with anyio.move_on_after(max(1.0, (d.until - now_in(cfg)).total_seconds() + 30)):
                await shutdown.wait()
            continue
        if d.action is Action.ASK:
            if dry_run:
                log.info("[dry-run] 여기서 승인을 요청했을 것")
                return
            if not await ask_approval(night, d, shutdown):
                return
            approved = True
            continue  # 승인을 기다리는 사이 시간·한도가 바뀌었을 수 있으니 다시 판정한다
        if dry_run:
            log.info("[dry-run] 여기서 작업을 시작했을 것")
            return

        approved = False  # 승인은 작업 1건에만 쓴다
        before = ideas_fingerprint()
        result = await run_job(night, d, shutdown)
        if result == "done" and ideas_fingerprint() == before:
            idle += 1
            log.warning("작업이 ideas/ 아래 아무것도 바꾸지 않음 (%d/%d)", idle, MAX_IDLE_JOBS)
            if idle >= MAX_IDLE_JOBS:
                log.error("진전 없는 작업이 연속돼 루프를 끝낸다 (진행 가능한 아이디어가 모두 막혔을 수 있음)")
                return
        elif result != "error":
            idle = 0
        if result != "error":
            failures = 0
            continue
        failures += 1
        if failures >= MAX_CONSECUTIVE_FAILURES:
            log.error("작업이 %d번 연속 실패해 루프를 끝낸다", failures)
            return
        with anyio.move_on_after(FAILURE_BACKOFF_S):
            await shutdown.wait()
