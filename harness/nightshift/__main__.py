"""uv run --project harness python -m nightshift {run,plan} [...]"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime

import anyio

from .policy import Config, Usage, daily_usage, deadline, decide, is_work_time, learned, weekly_ceiling
from .runner import EVENTS_FILE, HARNESS, STATE_DIR, load_state, passed_count, run


def last_usage(cfg: Config) -> Usage:
    u = Usage()
    if EVENTS_FILE.exists():
        lines = EVENTS_FILE.read_text().splitlines()
        if lines:
            e = json.loads(lines[-1])
            u.update(e["raw"], datetime.fromisoformat(e["at"]).astimezone(cfg.tz))
    return u


def plan(cfg: Config, at: datetime | None) -> None:
    now = at or datetime.now(cfg.tz)
    start = datetime.combine(now.date(), cfg.work_end, tzinfo=cfg.tz) if is_work_time(now, cfg) else now
    d = deadline(start, cfg)
    print(f"야간 시작 {start:%m-%d %a %H:%M}  →  토큰 소비 마감 D = {d:%m-%d %a %H:%M} (근무 시작 - {cfg.margin})")
    print(f"새 5시간 창을 열 수 있는 마지막 시각 = D - {cfg.window} = {d - cfg.window:%H:%M}")
    print("최선 시나리오 (야간 시작 시 열린 창이 없을 때):")
    t, i = start, 1
    while t + cfg.window <= d:
        print(f"  창 {i}: {t:%H:%M} ~ {t + cfg.window:%H:%M}")
        t, i = t + cfg.window, i + 1
    if i == 1:
        print("  없음 — 오늘 밤은 5시간 창을 하나도 온전히 쓸 수 없다")
    print(f"  루프 종료: {min(t, d):%H:%M} (이후 요청은 아침 창을 연다)")

    u = last_usage(cfg)
    state = load_state()
    samples = state.get("daytime_samples", [])
    job_costs = state.get("job_cost_samples", [])
    if u.seven_reset and u.seven_util is not None:
        print(f"\n마지막 관측 ({u.observed_at:%m-%d %H:%M}): 주간 {u.seven_util:.0%}, 초기화 {u.seven_reset:%m-%d %a %H:%M}")
        daily = daily_usage(samples, cfg)
        if u.seven_reset > start:
            w = weekly_ceiling(start, u.seven_reset, u.seven_util, daily, cfg)
            print(f"  초기화 전: 남은 근무일 {w['work_days']} × {daily:.1%} 예약, 남은 야간 {w['nights']}"
                  f" → 이번 야간 주간 상한 {w['ceiling']:.1%} (루프가 더 쓸 수 있는 몫 {max(0, w['ceiling'] - u.seven_util):.1%})")
        if u.seven_reset < d:
            print(f"  {u.seven_reset:%H:%M}에 주간이 초기화되면 새 주간 기준으로 다시 계산한다")
    else:
        print("\n한도 관측 기록 없음 — 첫 야간 실행 때 probe로 채운다")
    print(f"\n근무 시간 사용량 표본 {len(samples)}개, 적용값 {daily_usage(samples, cfg):.1%}/일")
    print(f"작업 1건 비용 표본 {len(job_costs)}개, 적용 예상치 {learned(job_costs, cfg.job_cost_default, cfg):.1%}p"
          f" (새 작업은 여유 ≥ max({cfg.min_headroom:.0%}, 예상치)일 때만 시작)")
    print(f"PIPELINE.md 통과(실증 대기): {passed_count()} / {cfg.target_passed}")
    d = decide(now, u, None, cfg, daytime_samples=samples, job_cost_samples=job_costs, starting_job=True)
    print(f"지금({now:%m-%d %H:%M}) 판정: {d.action.value} — {d.reason}")


def main() -> None:
    p = argparse.ArgumentParser(prog="nightshift")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="야간 루프 실행 (근무 시간이면 즉시 종료)")
    r.add_argument("--dry-run", action="store_true", help="판정·probe까지만 하고 작업은 시작하지 않는다")
    pl = sub.add_parser("plan", help="오늘 밤 시간표와 주간 상한 계산 (API 호출 없음)")
    pl.add_argument("--at", help="이 시각 기준으로 계산, 예: '2026-09-14 22:00'")
    args = p.parse_args()

    cfg = Config.load(HARNESS / "nightshift.toml")
    if args.cmd == "plan":
        at = datetime.fromisoformat(args.at).replace(tzinfo=cfg.tz) if args.at else None
        plan(cfg, at)
        return

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(STATE_DIR / f"{datetime.now(cfg.tz):%Y-%m-%d}.log")],
    )
    anyio.run(run, cfg, args.dry_run)


if __name__ == "__main__":
    main()
