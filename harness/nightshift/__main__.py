"""uv run --directory harness python -m nightshift {run,plan,approval-url} [...]"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime

import anyio

from . import approval
from .policy import Config, Usage, deadline, decide, is_work_time
from .runner import EVENTS_FILE, HARNESS, STATE_DIR, TOKEN_FILE, passed_count, run


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
    print(f"\n주간 사용률 {cfg.approval_threshold:.0%} 미만: 자유 실행 / 이상: 작업 1건마다 승인 페이지에서 승인")
    if u.seven_util is not None and u.seven_reset:
        if u.seven_reset <= start:
            state = "그 뒤 주간 초기화가 지나 첫 probe에서 다시 읽는다"
        else:
            state = "승인 필요" if u.seven_util >= cfg.approval_threshold else "자유 실행"
        print(f"마지막 관측 ({u.observed_at:%m-%d %H:%M}): 주간 {u.seven_util:.0%}, 초기화 {u.seven_reset:%m-%d %a %H:%M}"
              f" → {state}")
    else:
        print("한도 관측 기록 없음 — 첫 작업 전에 probe로 읽는다")
    print(f"PIPELINE.md 통과(실증 대기): {passed_count()} / {cfg.target_passed}")
    d = decide(now, u, cfg, starting_job=True)
    print(f"지금({now:%m-%d %H:%M}) 판정: {d.action.value} — {d.reason}")


def approval_url(cfg: Config) -> None:
    host = approval.tailscale_ip()
    if host is None:
        print("Tailscale IP를 얻지 못했다. `tailscale status`를 확인하라.")
        return
    print(approval.ApprovalGate(host=host, port=cfg.approval_port, token=approval.load_token(TOKEN_FILE)).url)
    print("휴대폰에서 이 주소를 즐겨찾기해 두세요. 러너가 승인을 기다리는 동안에만 열린다.")


def main() -> None:
    p = argparse.ArgumentParser(prog="nightshift")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="야간 루프 실행 (근무 시간이면 즉시 종료)")
    r.add_argument("--dry-run", action="store_true", help="판정·probe까지만 하고 작업·승인 요청은 하지 않는다")
    pl = sub.add_parser("plan", help="오늘 밤 시간표와 주간 상태 (API 호출 없음)")
    pl.add_argument("--at", help="이 시각 기준으로 계산, 예: '2026-09-14 22:00'")
    sub.add_parser("approval-url", help="승인 페이지 주소 (즐겨찾기용)")
    args = p.parse_args()

    cfg = Config.load(HARNESS / "nightshift.toml")
    if args.cmd == "plan":
        plan(cfg, datetime.fromisoformat(args.at).replace(tzinfo=cfg.tz) if args.at else None)
        return
    if args.cmd == "approval-url":
        approval_url(cfg)
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
