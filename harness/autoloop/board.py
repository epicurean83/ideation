"""아이디어 보드: `통과(실증 대기)` 아이템을 바로 확인하는 작은 웹 페이지.

- `ideas/PIPELINE.md`와 `ideas/<slug>/` 파일을 요청마다 새로 읽는다. 루프가 돌면서 바뀐 내용이 새로고침으로 바로 보인다.
- 승인 페이지와 같은 방식: Tailscale IP에만 바인딩하고, 같은 토큰으로 접근한다. 첫 방문 뒤에는 쿠키로 유지한다.
- 마크다운은 HTML을 끈 markdown-it으로 렌더링한다. 문서에는 웹 원자료가 섞이므로 원문 HTML·스크립트를 실행하지 않는다.
- 파일은 `ideas/<slug>/` 안의 `.md`만 연다(경로 탈출 차단).
"""

from __future__ import annotations

import html
import json
import re
import secrets
import threading
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from markdown_it import MarkdownIt

PASSED = "통과(실증 대기)"
TERMINAL = {"종료", "보류"}
COOKIE = "autoloop_t"

# 통과 아이템 카드에 바로가기로 띄울 핵심 문서 (CLAUDE.md S4 산출물 세트 순서)
KEY_DOCS = [
    ("원페이저", "docs/one-pager.md"),
    ("PRD", "docs/prd.md"),
    ("스코어카드", "06-validation/scorecard.md"),
    ("피치 10분", "docs/pitch-10min.md"),
    ("실험", "06-validation/experiments.md"),
    ("포지셔닝", "02-strategy/positioning.md"),
    ("진행 기록", "PROGRESS.md"),
]

_md = MarkdownIt("commonmark", {"html": False, "linkify": False}).enable("table").enable("strikethrough")


def norm(label: str) -> str:
    return re.sub(r"\s", "", label)


# ── 데이터 읽기 ───────────────────────────────────────────────────────────────


def read_pipeline(path: Path) -> list[dict]:
    """PIPELINE.md 표를 헤더 이름을 키로 한 dict 목록으로."""
    if not path.exists():
        return []
    lines = [ln.strip() for ln in path.read_text().splitlines() if ln.strip().startswith("|")]
    if not lines:
        return []
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    rows = []
    for ln in lines[1:]:
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
            continue
        rows.append(dict(zip(header, cells + [""] * (len(header) - len(cells)))))
    return rows


def scorecard_overall(idea_dir: Path) -> str | None:
    """스코어카드 표의 Overall 행 점수."""
    f = idea_dir / "06-validation" / "scorecard.md"
    if not f.exists():
        return None
    for ln in f.read_text(errors="replace").splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) >= 2 and "overall" in cells[0].lower().replace("*", ""):
            m = re.search(r"\d+(?:\.\d+)?", cells[1])
            if m:
                return m.group(0)
    return None


def section(md_text: str, title: str) -> str:
    """제목에 title이 들어간 마크다운 절의 본문 (다음 같은 수준 이상 제목 전까지)."""
    lines = md_text.splitlines()
    for i, ln in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*)", ln)
        if m and title in m.group(2):
            level, body = len(m.group(1)), []
            for nxt in lines[i + 1:]:
                n = re.match(r"^(#{1,6})\s", nxt)
                if n and len(n.group(1)) <= level:
                    break
                body.append(nxt)
            return "\n".join(body).strip()
    return ""


def count_items(md_block: str) -> int:
    return sum(1 for ln in md_block.splitlines() if re.match(r"^\s*(?:[-*]|\d+\.)\s+\S", ln))


def list_docs(idea_dir: Path) -> list[str]:
    return sorted(str(p.relative_to(idea_dir)) for p in idea_dir.rglob("*.md") if p.is_file())


def safe_doc(ideas_root: Path, slug: str, rel: str) -> Path | None:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        return None
    idea_dir = (ideas_root / slug).resolve()
    target = (idea_dir / rel).resolve()
    if target.suffix != ".md" or idea_dir not in target.parents or not target.is_file():
        return None
    return target


