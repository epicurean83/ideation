"""언제 토큰을 써도 되는지 판정한다. 부수효과 없는 순수 함수만 둔다.

지켜야 할 불변식은 하나다: 사용자가 근무를 시작하는 시각(work_start)에
사용자의 5시간 창과 주간 한도 몫이 루프 때문에 줄어 있으면 안 된다.
정보가 없거나 오래됐으면 항상 멈추는 쪽(fail-closed)으로 판정한다.

5시간 창 규칙
  창은 "직전 창이 끝난 뒤 첫 요청" 시각에 열린다. 2026-09-14 로컬 기록으로 복원하면
  종료 시각 = 시작 시각을 정시로 내림 + 5h 였다(16:01:50 시작 → 21:00 종료).
  아래 계산은 내림 없이 시작 + 5h로 잡으므로 실제보다 늦게 끝난다고 가정한다(보수적).
  D = 다음 work_start - safety_margin 이라고 하면:
  - 지금 요청이 새 창을 열어도 now + 5h <= D 이면 안전하다. 그 경계가 fresh_limit = D - 5h.
  - 이미 열린 창의 종료 시각 R을 알고 R <= D 이면, R 직전까지는 그 창 안이므로 안전하다.
  - 그 밖에는 요청 하나가 사용자 아침 창을 열거나 갉아먹을 수 있으므로 멈춘다.

주간 한도 규칙
  주간 초기화 전까지 남은 근무일 W, 남은 야간 N에 대해
  루프 몫 = 1 - reserve_safety - daily × W - 야간 시작 시 사용률,
  이번 야간 상한 = 야간 시작 사용률 + 루프 몫 / N.
  작업을 새로 시작하려면 상한까지 여유가 작업 1건 예상 비용 이상이어야 하고,
  작업 중에는 사용률이 상한 - stop_margin에 닿으면 멈춘다.
  초기화 직전 야간(W=0, N=1)에는 어차피 사라질 잔량을 전부 쓸 수 있다.
"""

from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass, field
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
    probe_every: timedelta
    daily_usage_default: float
    reserve_safety: float
    job_cost_default: float
    min_headroom: float
    heavy_headroom: float
    stop_margin: float
    learn_min_samples: int
    learn_multiplier: float
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
            probe_every=timedelta(minutes=raw["probe_every_minutes"]),
            daily_usage_default=weekly["daily_usage_default"],
            reserve_safety=weekly["reserve_safety"],
            job_cost_default=weekly["job_cost_default"],
            min_headroom=weekly["min_headroom"],
            heavy_headroom=weekly["heavy_headroom"],
            stop_margin=weekly["stop_margin"],
            learn_min_samples=weekly["learn_min_samples"],
            learn_multiplier=weekly["learn_multiplier"],
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
    PROBE = "probe"  # 주간 정보가 없거나 오래됨 → 한 번 읽고 다시 판정. 그래도 이러면 멈춘다
    WAIT = "wait"
    STOP = "stop"


@dataclass(frozen=True)
class Decision:
    action: Action
    until: datetime
    reason: str
    detail: dict = field(default_factory=dict)

    @property
    def heavy_allowed(self) -> bool:
        return bool(self.detail.get("heavy_allowed"))


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


# ── 주간 한도 ────────────────────────────────────────────────────────────────


def count_starts(t: time, start: datetime, end: datetime, cfg: Config, workdays_only: bool) -> int:
    """[start, end) 안에 있는 매일 t 시각의 개수."""
    n = 0
    day = start.astimezone(cfg.tz) - timedelta(days=1)
    while day.date() <= end.date():
        at = _at(day, t, cfg)
        if start <= at < end and (not workdays_only or at.weekday() in cfg.workdays):
            n += 1
        day += timedelta(days=1)
    return n


