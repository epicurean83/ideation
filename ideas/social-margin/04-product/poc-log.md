# POC 12주 실행 계획 및 개발 로그 (POC Log)

## 1. 12주 마일스톤 및 스프린트 일정

```
[Sprint 1: Week 1~3]  Typo-Card Engine (클라이언트 OCR + 캔버스 렌더러 + SNS 내보내기)
        ↓
[Sprint 2: Week 4~7]  Social Margin Core (Supabase DB + 문장별 주석 CRUD + 딥링크)
        ↓
[Sprint 3: Week 8~10] Book Discovery & Vibe (알라딘 API + 무드 태그 필터링 + Edge KV)
        ↓
[Sprint 4: Week 11~12] Silent Room + PWA + 얼리어답터 100명 비공개 베타 론칭 & 실측 시작
```

### 주차별 상세 개발 계획

| 주차 | 스프린트 | 주요 구현 내용 | 검증 체크포인트 |
|:---:|---|---|---|
| **W1** | **Sprint 1** | Next.js 14 + Tailwind CSS 프로젝트 셋업, Canvas 기반 텍스트 카드 렌더러 구현 | 고화질 PNG 렌더링 1초 이내 완료 여부 |
| **W2** | **Sprint 1** | Tesseract.js 온디바이스 OCR 연동, 이미지 크롭 및 텍스트 자동 추출 | 모바일 브라우저 OCR 정확도 85% 이상 |
| **W3** | **Sprint 1** | 템플릿 3종(미니멀, 종이 질감, 다크), 스레드/인스타 스토리 비율 토글, 클립보드 복사/다운로드 | **Sprint 1 완료: 카드 생성기 웹 배포** |
| **W4** | **Sprint 2** | Supabase Auth(카카오/구글), PostgreSQL 스키마 설계 (`books`, `quotes`, `margins`) | 소셜 로그인 및 세션 유지 정상 확인 |
| **W5** | **Sprint 2** | 문장 등록 및 특정 문장 상세 페이지(`/quote/[id]`) 구현, Dynamic OG 태그 생성 | SNS 공유 시 오픈그래프 카드 정상 노출 |
| **W6** | **Sprint 2** | 소셜 마진(포스트잇 주석) 작성/조회/삭제 및 공감(좋아요) 토글 인터랙션 | 실시간 주석 카운트 갱신 |
| **W7** | **Sprint 2** | 딥링크 라우팅 (`socialmargin.app/q/123` $\rightarrow$ 해당 문장 마진 노트 포커싱) | **Sprint 2 완료: 소셜 마진 코어 완성** |
| **W8** | **Sprint 3** | Cloudflare Workers 기반 알라딘 Open API 프록시 및 Edge KV 캐싱 레이어 구축 | 도서 검색 응답속도 150ms 이내 |
| **W9** | **Sprint 3** | 무드(Vibe) 태그 시스템 구현 및 태그별 문장 모아보기 피드 | 감정 태그 클릭 시 즉시 필터링 |
| **W10**| **Sprint 3** | 도서 구매 제휴 링크(알라딘 어필리에이트) 파라미터 자동 삽입 | **Sprint 3 완료: 도서 탐색 완성** |
| **W11**| **Sprint 4** | 뽀모도로 무음 독서 타이머(25분/5분) 및 현재 독서 중인 유저 수 Realtime 표시 | 타이머 백그라운드 동작 안정성 |
| **W12**| **Sprint 4** | PWA 매니페스트 설정, 모더레이션 자동 규칙 적용, 스레드 독서계 100명 베타 초대 | **Sprint 4 완료: 실측 데이터 수집 개시** |

---

## 2. 개발 진행 로그 (주간 기록용)

* `[2026-09-21]`: S3 POC 기획 수립 완료, Week 1 Typo-Card Engine 개발 착수 준비.