# ── 렌더링 ────────────────────────────────────────────────────────────────────

CSS = """
:root{--bg:#f6f5f1;--card:#fff;--ink:#1c1b19;--muted:#6b6862;--line:#e4e1da;--accent:#1f6f43;--accent-bg:#e6f2ea;
--warn:#8a5a00;--warn-bg:#fdf1d8;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--card:#1f1e1b;--ink:#ecebe6;--muted:#a19e96;--line:#34322d;
--accent:#6cc494;--accent-bg:#1d3326;--warn:#f0c060;--warn-bg:#3a2e12;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif}
main{max-width:860px;margin:0 auto;padding:20px 16px 48px}
a{color:var(--accent)}h1{font-size:1.4rem;margin:.2em 0 .1em}h2{font-size:1.05rem;margin:28px 0 10px}
.muted{color:var(--muted)}.small{font-size:.85rem}
.top{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
.stats{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 4px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 12px;min-width:92px}
.stat b{display:block;font-size:1.3rem;font-variant-numeric:tabular-nums}
.banner{background:var(--warn-bg);color:var(--warn);border-radius:10px;padding:10px 14px;margin:14px 0;font-weight:600}
.banner a{color:inherit}
.cards{display:grid;gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.card h3{margin:0 0 2px;font-size:1.05rem}.card h3 a{color:var(--ink);text-decoration:none}
.meta{display:flex;gap:6px 14px;flex-wrap:wrap;margin:8px 0;font-size:.88rem;color:var(--muted)}
.score{background:var(--accent-bg);color:var(--accent);border-radius:999px;padding:1px 9px;font-weight:600}
.links{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
.links a{border:1px solid var(--line);border-radius:8px;padding:5px 10px;text-decoration:none;font-size:.88rem;color:var(--ink)}
.empty{background:var(--card);border:1px dashed var(--line);border-radius:12px;padding:22px;text-align:center;color:var(--muted)}
.tablewrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:12px}
table{border-collapse:collapse;width:100%;font-size:.9rem}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:500;white-space:nowrap}tr:last-child td{border-bottom:0}
details{margin-top:12px}summary{cursor:pointer;color:var(--muted)}
.doc{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:6px 18px 18px;overflow-wrap:anywhere}
.doc table{display:block;overflow-x:auto}.doc pre{overflow-x:auto;background:var(--bg);padding:10px;border-radius:8px}
.doc code{font-size:.9em}.doc blockquote{margin:0;padding-left:12px;border-left:3px solid var(--line);color:var(--muted)}
ul.files{padding-left:18px}ul.files li{margin:3px 0}
td.slug{white-space:nowrap}td.problem{min-width:11em}
@media (max-width:560px){.wide{display:none}}
"""


def page(title: str, body: str, refresh: bool = False) -> str:
    meta = '<meta http-equiv="refresh" content="60">' if refresh else ""
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">{meta}'
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body><main>{body}</main></body></html>")


