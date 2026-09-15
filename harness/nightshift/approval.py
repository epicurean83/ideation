"""주간 사용률이 기준 이상일 때 작업 1건마다 사용자 승인을 받는 작은 웹 페이지.

- Tailscale IP에만 바인딩한다. tailnet 밖에서는 열리지 않는다.
- URL에 고정 토큰을 붙여 휴대폰에 즐겨찾기해 두고 연다. 토큰이 틀리면 403.
- 대기 중인 요청은 한 번에 하나. 승인하면 작업 1건만 허용되고, 다음 작업은 다시 묻는다.
- 외부 서비스·추가 의존성 없이 표준 라이브러리만 쓴다.
"""

from __future__ import annotations

import html
import json
import secrets
import subprocess
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


def tailscale_ip() -> str | None:
    try:
        out = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=10, check=True)
        return out.stdout.split()[0] if out.stdout.split() else None
    except (OSError, subprocess.SubprocessError):
        return None


def load_token(path: Path) -> str:
    if path.exists():
        return path.read_text().strip()
    path.parent.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(24)
    path.write_text(token)
    path.chmod(0o600)
    return token


@dataclass
class Request:
    id: str
    created_at: datetime
    info: dict
    choice: str | None = None  # "approve" | "deny" | "expired"
    decided_at: datetime | None = None


@dataclass
class ApprovalGate:
    host: str
    port: int
    token: str
    history: list[Request] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _server: ThreadingHTTPServer | None = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/?t={self.token}"

    @property
    def pending(self) -> Request | None:
        with self._lock:
            last = self.history[-1] if self.history else None
            return last if last and last.choice is None else None

    def open_request(self, info: dict) -> Request:
        with self._lock:
            for r in self.history:
                if r.choice is None:
                    r.choice = "expired"
            req = Request(id=uuid.uuid4().hex[:12], created_at=datetime.now().astimezone(), info=info)
            self.history = (self.history + [req])[-20:]
            return req

    def decide(self, req_id: str, choice: str) -> bool:
        if choice not in ("approve", "deny"):
            return False
        with self._lock:
            for r in self.history:
                if r.id == req_id and r.choice is None:
                    r.choice, r.decided_at = choice, datetime.now().astimezone()
                    return True
        return False

    def expire(self, req: Request) -> None:
        with self._lock:
            if req.choice is None:
                req.choice, req.decided_at = "expired", datetime.now().astimezone()

    def start(self) -> None:
        gate = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # 요청 로그는 러너 로그를 어지럽히지 않게 끈다
                pass

            def _authorized(self, token: str | None) -> bool:
                return token is not None and secrets.compare_digest(token, gate.token)

            def _send(self, status: int, body: str, content_type: str = "text/html; charset=utf-8") -> None:
                data = body.encode()
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                q = parse_qs(urlparse(self.path).query)
                if not self._authorized((q.get("t") or [None])[0]):
                    return self._send(403, "forbidden", "text/plain")
                if urlparse(self.path).path == "/status.json":
                    p = gate.pending
                    return self._send(200, json.dumps({"pending": p.id if p else None}), "application/json")
                self._send(200, render(gate))

            def do_POST(self):
                length = int(self.headers.get("Content-Length") or 0)
                form = parse_qs(self.rfile.read(min(length, 10_000)).decode())
                if not self._authorized((form.get("t") or [None])[0]):
                    return self._send(403, "forbidden", "text/plain")
                gate.decide((form.get("id") or [""])[0], (form.get("choice") or [""])[0])
                self.send_response(303)
                self.send_header("Location", f"/?t={gate.token}")
                self.end_headers()

        self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        threading.Thread(target=self._server.serve_forever, name="approval-gate", daemon=True).start()

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None


LABEL = {"approve": "승인", "deny": "거절", "expired": "만료", None: "대기 중"}


def render(gate: ApprovalGate) -> str:
    esc = html.escape
    p = gate.pending
    if p:
        rows = "".join(f"<tr><th>{esc(str(k))}</th><td>{esc(str(v))}</td></tr>" for k, v in p.info.items())
        body = f"""
<h1>작업 1건 승인 요청</h1>
<p class="muted">{p.created_at:%m-%d %H:%M} 요청</p>
<table>{rows}</table>
<form method="post">
  <input type="hidden" name="t" value="{esc(gate.token)}">
  <input type="hidden" name="id" value="{esc(p.id)}">
  <button name="choice" value="approve" class="ok">승인 — 작업 1건 실행</button>
  <button name="choice" value="deny" class="no">거절 — 오늘 밤 종료</button>
</form>"""
    else:
        body = "<h1>대기 중인 요청 없음</h1><p class=\"muted\">요청이 생기면 이 페이지를 새로고침하세요.</p>"
    past = "".join(
        f"<li>{r.created_at:%m-%d %H:%M} · {esc(LABEL[r.choice])}</li>" for r in reversed(gate.history) if r.choice
    )
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>nightshift 승인</title>
<style>
body{{font-family:system-ui,sans-serif;margin:0;padding:16px;background:#f6f6f4;color:#1b1b1b}}
h1{{font-size:1.25rem;margin:.2em 0}} .muted{{color:#666}} table{{border-collapse:collapse;margin:12px 0;width:100%}}
th{{text-align:left;padding:6px 8px 6px 0;color:#555;font-weight:500;white-space:nowrap;vertical-align:top}}
td{{padding:6px 0;word-break:break-all}} button{{display:block;width:100%;padding:14px;margin:8px 0;font-size:1rem;border:0;border-radius:10px}}
.ok{{background:#1f6f43;color:#fff}} .no{{background:#e4e4e0;color:#1b1b1b}} ul{{padding-left:18px;color:#555}}
</style></head><body>{body}<h2 style="font-size:1rem;margin-top:24px">최근 결정</h2><ul>{past or '<li>없음</li>'}</ul>
</body></html>"""