def night_start(now: datetime, cfg: Config) -> datetime:
    """now가 속한 야간의 시작 시각(가장 최근 work_end)."""
    now = now.astimezone(cfg.tz)
    today_end = _at(now, cfg.work_end, cfg)
    return today_end if now >= today_end else today_end - timedelta(days=1)


def reset_key(reset: datetime) -> str:
    """주간 초기화 시각을 정시로 맞춘 키. resetsAt이 몇 초 흔들려도 같은 주간으로 본다."""
    return str(round(reset.timestamp() / 3600))


def learned(samples: list[float], default: float, cfg: Config) -> float:
    """표본이 충분하면 nearest-rank 75백분위 × 안전 계수, 아니면 기본값."""
    if len(samples) < cfg.learn_min_samples:
        return default
    ordered = sorted(samples)
    return ordered[max(0, math.ceil(0.75 * len(ordered)) - 1)] * cfg.learn_multiplier


def daily_usage(samples: list[float], cfg: Config) -> float:
    return learned(samples, cfg.daily_usage_default, cfg)


def weekly_ceiling(now: datetime, seven_reset: datetime, base_util: float, daily: float, cfg: Config) -> dict:
    work_days = count_starts(cfg.work_start, next_work_start(now, cfg), seven_reset, cfg, workdays_only=True)
    nights = max(1, count_starts(cfg.work_end, night_start(now, cfg), seven_reset, cfg, workdays_only=False))
    share = 1 - cfg.reserve_safety - daily * work_days - base_util
    ceiling = base_util + max(0.0, share) / nights
    return {"ceiling": ceiling, "work_days": work_days, "nights": nights, "loop_share": share, "daily": daily}


def usage_missing(now: datetime, usage: Usage, cfg: Config) -> str | None:
    if usage.seven_util is None or usage.seven_reset is None or usage.observed_at is None:
        return "주간 사용률 정보 없음"
    if usage.seven_reset <= now:
        return "주간 초기화가 지나 사용률을 다시 읽어야 함"
    if now - usage.observed_at > cfg.usage_max_age:
        return f"주간 사용률이 {cfg.usage_max_age} 넘게 갱신되지 않음"
    return None


# ── 종합 판정 ────────────────────────────────────────────────────────────────


def decide(
    now: datetime,
    usage: Usage,
    base_util: float | None,
    cfg: Config,
    *,
    daytime_samples: list[float] = (),
    job_cost_samples: list[float] = (),
    starting_job: bool,
) -> Decision:
    """지금 토큰을 써도 되는가.

    base_util: 이번 주간 기간에서 이 야간이 시작될 때의 주간 사용률.
    starting_job: 새 작업을 시작하려는가(여유 ≥ 작업 1건 예상 비용 요구), 도는 작업을 계속하려는가.
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

    if missing := usage_missing(now, usage, cfg):
        return Decision(Action.PROBE, until, missing)

    base = usage.seven_util if base_util is None else base_util
    w = weekly_ceiling(now, usage.seven_reset, base, daily_usage(list(daytime_samples), cfg), cfg)
    headroom = w["ceiling"] - usage.seven_util
    job_cost = learned(list(job_cost_samples), cfg.job_cost_default, cfg)
    need = max(cfg.min_headroom, job_cost) if starting_job else cfg.stop_margin
    w |= {"headroom": headroom, "need": need, "job_cost": job_cost, "heavy_allowed": headroom >= cfg.heavy_headroom}

    if (headroom < need) if starting_job else (headroom <= need):
        msg = (f"이번 야간 주간 몫 부족 (사용 {usage.seven_util:.1%}, 상한 {w['ceiling']:.1%}, "
               f"여유 {headroom:.1%} < 필요 {need:.1%})")
        if usage.seven_reset < until:
            return Decision(Action.WAIT, usage.seven_reset, msg + ", 주간 초기화 후 재계산", w)
        return Decision(Action.STOP, now, msg, w)

    return Decision(Action.RUN, until, why, w)