def render_board(rows: list[dict], ideas_root: Path, target: int, approval_pending: bool, approval_url: str | None,
                 now: datetime) -> str:
    esc = html.escape
    passed = [r for r in rows if norm(r.get("판정", "")) == norm(PASSED)]
    closed = [r for r in rows if norm(r.get("판정", "")) in TERMINAL]
    active = [r for r in rows if r not in passed and r not in closed]

    banner = ""
    if approval_pending:
        link = f' — <a href="{esc(approval_url)}">승인 페이지 열기</a>' if approval_url else ""
        banner = f'<div class="banner">루프가 다음 작업 승인을 기다리고 있습니다{link}</div>'

    stats = "".join(f'<div class="stat"><b>{v}</b><span class="small muted">{k}</span></div>' for k, v in [
        ("통과(실증 대기)", f"{len(passed)} / {target}"), ("진행 중", len(active)), ("종료·보류", len(closed))])

    if passed:
        cards = []
        for r in sorted(passed, key=lambda r: r.get("갱신일", ""), reverse=True):
            slug = r.get("slug", "")
            idea_dir = ideas_root / slug
            score = scorecard_overall(idea_dir) if idea_dir.is_dir() else None
            progress = (idea_dir / "PROGRESS.md").read_text(errors="replace") if (idea_dir / "PROGRESS.md").exists() else ""
            questions = count_items(section(progress, "인터뷰 대기 질문"))
            links = "".join(f'<a href="/doc/{quote(slug)}/{quote(rel)}">{esc(label)}</a>'
                            for label, rel in KEY_DOCS if (idea_dir / rel).is_file())
            meta = [f'<span class="score">스코어 {esc(score)}</span>' if score else "",
                    f"인터뷰 대기 질문 {questions}개" if questions else "",
                    f"갱신 {esc(r.get('갱신일', ''))}" if r.get("갱신일") else ""]
            cards.append(
                f'<article class="card"><h3><a href="/idea/{quote(slug)}">{esc(slug)}</a></h3>'
                f'<div>{esc(r.get("한 줄 문제 정의", ""))}</div>'
                f'<div class="meta">{"".join(f"<span>{m}</span>" for m in meta if m)}</div>'
                f'<div class="small muted">다음: {esc(r.get("다음 액션", "") or "-")}</div>'
                f'<div class="links">{links or '<span class="small muted">문서 없음</span>'}</div></article>')
        passed_html = f'<div class="cards">{"".join(cards)}</div>'
    else:
        passed_html = '<div class="empty">아직 통과한 아이디어가 없습니다. 루프가 G4를 넘기면 여기에 나타납니다.</div>'

    def table(items: list[dict]) -> str:
        if not items:
            return '<p class="muted small">없음</p>'
        # 좁은 화면에서는 .wide 열(게이트·다음 액션·갱신일)을 숨긴다
        cols = [("slug", ""), ("문제", ""), ("단계", ""), ("게이트", "wide"), ("판정", ""), ("다음 액션", "wide"), ("갱신일", "wide")]
        head = "".join(f'<th class="{c}">{h}</th>' for h, c in cols)
        body = "".join(
            f'<tr><td class="slug"><a href="/idea/{quote(r.get("slug", ""))}">{esc(r.get("slug", ""))}</a></td>'
            f'<td class="problem">{esc(r.get("한 줄 문제 정의", ""))}</td><td>{esc(r.get("현재 단계", ""))}</td>'
            f'<td class="wide">{esc(r.get("마지막 게이트", ""))}</td><td class="slug">{esc(r.get("판정", ""))}</td>'
            f'<td class="wide">{esc(r.get("다음 액션", ""))}</td><td class="wide">{esc(r.get("갱신일", ""))}</td></tr>'
            for r in items)
        return f'<div class="tablewrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'

    body = (f'<div class="top"><h1>아이디어 보드</h1><span class="small muted">{now:%m-%d %H:%M} 기준 · 1분마다 새로고침</span></div>'
            f"{banner}<div class=\"stats\">{stats}</div>"
            f"<h2>통과(실증 대기)</h2>{passed_html}"
            f"<h2>진행 중</h2>{table(active)}"
            f"<details><summary>종료·보류 {len(closed)}건</summary>{table(closed)}</details>")
    return page("아이디어 보드", body, refresh=True)


def render_idea(slug: str, row: dict | None, ideas_root: Path) -> str:
    esc = html.escape
    idea_dir = ideas_root / slug
    docs = list_docs(idea_dir) if idea_dir.is_dir() else []
    progress = (idea_dir / "PROGRESS.md").read_text(errors="replace") if (idea_dir / "PROGRESS.md").exists() else ""
    questions = section(progress, "인터뷰 대기 질문")
    score = scorecard_overall(idea_dir) if idea_dir.is_dir() else None

    groups: dict[str, list[str]] = {}
    for rel in docs:
        groups.setdefault(rel.split("/")[0] if "/" in rel else "(최상위)", []).append(rel)
    files = "".join(
        f"<h2>{esc(g)}</h2><ul class=\"files\">"
        + "".join(f'<li><a href="/doc/{quote(slug)}/{quote(r)}">{esc(r)}</a></li>' for r in rels) + "</ul>"
        for g, rels in groups.items())

    info = ""
    if row:
        info = "".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in row.items() if k != "slug")
        if score:
            info += f"<tr><th>스코어카드</th><td>{esc(score)}</td></tr>"
        info = f'<div class="tablewrap"><table>{info}</table></div>'
    body = (f'<p class="small"><a href="/">← 보드</a></p><h1>{esc(slug)}</h1>{info}'
            + (f'<h2>인터뷰 대기 질문</h2><div class="doc">{_md.render(questions)}</div>' if questions else "")
            + (files or '<p class="muted">문서 없음</p>'))
    return page(slug, body)


