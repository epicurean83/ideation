"""지금 작업을 시작하거나 계속해도 되는지 판정한다. 부수효과 없는 순수 함수만 둔다.

시간대 제한은 없다(2026-09-15 사용자 결정: 저녁에만 도는 스케줄링 제거). 루프는 사용자가 직접 띄울 때 돈다.

주간 한도 규칙 (2026-09-15 사용자 결정)
  - 주간 사용률 < approval_threshold(70%): 새 작업을 자유롭게 시작한다.
  - 주간 사용률 ≥ approval_threshold: 작업 1건을 시작할 때마다 사용자 승인이 필요하다(Action.ASK).
  - 이미 시작한 작업은 도중에 70%를 넘어도 끝까지 한다. 확인 단위는 "작업 1건"이다.
  - 작업을 시작하려는데 주간 사용률 정보가 없거나 오래됐으면 먼저 읽는다(Action.PROBE, fail-closed).

한도 소진 (status=rejected)
  - 초기화까지 max_wait 이내면 기다리고(WAIT), 더 멀면 멈춘다(STOP). 도는 작업은 끊는다.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Config:
    tz: ZoneInfo
    job_max: timedelta
    usage_max_age: timedelta
    max_wait: timedelta
    approval_threshold: float
    approval_port: int
    board_port: int
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
            job_max=timedelta(minutes=raw["job_max_minutes"]),
            usage_max_age=timedelta(minutes=raw["usage_max_age_minutes"]),
            max_wait=timedelta(hours=raw["max_wait_hours"]),
            approval_threshold=weekly["approval_threshold"],
            approval_port=weekly["approval_port"],
            board_port=raw["board"]["port"],
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
    reason: str
    until: datetime | None = None  # WAIT일 때 기다릴 시각


def usage_missing(now: datetime, usage: Usage, cfg: Config) -> str | None:
    if usage.seven_util is None or usage.seven_reset is None or usage.observed_at is None:
        return "주간 사용률 정보 없음"
    if usage.seven_reset <= now:
        return "주간 초기화가 지나 사용률을 다시 읽어야 함"
    if now - usage.observed_at > cfg.usage_max_age:
        return f"주간 사용률이 {cfg.usage_max_age} 넘게 갱신되지 않음"
    return None


def decide(now: datetime, usage: Usage, cfg: Config, *, starting_job: bool, approved: bool = False) -> Decision:
    """지금 토큰을 써도 되는가.

    starting_job: 새 작업을 시작하려는가(주간 규칙 적용), 도는 작업을 계속하려는가(한도 소진만 본다).
    approved: 이번에 시작할 작업 1건에 대해 사용자가 이미 승인했는가.
    """
    if usage.rejected_until and usage.rejected_until > now:
        if usage.rejected_until - now <= cfg.max_wait:
            return Decision(Action.WAIT, f"한도 소진, {usage.rejected_until:%m-%d %H:%M} 초기화까지 대기",
                            usage.rejected_until)
        return Decision(Action.STOP, f"한도 소진, 초기화({usage.rejected_until:%m-%d %H:%M})가 {cfg.max_wait}보다 멂")

    if not starting_job:
        return Decision(Action.RUN, "작업 계속")

    if missing := usage_missing(now, usage, cfg):
        return Decision(Action.PROBE, missing)

    if usage.seven_util >= cfg.approval_threshold and not approved:
        return Decision(Action.ASK, f"주간 사용률 {usage.seven_util:.0%} ≥ {cfg.approval_threshold:.0%}, 작업 1건마다 승인 필요")

    return Decision(Action.RUN, f"주간 사용률 {usage.seven_util:.0%}" + (" (승인됨)" if approved else ""))
