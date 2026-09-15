"""언제 토큰을 써도 되는지 판정한다. 부수효과 없는 순수 함수만 둔다.

5시간 창 규칙 — 사용자가 근무를 시작하는 시각(work_start)에 5시간 창이 비어 있어야 한다
  창은 "직전 창이 끝난 뒤 첫 요청" 시각에 열린다. 2026-09-14 로컬 기록으로 복원하면
  종료 시각 = 시작 시각을 정시로 내림 + 5h 였다(16:01:50 시작 → 21:00 종료).
  아래 계산은 내림 없이 시작 + 5h로 잡으므로 실제보다 늦게 끝난다고 가정한다(보수적).
  D = 다음 work_start - safety_margin 이라고 하면:
  - 지금 요청이 새 창을 열어도 now + 5h <= D 이면 안전하다. 그 경계가 fresh_limit = D - 5h.
  - 이미 열린 창의 종료 시각 R을 알고 R <= D 이면, R 직전까지는 그 창 안이므로 안전하다.
  - 그 밖에는 요청 하나가 사용자 아침 창을 열거나 갉아먹을 수 있으므로 멈춘다.

주간 한도 규칙 (2026-09-15 사용자 결정)
  - 주간 사용률 < approval_threshold(70%): 새 작업을 자유롭게 시작한다.
  - 주간 사용률 ≥ approval_threshold: 작업 1건을 시작할 때마다 사용자 승인이 필요하다(Action.ASK).
  - 이미 시작한 작업은 도중에 70%를 넘어도 끝까지 한다. 확인 단위는 "작업 1건"이다.
  - 작업을 시작하려는데 주간 사용률 정보가 없거나 오래됐으면 먼저 읽는다(Action.PROBE, fail-closed).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum
from pathlib import Path
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Config:
    tz: ZoneInfo
    work_start: time
    work_end: time
    workdays: frozenset[int]
    margin: timedelta
    window: timedelta
    job_max: timedelta
    min_job: timedelta
    usage_max_age: timedelta
    approval_threshold: float
    approval_port: int
    target_passed: int
    model: str | None
    probe_model: str
    prompt_file: str

    @classmethod
    def load(cls, path: Path) -> Config:
        raw = tomllib.loads(path.read_text())
        weekly, loop = raw["weekly"], raw["loop"]
        return cls(
            tz=ZoneInfo(raw["timezone"]),
            work_start=time.fromisoformat(raw["work_start"]),
            work_end=time.fromisoformat(raw["work_end"]),
            workdays=frozenset(raw["workdays"]),
            margin=timedelta(minutes=raw["safety_margin_minutes"]),
            window=timedelta(hours=raw["window_hours"]),
            job_max=timedelta(minutes=raw["job_max_minutes"]),
            min_job=timedelta(minutes=raw["min_job_minutes"]),
            usage_max_age=timedelta(minutes=raw["usage_max_age_minutes"]),
            approval_threshold=weekly["approval_threshold"],
            approval_port=weekly["approval_port"],
            target_passed=loop["target_passed"],
            model=loop["model"] or None,
            probe_model=loop["probe_model"],
            prompt_file=loop["prompt_file"],
        )


@dataclass
class Usage:
    """구독 한도 상태. Agent SDK RateLimitEvent의 raw dict에서 채운다."""

    five_reset: datetime | None = None
    five_util: float | None = None
    seven_reset: datetime | None = None
    seven_util: float | None = None
    rejected_until: datetime | None = None
    observed_at: datetime | None = None  # 주간 사용률을 마지막으로 읽은 시각

    def update(self, raw: dict, now: datetime) -> None:
        tz = now.tzinfo
        windows = raw.get("unifiedWindows") or {}

        def reset_of(w: dict) -> datetime | None:
            return datetime.fromtimestamp(w["resetsAt"], tz) if w.get("resetsAt") else None

        if "five_hour" in windows:
            self.five_reset, self.five_util = reset_of(windows["five_hour"]), windows["five_hour"].get("utilization")
        # seven_day_opus 등 모델별 주간 창이 따로 오면 가장 빡빡한 쪽을 쓴다
        weekly = [w for key, w in windows.items() if key.startswith("seven_day")]
        if weekly:
            tightest = max(weekly, key=lambda w: w.get("utilization") or 0)
            self.seven_reset, self.seven_util = reset_of(tightest), tightest.get("utilization")
            if self.seven_util is not None:
                self.observed_at = now

        # unifiedWindows가 없는 이벤트는 단일 창 정보만 담는다. 사용률이 없으면 모르는 것으로 둔다
        kind, reset_ts = raw.get("rateLimitType"), raw.get("resetsAt")
        if not windows and kind and reset_ts:
            reset = datetime.fromtimestamp(reset_ts, tz)
            if kind == "five_hour":
                self.five_reset, self.five_util = reset, raw.get("utilization")
            elif kind.startswith("seven_day"):
                self.seven_reset, self.seven_util = reset, raw.get("utilization")
                self.observed_at = now if self.seven_util is not None else None

        if raw.get("status") == "rejected" and reset_ts:
            self.rejected_until = datetime.fromtimestamp(reset_ts, tz)
        elif raw.get("status") in ("allowed", "allowed_warning"):
            self.rejected_until = None


class Action(Enum):
    RUN = "run"
    ASK = "ask"      # 주간 사용률이 기준 이상 → 이 작업을 시작해도 되는지 사용자 승인 필요
    PROBE = "probe"  # 주간 정보가 없거나 오래됨 → 한 번 읽고 다시 판정. 그래도 이러면 멈춘다
    WAIT = "wait"
    STOP = "stop"


@dataclass(frozen=True)
class Decision:
    action: Action
    until: datetime
    reason: str


# ── 시각 계산 ────────────────────────────────────────────────────────────────


def _at(day: datetime, t: time, cfg: Config) -> datetime:
    return datetime.combine(day.date(), t, tzinfo=cfg.tz)


def is_work_time(now: datetime, cfg: Config) -> bool:
    now = now.astimezone(cfg.tz)
    return now.weekday() in cfg.workdays and cfg.work_start <= now.time() < cfg.work_end


def next_work_start(now: datetime, cfg: Config) -> datetime:
    """now 이후 가장 가까운 근무 시작 시각. 근무 중이면 now."""
    now = now.astimezone(cfg.tz)
    if is_work_time(now, cfg):
        return now
    for offset in range(8):
        candidate = _at(now + timedelta(days=offset), cfg.work_start, cfg)
        if candidate > now and candidate.weekday() in cfg.workdays:
            return candidate
    raise ValueError("workdays가 비어 있다")


def deadline(now: datetime, cfg: Config) -> datetime:
    """D: 루프가 소비한 5시간 창이 반드시 끝나 있어야 하는 시각."""
    return next_work_start(now, cfg) - cfg.margin


def spend_until(now: datetime, usage: Usage, cfg: Config) -> tuple[datetime, str]:
    """5시간 창 규칙만으로 본, 요청을 보내도 되는 마지막 시각."""
    d = deadline(now, cfg)
    fresh_limit = d - cfg.window
    r = usage.five_reset
    if r is not None and now < r - cfg.margin:
        if r > d:
            return fresh_limit, f"현재 창이 {r:%H:%M}까지 이어져 아침 창을 침범"
        if r - cfg.margin >= fresh_limit:
            return r - cfg.margin, f"현재 창이 {r:%H:%M}에 끝남 (≤ {d:%H:%M})"
    return fresh_limit, f"새 창을 열어도 {d:%H:%M} 전에 끝나는 마지막 시각"


def usage_missing(now: datetime, usage: Usage, cfg: Config) -> str | None:
    if usage.seven_util is None or usage.seven_reset is None or usage.observed_at is None:
        return "주간 사용률 정보 없음"
    if usage.seven_reset <= now:
        return "주간 초기화가 지나 사용률을 다시 읽어야 함"
    if now - usage.observed_at > cfg.usage_max_age:
        return f"주간 사용률이 {cfg.usage_max_age} 넘게 갱신되지 않음"
    return None


# ── 종합 판정 ────────────────────────────────────────────────────────────────


def decide(now: datetime, usage: Usage, cfg: Config, *, starting_job: bool, approved: bool = False) -> Decision:
    """지금 토큰을 써도 되는가.

    starting_job: 새 작업을 시작하려는가(주간 규칙 적용), 도는 작업을 계속하려는가(시간·한도 소진만 본다).
    approved: 이번에 시작할 작업 1건에 대해 사용자가 이미 승인했는가.
    """
    if is_work_time(now, cfg):
        return Decision(Action.STOP, now, "근무 시간")

    until, why = spend_until(now, usage, cfg)
    if now >= until:
        return Decision(Action.STOP, now, f"5시간 창 규칙: {why}")

    if usage.rejected_until and usage.rejected_until > now:
        if usage.rejected_until < until:
            return Decision(Action.WAIT, usage.rejected_until, "한도 소진, 초기화까지 대기")
        return Decision(Action.STOP, now, "한도 소진, 오늘 밤 안에 초기화되지 않음")

    if not starting_job:
        return Decision(Action.RUN, until, why)

    if missing := usage_missing(now, usage, cfg):
        return Decision(Action.PROBE, until, missing)

    if usage.seven_util >= cfg.approval_threshold and not approved:
        return Decision(Action.ASK, until,
                        f"주간 사용률 {usage.seven_util:.0%} ≥ {cfg.approval_threshold:.0%}, 작업 1건마다 승인 필요")

    return Decision(Action.RUN, until, why)