def render_doc(slug: str, rel: str, path: Path) -> str:
    body = (f'<p class="small"><a href="/">보드</a> / <a href="/idea/{quote(slug)}">{html.escape(slug)}</a> / '
            f"{html.escape(rel)}</p><div class=\"doc\">{_md.render(path.read_text(errors='replace'))}</div>")
    return page(f"{slug} · {rel}", body)


# ── 서버 ─────────────────────────────────────────────────────────────────────


@dataclass
class Board:
    host: str
    port: int
    token: str
    ideas_root: Path
    target: int
    approval_port: int | None = None
    _server: ThreadingHTTPServer | None = field(default=None, repr=False)

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/?t={self.token}"

    def approval_url(self) -> str | None:
        return f"http://{self.host}:{self.approval_port}/?t={self.token}" if self.approval_port else None

    def approval_pending(self) -> bool:
        """같은 머신에서 루프가 승인을 기다리는 중인지. 승인 페이지가 안 떠 있으면 False."""
        if not self.approval_port:
            return False
        try:
            with urllib.request.urlopen(
                    f"http://{self.host}:{self.approval_port}/status.json?t={self.token}", timeout=1) as r:
                return bool(json.load(r).get("pending"))
        except Exception:
            return False

    def handle(self, path: str, token: str | None) -> tuple[int, str, dict]:
        """(status, body, extra headers). HTTP 없이 테스트할 수 있게 분리했다."""
        if token is None or not secrets.compare_digest(token, self.token):
            return 403, "forbidden", {}
        parts = [unquote(p) for p in urlparse(path).path.split("/") if p]
        pipeline = read_pipeline(self.ideas_root / "PIPELINE.md")
        if not parts:
            return 200, render_board(pipeline, self.ideas_root, self.target, self.approval_pending(),
                                     self.approval_url(), datetime.now().astimezone()), {}
        if parts[0] == "idea" and len(parts) == 2:
            slug = parts[1]
            row = next((r for r in pipeline if r.get("slug") == slug), None)
            if row is None and not (re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug) and (self.ideas_root / slug).is_dir()):
                return 404, page("없음", '<p>그런 아이디어가 없습니다. <a href="/">보드로</a></p>'), {}
            return 200, render_idea(slug, row, self.ideas_root), {}
        if parts[0] == "doc" and len(parts) >= 3:
            slug, rel = parts[1], "/".join(parts[2:])
            target = safe_doc(self.ideas_root, slug, rel)
            if target is None:
                return 404, page("없음", '<p>그런 문서가 없습니다. <a href="/">보드로</a></p>'), {}
            return 200, render_doc(slug, rel, target), {}
        return 404, page("없음", '<p><a href="/">보드로</a></p>'), {}

    def start(self) -> None:
        board = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                q = parse_qs(urlparse(self.path).query)
                cookie = dict(c.strip().split("=", 1) for c in (self.headers.get("Cookie") or "").split(";") if "=" in c)
                token = (q.get("t") or [None])[0] or cookie.get(COOKIE)
                status, body, headers = board.handle(self.path, token)
                data = body.encode()
                self.send_response(status)
                self.send_header("Content-Type", "text/html; charset=utf-8" if status != 403 else "text/plain")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; img-src 'self'")
                if status != 403 and q.get("t"):
                    self.send_header("Set-Cookie", f"{COOKIE}={board.token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=31536000")
                for k, v in headers.items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(data)

        self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        threading.Thread(target=self._server.serve_forever, name="board", daemon=True).start()

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
