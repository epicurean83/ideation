#!/usr/bin/env bash
# 야간 루프를 systemd --user 타이머로 설치한다.
#   ./install-systemd.sh           유닛 파일만 설치 (타이머 비활성)
#   ./install-systemd.sh --enable  타이머까지 켠다
#   ./install-systemd.sh --disable 타이머를 끈다
set -euo pipefail

HARNESS="$(cd "$(dirname "$0")" && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UV="$(command -v uv)"
CLAUDE_BIN_DIR="$(dirname "$(command -v claude)")"

read_cfg() { sed -n "s/^$1 *= *\"\(.*\)\".*/\1/p" "$HARNESS/nightshift.toml"; }
TZ_NAME="$(read_cfg timezone)"        # Asia/Seoul
WORK_START="$(read_cfg work_start)"   # 09:00
WORK_END="$(read_cfg work_end)"       # 22:00
# workdays = [0, 1, ...] (월=0) → systemd 요일 목록 Mon,Tue,...
WORKDAYS="$(sed -n 's/^workdays *= *\[\(.*\)\].*/\1/p' "$HARNESS/nightshift.toml" \
  | tr -d ' ' | tr ',' '\n' | while read -r d; do echo "Mon Tue Wed Thu Fri Sat Sun" | cut -d' ' -f$((d + 1)); done | paste -sd,)"
# 러너가 규칙대로 먼저 멈추지만, 버그가 있어도 근무 시작 3분 전에는 반드시 죽인다
KILL_AT="$(date -d "$WORK_START today - 3 minutes" +%H:%M)"

mkdir -p "$UNIT_DIR"

cat > "$UNIT_DIR/ideation-nightshift.service" <<UNIT
[Unit]
Description=Ideation night-shift loop ($HARNESS)

[Service]
Type=simple
WorkingDirectory=$HARNESS
Environment=PATH=$CLAUDE_BIN_DIR:/usr/local/bin:/usr/bin:/bin
Environment=TZ=$TZ_NAME
# API 키가 있으면 구독 대신 API로 과금된다. 루프는 구독으로만 돈다
UnsetEnvironment=ANTHROPIC_API_KEY
ExecStart=$UV run --project $HARNESS python -m nightshift run
KillSignal=SIGTERM
TimeoutStopSec=150
UNIT

cat > "$UNIT_DIR/ideation-nightshift.timer" <<UNIT
[Unit]
Description=Start ideation night-shift loop at $WORK_END

[Timer]
OnCalendar=*-*-* $WORK_END:00 $TZ_NAME
# 꺼져 있다가 켜졌을 때 놓친 실행을 몰아서 하지 않는다 (근무 시간에 돌 위험)
Persistent=false
AccuracySec=1min

[Install]
WantedBy=timers.target
UNIT

cat > "$UNIT_DIR/ideation-nightshift-kill.service" <<UNIT
[Unit]
Description=Hard stop for ideation night-shift loop

[Service]
Type=oneshot
ExecStart=/usr/bin/systemctl --user stop ideation-nightshift.service
UNIT

cat > "$UNIT_DIR/ideation-nightshift-kill.timer" <<UNIT
[Unit]
Description=Hard stop ideation night-shift loop at $KILL_AT on workdays

[Timer]
OnCalendar=$WORKDAYS *-*-* $KILL_AT:00 $TZ_NAME
Persistent=true

[Install]
WantedBy=timers.target
UNIT

systemctl --user daemon-reload
echo "유닛 설치: $UNIT_DIR/ideation-nightshift{,-kill}.{service,timer}"
echo "시작 매일 $WORK_END, 강제 종료 $WORKDAYS $KILL_AT ($TZ_NAME)"

case "${1:-}" in
  --enable)
    systemctl --user enable --now ideation-nightshift.timer ideation-nightshift-kill.timer
    systemctl --user list-timers 'ideation-nightshift*' --no-pager ;;
  --disable)
    systemctl --user disable --now ideation-nightshift.timer ideation-nightshift-kill.timer
    systemctl --user stop ideation-nightshift.service || true ;;
esac
