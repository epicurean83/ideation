from datetime import datetime, timedelta
from pathlib import Path

from autoloop.policy import Action, Config, Usage, decide

CFG = Config.load(Path(__file__).parents[1] / "autoloop.toml")
TZ = CFG.tz


def kst(day: int, hh: int, mm: int = 0) -> datetime:
    # 2026-09-14는 월요일
    return datetime(2026, 9, day, hh, mm, tzinfo=TZ)


def usage(now=None, five_reset=None, seven_util=None, seven_reset=None, rejected_until=None) -> Usage:
    """now를 주면 그 시각에 주간 사용률을 막 읽은 것으로 둔다."""
    return Usage(five_reset=five_reset, seven_util=seven_util, seven_reset=seven_reset,
                 rejected_until=rejected_until, observed_at=now if seven_util is not None else None)


def start(now, u, **kw):
    return decide(now, u, CFG, starting_job=True, **kw)


def running(now, u):
    return decide(now, u, CFG, starting_job=False)


def week(now, util=0.30, **kw):
    """주간 초기화 다음 주 화 04:00, 사용률 util을 막 읽은 상태."""
    return usage(now, seven_util=util, seven_reset=kst(22, 4), **kw)


# ── 시간대 제한 없음 (2026-09-15 사용자 결정) ────────────────────────────────────


def test_runs_at_any_time_of_day():
    for now in (kst(15, 10), kst(15, 14, 30), kst(15, 21, 59), kst(16, 3), kst(16, 8, 30)):
        assert start(now, week(now)).action is Action.RUN
        assert running(now, week(now)).action is Action.RUN


# ── 주간 70% 승인 규칙 ─────────────────────────────────────────────────────────


def test_below_threshold_runs_freely():
    now = kst(15, 23)
    assert start(now, week(now, util=0.69)).action is Action.RUN


def test_at_or_above_threshold_asks_before_each_job():
    now = kst(15, 11)
    for util in (0.70, 0.95):
        assert start(now, week(now, util=util)).action is Action.ASK


def test_approval_lets_the_approved_job_start():
    now = kst(15, 23)
    assert start(now, week(now, util=0.80), approved=True).action is Action.RUN


def test_running_job_crossing_threshold_is_not_interrupted():
    now = kst(15, 23)
    assert running(now, week(now, util=0.85)).action is Action.RUN


# ── 한도 소진 ─────────────────────────────────────────────────────────────────


def test_rejected_waits_when_reset_is_near():
    now = kst(15, 1)
    d = start(now, week(now, rejected_until=kst(15, 3)))
    assert d.action is Action.WAIT and d.until == kst(15, 3)
    assert running(now, week(now, rejected_until=kst(15, 3))).action is Action.WAIT  # 도는 작업은 끊긴다


def test_rejected_stops_when_reset_is_far():
    now = kst(15, 1)
    assert start(now, week(now, rejected_until=now + CFG.max_wait + timedelta(minutes=1))).action is Action.STOP
    assert running(now, week(now, rejected_until=kst(22, 4))).action is Action.STOP


def test_rejected_wins_over_approval():
    now = kst(15, 1)
    assert start(now, week(now, util=0.99, rejected_until=kst(15, 3)), approved=True).action is Action.WAIT


# ── 정보 부족 시 fail-closed ────────────────────────────────────────────────────


def test_missing_or_stale_usage_requires_probe_before_starting():
    now = kst(14, 22)
    assert start(now, Usage()).action is Action.PROBE
    assert start(now, Usage(seven_reset=kst(15, 4))).action is Action.PROBE
    stale = usage(now - CFG.usage_max_age - timedelta(minutes=1), seven_util=0.30, seven_reset=kst(15, 4))
    assert start(now, stale).action is Action.PROBE
    past_reset = kst(15, 4, 1)
    u = usage(past_reset, seven_util=0.30, seven_reset=kst(15, 4))  # 주간 초기화 시각이 지남
    assert start(past_reset, u).action is Action.PROBE


def test_running_job_does_not_need_fresh_usage():
    now = kst(14, 23)
    stale = usage(now - timedelta(hours=1), seven_util=0.30, seven_reset=kst(15, 4))
    assert running(now, stale).action is Action.RUN


def test_single_window_event_without_utilization_clears_weekly_usage():
    u, now = Usage(), kst(14, 22)
    u.update({"unifiedWindows": {"seven_day": {"utilization": 0.3, "resetsAt": 1789412400}}}, now)
    u.update({"status": "allowed_warning", "rateLimitType": "seven_day", "resetsAt": 1790017200}, now)
    assert u.seven_util is None and u.observed_at is None
    assert start(now, u).action is Action.PROBE


def test_usage_update_parses_sdk_rate_limit_event():
    raw = {
        "status": "allowed", "resetsAt": 1789387200, "rateLimitType": "five_hour",
        "unifiedWindows": {
            "five_hour": {"utilization": 0.47, "resetsAt": 1789387200},
            "seven_day": {"utilization": 0.7, "resetsAt": 1789412400},
        },
    }
    u = Usage()
    u.update(raw, kst(14, 18, 47))
    assert u.five_reset == kst(14, 21) and u.five_util == 0.47
    assert u.seven_reset == kst(15, 4) and u.seven_util == 0.7
    assert u.observed_at == kst(14, 18, 47) and u.rejected_until is None


def test_rejected_event_sets_and_clears_rejection():
    u, now = Usage(), kst(15, 1)
    u.update({"status": "rejected", "rateLimitType": "five_hour", "resetsAt": 1789412400}, now)
    assert u.rejected_until == kst(15, 4)
    u.update({"status": "allowed", "unifiedWindows": {}}, now)
    assert u.rejected_until is None
