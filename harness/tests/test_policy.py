from datetime import datetime, timedelta
from pathlib import Path

import pytest

from nightshift.policy import Action, Config, Usage, deadline, decide, daily_usage, learned, spend_until, weekly_ceiling

CFG = Config.load(Path(__file__).parents[1] / "nightshift.toml")
TZ = CFG.tz


def kst(day: int, hh: int, mm: int = 0) -> datetime:
    # 2026-09-14는 월요일
    return datetime(2026, 9, day, hh, mm, tzinfo=TZ)


def usage(now=None, five_reset=None, seven_util=None, seven_reset=None, rejected_until=None) -> Usage:
    """now를 주면 그 시각에 주간 사용률을 막 읽은 것으로 둔다."""
    return Usage(five_reset=five_reset, seven_util=seven_util, seven_reset=seven_reset,
                 rejected_until=rejected_until, observed_at=now if seven_util is not None else None)


def start(now, u, base=None, **kw):
    return decide(now, u, base, CFG, starting_job=True, **kw)


def running(now, u, base=None, **kw):
    return decide(now, u, base, CFG, starting_job=False, **kw)


def fresh_week(now, util=0.01, **kw):
    """새 주(화 04:00 초기화 직후) 기준 넉넉한 주간 상태."""
    return usage(now, seven_util=util, seven_reset=kst(22, 4), **kw)


# ── 5시간 창 ─────────────────────────────────────────────────────────────────


def test_deadline_is_next_morning_minus_margin():
    assert deadline(kst(14, 22), CFG) == kst(15, 8, 55)


def test_no_window_info_allows_until_fresh_limit():
    until, _ = spend_until(kst(14, 22), Usage(), CFG)
    assert until == kst(15, 3, 55)


def test_first_window_ending_before_fresh_limit_extends_to_fresh_limit():
    # 22:00에 연 창이 03:00에 끝남. 03:55까지는 새 창을 열어도 08:55 전에 끝난다
    until, _ = spend_until(kst(14, 23), Usage(five_reset=kst(15, 3)), CFG)
    assert until == kst(15, 3, 55)


def test_second_window_runs_until_its_own_reset():
    until, _ = spend_until(kst(15, 3, 10), Usage(five_reset=kst(15, 8, 10)), CFG)
    assert until == kst(15, 8, 5)


def test_no_new_window_after_fresh_limit():
    now = kst(15, 4, 10)
    assert start(now, fresh_week(now, five_reset=kst(15, 3))).action is Action.STOP


def test_window_reaching_into_morning_is_forbidden():
    # 04:30에 누군가 연 창은 09:30에 끝난다 → 아침 창 침범
    now = kst(15, 5)
    assert start(now, fresh_week(now, five_reset=kst(15, 9, 30))).action is Action.STOP


def test_stops_just_before_window_reset():
    now = kst(15, 7, 56)
    assert running(now, fresh_week(now, five_reset=kst(15, 8))).action is Action.STOP


def test_never_runs_in_work_hours():
    for now in (kst(15, 10), kst(15, 21, 59)):
        assert start(now, fresh_week(now)).action is Action.STOP


def test_user_evening_window_is_fair_game():
    # 사용자가 19:00에 연 창(00:00 종료)의 잔량은 루프가 써도 된다
    now = kst(14, 22)
    d = start(now, usage(now, five_reset=kst(15, 0), seven_util=0.70, seven_reset=kst(15, 4)))
    assert d.action is Action.RUN
    assert d.until == kst(15, 3, 55)


def test_rejected_waits_for_reset_within_night():
    now = kst(15, 1)
    d = start(now, fresh_week(now, five_reset=kst(15, 3), rejected_until=kst(15, 3)))
    assert d.action is Action.WAIT and d.until == kst(15, 3)


# ── 주간 한도 (2026-09-14 실측: 70%, 화 04:00 초기화) ─────────────────────────


def test_night_before_weekly_reset_may_use_everything_left():
    w = weekly_ceiling(kst(14, 22), kst(15, 4), 0.70, 0.11, CFG)
    assert w["work_days"] == 0 and w["nights"] == 1
    assert w["ceiling"] == pytest.approx(0.97)


