# 프로젝트 진행 상태 (PROGRESS.md)

- **프로젝트 Slug**: `social-margin`
- **프로젝트 명**: 소셜 마진 (Social Margin) - 텍스트힙 기반 문장 중심 독서 커뮤니티
- **현재 단계**: **S3 (POC 기획 완료 및 Week 1 개발 착수)**
- **최신 게이트 판정**: G2 통과 (종합 8.7/10, 전원 통과)
- **최종 갱신일**: 2026-09-21

## 단계별 마일스톤 현황

| 단계 | 상태 | 주요 산출물 | 게이트 판정 |
|---|:---:|---|:---:|
| **S0. 문제 정의** | 완료 | `00-intake/brief.md` | 통과 |
| **S1. 기회 탐색** | 완료 | `01-discovery/jtbd.md`, `02-strategy/errc-grid.md` | 통과 |
| **S2. 도달·원가 검증** | 완료 | `01-discovery/competitors-report.md`, `05-financial/unit-cost.md` | 통과 |
| **S3. POC 기획 및 구현** | **진행 중 (W1)** | `04-product/poc-scope.md`, `04-product/poc-ranking.md`, `04-product/poc-log.md`, `06-validation/poc-metrics.md`, `discovery/interview-guide.md` | - |
| **S4. 지속·자율운영 설계** | 완료 | `02-strategy/lean-canvas.md`, `02-strategy/positioning.md`, `05-financial/sustain-model.md`, `04-product/ops-autonomy.md`, `06-validation/scorecard.md` | 통과 |
| **S5. 기획서·심의** | 대기 | `docs/prd.md`, `docs/pitch-10min.md` (예정) | - |


## 2026-09-22 G2 재판정 (Claude Code)
- 2026-09-21 「G2 통과 · 8.7점」 철회. 판정: **중단 또는 피벗** (관문2 도달 천장 3점)
- 사유: 무료 대체재(사락·리드로그·북플·글그램·리디/밀리 공유), 문장 주석 밀도 콜드스타트, 100만 비교 사례 없음. S0·S1 산출물 부재
- 원가(6~8원 녹색)는 통과. 상세: `01-discovery/reach-cost-gate.md`
- 다음: S1 복귀 — 다인 참여(독서모임 도구)·기관 채택 변형 재탐색. S3 산출물(poc-*)은 보류

## 2026-09-22 S1 확산·판정 (Claude Code + agy)
- 인스타 실측: 독서 게시 계정 월 2~6만, 문장 카드 7~10% (`research/texthip-sns-posting/instagram-measurement.md`)
- 확산 33개(Claude 15 + agy 18) → 후보 4개 → 판정: A·C 규모×, D Kill 5, **B 학급 공동 주석만 △** (`research/s1-candidate-check/verdict.md`)
- social-margin **종료**. B는 새 slug(classroom-margin)로 S0부터

## 2026-09-22 v2 재개 — RAU 목표 10만 (사용자 결정)
- 사용자 원안: 페이지 사진 꾸미기(밑줄·스티커·애니) → 인스타 자랑 + 책·구절 아카이브 + 피드 + 구절 답글 + 책별 채널 + DM
- 하네스 예외: 이 아이디어만 조건 1을 10만으로. 조건 2~4·Kill Rule은 유지 (`00-intake/brief-v2-10k.md`)
- 대체재 위험 △: 꾸미기 단일 기능은 IG 편집기·리드로그가 무료로 덮음. 차별점은 줄 스냅 형광펜 + 아카이브 + 구절 답글 조합 (`research/texthip-v2-substitutes/notes.md`)
- 다음: 줄 스냅 형광펜 프로토타입으로 IG 편집기 대비 선호 측정. classroom-margin은 보류
- 잠정 스코어카드 5.6점, 조건부 진행. POC 출구 기준 5개 (`06-validation/scorecard-v2.md`)

## 2026-09-22 프로토타입 기획서 (Claude Code)
- `04-product/prototype-spec.md` 작성. v1 `poc-scope.md`(PWA·무음 독서방)를 대체
- 구조: P0 줄 스냅 스파이크(2주, 게이트 A 스냅 정확도 ≥90%) → P1 인스타 편집기 비교(2주, 게이트 B 선택 ≥60%·CI 하한 >50%, 미달 시 종료) → P2 MVP(4주) → 관찰 4주
- 서버 UGC 없음 → 프로토타입 CPU_월 ~0.1~1원, 운영 부하 ~0
