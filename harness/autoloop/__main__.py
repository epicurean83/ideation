"""uv run --directory harness python -m autoloop {run,board,status,approval-url} [...]"""

from __future__ import annotations

import argparse
import json
import logging
import threading
from datetime import datetime

import anyio

from . import approval, board
from .policy import Config, Usage, decide
from .runner import EVENTS_FILE, HARNESS, PIPELINE, STATE_DIR, TOKEN_FILE, passed_count, run


def last_usage(cfg: Config) -> Usage:
    u = Usage()
    if EVENTS_FILE.exists():
        lines = EVENTS_FILE.read_text().splitlines()
        if lines:
            e = json.loads(lines[-1])
            u.update(e["raw"], datetime.fromisoformat(e["at"]).astimezone(cfg.tz))
    return u


def status(cfg: Config) -> None:
    now = datetime.now(cfg.tz)
    u = last_usage(cfg)
    print(f"주간 사용률 {cfg.approval_threshold:.0%} 미만: 자유 실행 / 이상: 작업 1건마다 승인 페이지에서 승인")
    if u.seven_util is not None and u.seven_reset:
        if u.seven_reset <= now:
            state = "그 뒤 주간 초기화가 지나 첫 probe에서 다시 읽는다"
        else:
            state = "승인 필요" if u.seven_util >= cfg.approval_threshold else "자유 실행"
        print(f"마지막 관측 ({u.observed_at:%m-%d %H:%M}): 주간 {u.seven_util:.0%}, 초기화 {u.seven_reset:%m-%d %a %H:%M}"
              f" → {state}")
    else:
        print("한도 관측 기록 없음 — 첫 작업 전에 probe로 읽는다")
    print(f"PIPELINE.md 통과(실증 대기): {passed_count()} / {cfg.target_passed}")
    d = decide(now, u, cfg, starting_job=True)
    print(f"지금 판정 (마지막 관측 기준): {d.action.value} — {d.reason}")


def approval_url(cfg: Config) -> None:
    host = approval.tailscale_ip()
    if host is None:
        print("Tailscale IP를 얻지 못했다. `tailscale status`를 확인하라.")
        return
    print(approval.ApprovalGate(host=host, port=cfg.approval_port, token=approval.load_token(TOKEN_FILE)).url)
    print("휴대폰에서 이 주소를 즐겨찾기해 두세요. 러너가 승인을 기다리는 동안에만 열린다.")


def serve_board(cfg: Config) -> None:
    host = approval.tailscale_ip()
    if host is None:
        print("Tailscale IP를 얻지 못했다. `tailscale status`를 확인하라.")
        return
    b = board.Board(host=host, port=cfg.board_port, token=approval.load_token(TOKEN_FILE), ideas_root=PIPELINE.parent,
                    target=cfg.target_passed, approval_port=cfg.approval_port)
    b.start()
    print(f"아이디어 보드: {b.url}", flush=True)
    print("휴대폰·PC에서 이 주소를 즐겨찾기하세요. Ctrl+C로 멈춘다.")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        b.stop()


def main() -> None:
    p = argparse.ArgumentParser(prog="autoloop")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="자동 루프 실행 (Ctrl+C로 멈춘다)")
    r.add_argument("--dry-run", action="store_true", help="판정·probe까지만 하고 작업·승인 요청은 하지 않는다")
    sub.add_parser("board", help="아이디어 보드 웹페이지 띄우기 (API 호출 없음)")
    sub.add_parser("status", help="마지막 관측 주간 사용률과 통과 개수 (API 호출 없음)")
    sub.add_parser("approval-url", help="승인 페이지 주소 (즐겨찾기용)")
    args = p.parse_args()

    cfg = Config.load(HARNESS / "autoloop.toml")
    if args.cmd == "board":
        serve_board(cfg)
        return
    if args.cmd == "status":
        status(cfg)
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