def test_fresh_week_reserves_seven_workdays_and_spreads_over_nights():
    w = weekly_ceiling(kst(15, 4, 10), kst(22, 4), 0.01, 0.11, CFG)
    assert w["work_days"] == 7          # 화 09:00 … 다음 월 09:00
    assert w["nights"] == 8             # 월 22:00(오늘 밤) … 다음 월 22:00
    assert w["ceiling"] == pytest.approx(0.01 + (1 - 0.03 - 0.77 - 0.01) / 8)


def test_weekly_share_exhausted_waits_for_reset_if_it_comes_tonight():
    # 03:00에 연 창(08:00 종료) 안에서 주간 몫이 바닥남 → 04:00 주간 초기화까지 대기
    now = kst(15, 3, 30)
    u = usage(now, five_reset=kst(15, 8), seven_util=0.97, seven_reset=kst(15, 4))
    d = running(now, u, 0.70)
    assert d.action is Action.WAIT and d.until == kst(15, 4)


def test_weekly_share_exhausted_stops_when_reset_is_days_away():
    # 화 밤: W=6, N=7 → 상한 0.01 + 0.30/7 ≈ 5.3%
    now = kst(15, 23)
    assert running(now, usage(now, seven_util=0.06, seven_reset=kst(22, 4)), 0.01).action is Action.STOP


# B1: 여유가 조금 남았다고 새 작업을 시작하면 작업 1건이 사용자 몫을 먹는다
def test_b1_new_job_needs_headroom_for_expected_job_cost():
    # 일 22:00, 주간 초기화 화 04:00: W=1, N=2, 사용률 0.84 → 상한 0.85, 여유 1%
    now = kst(20, 22)
    u = usage(now, seven_util=0.84, seven_reset=kst(22, 4))
    assert start(now, u).action is Action.RUN                                        # 예상 비용 기본 1% → 딱 맞음
    assert start(now, u, job_cost_samples=[0.03, 0.04, 0.05]).action is Action.STOP  # 실측 비용 ~5% → 시작 불가
    assert not start(now, u).heavy_allowed                                           # 여유 1% < 5% → 무거운 스킬 차단


def test_b1_running_job_is_stopped_when_fresh_usage_reaches_ceiling():
    now = kst(20, 23)
    assert running(now, usage(now, seven_util=0.84, seven_reset=kst(22, 4)), 0.84).action is Action.RUN
    # probe가 새 사용률을 읽음
    assert running(now, usage(now, seven_util=0.85, seven_reset=kst(22, 4)), 0.84).action is Action.STOP


def test_b1_heavy_skills_allowed_only_with_large_headroom():
    now = kst(14, 22)
    assert start(now, usage(now, seven_util=0.70, seven_reset=kst(15, 4))).heavy_allowed  # 초기화 직전 밤, 여유 27%


# B2: 주간 정보가 없거나 오래되면 검사를 건너뛰지 않고 멈춘다
def test_b2_missing_weekly_usage_requires_probe():
    now = kst(14, 22)
    assert start(now, Usage()).action is Action.PROBE
    assert start(now, Usage(seven_reset=kst(15, 4))).action is Action.PROBE


def test_b2_stale_weekly_usage_requires_probe():
    now = kst(14, 23)
    u = usage(now - CFG.usage_max_age - timedelta(minutes=1), seven_util=0.70, seven_reset=kst(15, 4))
    assert running(now, u, 0.70).action is Action.PROBE


def test_b2_weekly_reset_in_the_past_requires_probe():
    now = kst(15, 4, 1)
    u = usage(now, five_reset=kst(15, 8), seven_util=0.97, seven_reset=kst(15, 4))
    assert start(now, u, 0.70).action is Action.PROBE


def test_b2_single_window_event_without_utilization_clears_weekly_usage():
    u, now = Usage(), kst(14, 22)
    u.update({"unifiedWindows": {"seven_day": {"utilization": 0.7, "resetsAt": 1789412400}}}, now)
    u.update({"status": "allowed_warning", "rateLimitType": "seven_day", "resetsAt": 1790017200}, now)
    assert u.seven_util is None and u.observed_at is None
    assert start(now, u).action is Action.PROBE


def test_learned_uses_p75_with_multiplier():
    assert daily_usage([0.1, 0.12], CFG) == CFG.daily_usage_default
    assert daily_usage([0.10, 0.12, 0.09, 0.08], CFG) == pytest.approx(0.10 * 1.2)  # nearest-rank p75 of 4 = 3rd
    assert learned([0.02, 0.03, 0.05], 0.01, CFG) == pytest.approx(0.05 * 1.2)


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
