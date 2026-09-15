"""아이디어 보드 테스트. HTTP 없이 Board.handle로 확인하고, 하나만 실제 서버로 확인한다."""

import socket
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from autoloop import board as B

HEADER = "| slug | 한 줄 문제 정의 | 현재 단계 | 마지막 게이트 | 판정 | 다음 액션 | 갱신일 |\n|---|---|---|---|---|---|---|\n"


@pytest.fixture
def ideas(tmp_path: Path) -> Path:
    root = tmp_path / "ideas"
    (root / "cafe-waste" / "docs").mkdir(parents=True)
    (root / "cafe-waste" / "06-validation").mkdir()
    (root / "pet-meds" ).mkdir()
    (root / "PIPELINE.md").write_text(
        "# 아이디어 파이프라인\n\n" + HEADER
        + "| cafe-waste | 카페 원두 찌꺼기 처리비 | S5 | G4 | 통과(실증 대기) | 프로토타입 착수 결정 | 2026-09-16 |\n"
        + "| pet-meds | 반려동물 상비약 | S2 | G1 | 진행 중 | 시장 리서치 | 2026-09-15 |\n"
        + "| old-idea | 오래된 것 | S1 | G0 | 종료 | - | 2026-09-10 |\n")
    (root / "cafe-waste" / "docs" / "one-pager.md").write_text("# 원페이저\n\n<script>alert(1)</script>\n\n[x](javascript:alert(1))\n")
    (root / "cafe-waste" / "06-validation" / "scorecard.md").write_text(
        "| Dimension | Score (1-10) | Rationale |\n|---|---|---|\n| Timing | 7 | ok |\n| **Overall** | **6.8** | 조건부 |\n")
    (root / "cafe-waste" / "PROGRESS.md").write_text(
        "# PROGRESS\n\n## 인터뷰 대기 질문\n- 카페 점주는 처리비를 따로 인식하나 — 데스크로는 인식 여부를 못 봄\n- 월 몇 kg인가\n\n## 야간 가정\n- x\n")
    return root


def make(ideas: Path, **kw) -> B.Board:
    return B.Board(host="127.0.0.1", port=0, token="tok", ideas_root=ideas, target=10, **kw)


def test_parses_pipeline_rows(ideas):
    rows = B.read_pipeline(ideas / "PIPELINE.md")
    assert [r["slug"] for r in rows] == ["cafe-waste", "pet-meds", "old-idea"]
    assert rows[0]["판정"] == "통과(실증 대기)"


def test_board_shows_passed_ideas_first_with_score_and_questions(ideas):
    status, body, _ = make(ideas).handle("/", "tok")
    assert status == 200
    passed_section = body.split("<h2>진행 중</h2>")[0]
    assert "cafe-waste" in passed_section and "pet-meds" not in passed_section
    assert "스코어 6.8" in body and "인터뷰 대기 질문 2개" in body and "1 / 10" in body
    assert "/doc/cafe-waste/docs/one-pager.md" in body and "/doc/cafe-waste/docs/prd.md" not in body  # 있는 문서만


def test_empty_state(tmp_path):
    (tmp_path / "PIPELINE.md").write_text(HEADER)
    _, body, _ = make(tmp_path).handle("/", "tok")
    assert "아직 통과한 아이디어가 없습니다" in body


def test_spacing_variants_count_as_passed(ideas):
    p = ideas / "PIPELINE.md"
    p.write_text(p.read_text().replace("통과(실증 대기)", "통과 (실증 대기)"))
    _, body, _ = make(ideas).handle("/", "tok")
    assert "1 / 10" in body


def test_wrong_or_missing_token_is_forbidden(ideas):
    assert make(ideas).handle("/", "nope")[0] == 403
    assert make(ideas).handle("/", None)[0] == 403


@pytest.mark.parametrize("path", [
    "/doc/cafe-waste/../pet-meds/x.md",
    "/doc/cafe-waste/%2e%2e/%2e%2e/PIPELINE.md",
    "/doc/cafe-waste/docs/one-pager.txt",
    "/doc/..%2F..%2Fetc/passwd.md",
    "/doc/Cafe_Waste/docs/one-pager.md",
])
def test_doc_path_escape_is_blocked(ideas, path):
    assert make(ideas).handle(path, "tok")[0] == 404


def test_doc_renders_markdown_without_raw_html_or_js_links(ideas):
    status, body, _ = make(ideas).handle("/doc/cafe-waste/docs/one-pager.md", "tok")
    assert status == 200 and "<h1>원페이저</h1>" in body
    assert "<script>" not in body and "&lt;script&gt;" in body
    assert 'href="javascript' not in body


def test_idea_page_lists_docs_and_interview_questions(ideas):
    status, body, _ = make(ideas).handle("/idea/cafe-waste", "tok")
    assert status == 200 and "인터뷰 대기 질문" in body and "월 몇 kg인가" in body
    assert "docs/one-pager.md" in body and "06-validation/scorecard.md" in body
    assert make(ideas).handle("/idea/nope", "tok")[0] == 404


def test_scorecard_overall_parsing(tmp_path):
    (tmp_path / "06-validation").mkdir()
    f = tmp_path / "06-validation" / "scorecard.md"
    f.write_text("| **Overall** | 7/10 | x |\n")
    assert B.scorecard_overall(tmp_path) == "7"
    f.write_text("점수 없음\n")
    assert B.scorecard_overall(tmp_path) is None


def test_serves_over_http_with_cookie_after_first_visit(ideas):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    b = B.Board(host="127.0.0.1", port=port, token="tok", ideas_root=ideas, target=10)
    b.start()
    try:
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/")
        assert e.value.code == 403
        r = urllib.request.urlopen(b.url)
        cookie = r.headers["Set-Cookie"].split(";")[0]
        assert "HttpOnly" in r.headers["Set-Cookie"] and "default-src 'none'" in r.headers["Content-Security-Policy"]
        req = urllib.request.Request(f"http://127.0.0.1:{port}/idea/cafe-waste", headers={"Cookie": cookie})
        assert "cafe-waste" in urllib.request.urlopen(req).read().decode()
    finally:
        b.stop()
