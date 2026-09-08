# 신사업 발굴 · 기획 하네스

이 저장소는 신사업 아이디어를 **발굴 → 검증 → 기획서 → 심의**까지 끌고 가는 작업 공간이다.
`.claude/skills/`에 설치된 20개 스킬을 아래 프로세스 순서대로 조합해 쓴다.
스킬은 도구이고, 이 문서가 운영 규칙이다. 충돌하면 이 문서가 우선한다.

## 운영 원칙

- **출력 언어는 한국어.** 스킬 본문이 영어여도 산출물·대화는 한국어로 쓴다. 고유명사, 프레임워크 이름, 코드 식별자는 원문 유지.
- **증거 없는 주장은 쓰지 않는다.** 모든 수치에 출처·날짜·신뢰도(High/Medium/Low)를 붙인다. 웹 검색이 막히면 `[Knowledge-Based — 검증 필요]` 표시를 달고 신뢰도를 한 단계 낮춘다.
- **게이트는 정직하게.** 각 단계 끝의 Go/No-Go는 사용자가 듣고 싶은 답이 아니라 근거가 지지하는 답을 낸다. 스킬의 Radical Honesty Protocol을 그대로 적용한다.
- **한 아이디어 = 한 디렉터리.** 산출물은 전부 `ideas/<slug>/` 아래에 쌓는다. 채팅에만 남기고 끝내지 않는다.
- **비싼 스킬은 명시 호출만.** `crucible` Decision 모드, `startup-design` Full 모드, 딥 리서치 웨이브는 사용자가 지시했을 때만 돌린다.
- **superpowers 플러그인은 이 프로젝트에서 비활성.** 브레인스토밍은 `startup-design` Phase 2와 `blue-ocean-strategy`가 대신한다.

## 디렉터리 규약

```
ideas/
  PIPELINE.md                 # 전체 아이디어 목록과 현재 단계 (포트폴리오 보드)
  <slug>/                     # kebab-case, 예: ai-care-robot
    PROGRESS.md               # startup-design이 만드는 체크포인트. 세션 재개 기준점
    00-intake/                # 브리프, 프리플라이트, 브레인스톰, 인터뷰 원문
    01-discovery/             # 시장·경쟁·고객 리서치 (raw/ 포함)
    02-strategy/              # 린 캔버스, 포지셔닝, ERRC 그리드
    03-brand/ 04-product/     # Full 모드에서만
    05-financial/             # 수익 모델, 3년 추정
    06-validation/            # 스코어카드, 실험 설계
    discovery/                # product-discovery 산출물 (brief, interview-guide, synthesis, one-pager)
    crucible/                 # crucible 토론 전문 (YYYY-MM-DD-<slug>.md)
    docs/                     # 기획서(PRD/RFC), 피치 스크립트, 심의 자료
```

스킬별 경로 오버라이드:

- `startup-design`, `startup-competitors`, `startup-positioning`, `startup-pitch`의 `{project-name}/`은 항상 `ideas/<slug>/`다. 저장소 루트에 프로젝트 디렉터리를 만들지 않는다.
- `product-discovery`, `interview-snapshot`의 `discovery/{name}/`은 `ideas/<slug>/discovery/`다.
- `crucible` 전문은 `~/Documents/...`가 아니라 `ideas/<slug>/crucible/`에 쓴다. 중복 판정용 glob도 그 경로를 본다.
- `market-sizing`, `synthesize-interviews`가 참조하는 `context/*.md`는 없다. 대신 `ideas/<slug>/00-intake/brief.md`와 `01-discovery/*.md`를 읽는다.
- `lenny-podcast`는 트랜스크립트 아카이브가 없으므로 framework-only 모드로 답한다. 인용을 만들어내지 않는다.

## 프로세스: 6단계 + 5게이트

```
S0 문제 정의 ─G0─▶ S1 기회 탐색 ─G1─▶ S2 시장 검증 ─G2─▶ S3 고객 검증 ─G3─▶ S4 전략·모델 ─G4─▶ S5 기획서·심의
```

원칙은 **싸고 빠른 검증을 먼저, 비싼 리서치는 나중에**다. 앞 단계에서 죽일 수 있는 아이디어를 뒤 단계까지 끌고 가지 않는다.
각 단계는 아래 표의 스킬을 순서대로 쓴다. 표에 없는 스킬을 끼워 넣어도 되지만, 표에 있는 필수 스킬은 건너뛰지 않는다.

### S0. 문제 정의 (반나절)

목적: "무엇을 풀려는가"를 MECE하게 적고, 즉시 탈락 사유가 없는지 본다.

| 순서 | 스킬 | 용도 | 산출물 |
|---|---|---|---|
| 1 | `issue-tree` (Why/What) | 막연한 기회 영역을 원인·구성요소 트리로 분해 | `00-intake/issue-tree.md` |
| 2 | `startup-design` Phase 0.5만 | 지배적 기존 해법, 선례 실패, 규제 즉사 요인 3건 검색 | `00-intake/preflight.md` |
| 3 | `crucible --council` | 5인 페르소나 30초 돌 던지기 | 채팅 (파일 불필요) |

**G0 통과 조건:** 한 문장 문제 정의 + 대상 고객 가설 + 프리플라이트에 빨간불 없음. 빨간불이면 `PIPELINE.md`에 사유를 적고 종료.

### S1. 기회 탐색 (1일)

목적: 첫 아이디어에 성급히 수렴하지 않고 변형을 넓게 본 뒤, 검증할 하나를 고른다.

| 순서 | 스킬 | 용도 | 산출물 |
|---|---|---|---|
| 1 | `startup-design` Phase 1~2 (Fast Track) | 인테이크 인터뷰 + 변형 3~8개 발산·수렴 | `00-intake/brief.md`, `brainstorm.md`, `PROGRESS.md` |
| 2 | `blue-ocean-strategy` Six Paths + ERRC | 대체 산업·비고객·보완재에서 미개척 공간 탐색 | `02-strategy/errc-grid.md` |
| 3 | `jobs-to-be-done` | 고객이 "고용"하는 일(기능·감정·사회적)로 문제 재정의 | `01-discovery/jtbd.md` |
| 4 | `prioritize` (Value/Effort 또는 ICE) | 변형 후보 스택랭킹 | `00-intake/variant-ranking.md` |

**G1 통과 조건:** 검증 대상 변형 1개 확정, JTBD 한 문장, 핵심 가정 5개 이내로 목록화. 여기서 `PIPELINE.md`에 아이디어를 등록한다.

### S2. 시장 검증 (2~3일)

목적: 시장이 충분히 크고, 타이밍이 맞고, 이길 틈이 있는지 숫자로 확인한다.

| 순서 | 스킬 | 용도 | 산출물 |
|---|---|---|---|
| 1 | `startup-design` Phase 2.5~3 (Wave 1·2) | 리서치 깊이 결정 후 시장·경쟁 병렬 리서치 | `01-discovery/market-analysis.md`, `competitor-landscape.md`, `industry-trends.md`, `confidence-dashboard.md` |
| 2 | `market-sizing` | TAM/SAM/SOM을 top-down·bottom-up 양쪽으로 계산, 범위 제시 | `01-discovery/market-sizing.md` |
| 3 | `startup-competitors` | 상위 경쟁사 3~5곳 배틀카드, 가격 지형, 기능 매트릭스 | `01-discovery/competitors-report.md`, `pricing-landscape.md` |
| 4 | `market-research` | 리뷰 사이트·뉴스 기반 보완 조사 (필요 시) | `01-discovery/market-research.md` |
| 5 | `startup-design` Phase 3.5a~3.5 | 검증 에이전트 실행 후 Research Gate | `01-discovery/verification-report.md`, `research-gate.md` |

`startup-design`의 Wave 3(고객 목소리)·Wave 4(유통)는 G2를 통과한 뒤 S3·S4에서 필요할 때 실행한다.

**G2 통과 조건:** SOM이 사업 규모 기준을 넘고, 경쟁사 취약점 또는 미충족 세그먼트가 문서로 특정됨, 신뢰도 대시보드에서 핵심 주장의 절반 이상이 Medium 이상. 미달이면 피벗(S1로) 또는 종료.

### S3. 고객 검증 (1~2주, 인터뷰 대기 포함)

목적: 데스크 리서치가 아니라 실제 고객의 과거 행동으로 문제를 확인한다. 이 단계는 스킬만으로 끝나지 않는다. 사람이 인터뷰를 해야 한다.

| 순서 | 스킬 | 용도 | 산출물 |
|---|---|---|---|
| 1 | `product-discovery` (Mode 1) | 문제 가설·리서치 질문·성공 기준 브리프 | `discovery/brief.md` |
| 2 | `mom-test` + `product-discovery` (Mode 2) | 유도 질문 없는 인터뷰 가이드. 과거 행동·구체적 사례·약속(commitment) 질문 중심 | `discovery/interview-guide.md` |
| 3 | 사람이 인터뷰 진행 (최소 5건, 권장 8~12건) | 체크포인트에서 세션 중단. `PROGRESS.md`에 대기 상태 기록 | `00-intake/interviews/interview-N.md` |
| 4 | `interview-snapshot` | 인터뷰 1건당 스냅샷 1개 | `discovery/interviews/YYYY-MM-DD-<name>.md` |
| 5 | `synthesize-interviews` + `product-discovery` (Mode 3) | 스냅샷을 테마·페인포인트·기회 트리로 종합 | `discovery/synthesis.md`, `00-intake/interview-synthesis.md` |
| 6 | `startup-design` Phase 3.7 Interview Gate | 문제 확인율, 행동 신호(돈 냈나, 우회책 만들었나), 가정 감사 | `PROGRESS.md` 갱신 |

**G3 통과 조건:** 인터뷰 대상의 과반이 문제를 자발적으로 언급, 최소 2명이 돈이나 시간을 이미 쓰고 있음, 핵심 가정 중 반증된 것이 있으면 브리프 갱신 완료. 확인율이 낮으면 세그먼트를 바꿔 S3를 반복하거나 종료.

### S4. 전략 · 사업 모델 (2~3일)

목적: 어디에 서고, 무엇을 뺄지, 첫 실험이 무엇인지 정한다.

| 순서 | 스킬 | 용도 | 산출물 |
|---|---|---|---|
| 1 | `startup-positioning` | 경쟁 대안 맵, 카테고리 선택, 포지셔닝 문장 (Dunford + Moore + Onliness Test) | `02-strategy/positioning.md` |
| 2 | `obviously-awesome` | 포지셔닝 캔버스로 팀 워크숍용 재정리 (내부 설득 자료) | `02-strategy/positioning-canvas.md` |
| 3 | `blue-ocean-strategy` Strategy Canvas | 경쟁사 대비 가치 곡선 그리기, ERRC 확정 | `02-strategy/strategy-canvas.md` |
| 4 | `startup-design` Phase 4 + 7 (Stage A) | 린 캔버스, 가정 기반 수익 모델 | `02-strategy/lean-canvas.md`, `05-financial/revenue-model.md` |
| 5 | `lean-startup` | 가정 지도 → 가장 위험한 가정부터 MVP·실험 설계, 혁신 회계 지표 정의 | `06-validation/assumptions.md`, `experiments.md` |
| 6 | `prioritize` (RICE 또는 WSJF) | 실험·MVP 범위 스택랭킹, 스코프 컷 | `06-validation/experiment-ranking.md` |
| 7 | `startup-design` Phase 8 | 7개 차원 스코어카드 + 판정 | `06-validation/scorecard.md` |

**G4 통과 조건:** 스코어카드 6점 이상, 포지셔닝 문장 1개, 3개월 안에 돌릴 수 있는 실험 3개와 각 실험의 성공·실패 기준이 숫자로 적혀 있음. 4~5점이면 조건부(우려 사항 해소 계획 첨부), 3점 이하면 종료.

### S5. 기획서 · 심의 (2~3일)

목적: 의사결정자가 읽고 결정할 수 있는 문서를 만들고, 심의 전에 스스로 가장 강하게 반박한다.

| 순서 | 스킬 | 용도 | 산출물 |
|---|---|---|---|
| 1 | `prd` | 깊이 선택: one-pager(경영진) → brief(사업부) → full PRD/RFC(실행팀). 앞 단계 산출물을 전부 읽고 쓴다 | `docs/one-pager.md`, `docs/prd.md` |
| 2 | `product-discovery` (Mode 4) | 고객 증거 중심 이해관계자 원페이저 (PRD 부록) | `discovery/one-pager.md` |
| 3 | `critique` | 논리 공백, 근거 없는 가정, 빠진 관점 압박 테스트. 지적은 문서에 반영 | `docs/critique-round-N.md` |
| 4 | `crucible` (Decision 모드) | 9~11인 페르소나 토론 후 판정. 사용자 명시 호출 | `crucible/YYYY-MM-DD-<slug>.md` |
| 5 | `startup-pitch` | 10분/5분/2분 스크립트, 예상 Q&A, 채점 루브릭. 투자자 대신 경영진·심의위원 대상으로 톤 조정 | `docs/pitch-10min.md`, `pitch-qa.md` |
| 6 | `critique` 2회차 | 피치 스크립트 대상으로 반복 | `docs/critique-round-N.md` |

**최종 산출물 세트:** `docs/one-pager.md`(1장 요약) + `docs/prd.md`(본문) + `06-validation/scorecard.md`(판정) + `docs/pitch-10min.md`(발표) + `crucible/` 판정문. 이 다섯 개가 갖춰져야 심의에 올린다.

## 빠른 경로 (Fast Track)

"빠른 검증", "일주일 안에", "일단 감만"이라고 하면 아래로 압축한다.

1. S0 전체
2. S1: `startup-design` Fast Track (변형 3개) + `jobs-to-be-done` 한 문장
3. S2: Wave 1·2만, `market-sizing` 생략하고 startup-design의 TAM/SAM/SOM 사용
4. S3: 기존 고객 대화 5건 이상 있으면 문서화만, 없으면 인터뷰 3건 필수
5. S4: 린 캔버스 + 스코어카드 + 실험 3개
6. S5: `prd` one-pager + `critique` 1회

Fast Track으로 통과한 아이디어는 `PROGRESS.md`에 Fast Track임을 남기고, 본 심의 전에 Full로 확장한다.

## 수시 호출 스킬

단계와 무관하게 언제든 쓴다.

- `issue-tree` How 트리: 실행 계획을 짤 때, 여러 액션 중 순서를 정할 때
- `crucible --council`: 새 아이디어가 떠오를 때 30초 sanity check. 파일 안 남김
- `crucible --solo <persona>`: 한 관점만 필요할 때 (Contrarian, First Principles, Operator 등)
- `critique`: 어떤 문서든 남에게 보내기 전
- `lenny-podcast`: PM 실무 관행 질문. framework-only 모드
- `prioritize`: 후보가 3개 이상 쌓이면 즉시

## 세션 운영

- **시작 시:** `ideas/PIPELINE.md`를 읽고, 작업 중인 `<slug>`의 `PROGRESS.md`를 읽는다. 마지막 미완료 단계에서 이어간다. "이전 세션에서 [단계]까지 완료. [다음 단계]부터 진행합니다"라고 알린다.
- **단계 완료 시:** `PROGRESS.md`와 `PIPELINE.md`의 단계 열을 갱신한다. 게이트 판정과 근거를 한 줄로 남긴다.
- **종료·보류 시:** `PIPELINE.md`에 사유를 적는다. 디렉터리는 지우지 않는다. 죽은 아이디어의 리서치는 다음 아이디어의 프리플라이트 자료다.
- **커밋:** 게이트를 하나 넘을 때마다 `ideas/<slug>/`를 커밋한다. 메시지는 `<slug>: G2 통과 — SOM 1,200억, 경쟁사 3곳 취약점 특정` 형식으로 판정과 근거를 담는다.

## PIPELINE.md 형식

```markdown
| slug | 한 줄 문제 정의 | 현재 단계 | 마지막 게이트 | 판정 | 다음 액션 | 갱신일 |
|---|---|---|---|---|---|---|
| ai-care-robot | 독거노인 낙상 감지 | S3 | G2 | 통과 (조건부) | 인터뷰 8건 진행 중 | 2026-09-08 |
```

## 하지 말 것

- 리서치 없이 시장 규모 숫자를 쓰는 것
- 인터뷰 없이 G3를 통과시키는 것. 데스크 리서치의 "고객 목소리"는 인터뷰 대체가 아니다
- 스코어카드 없이 기획서를 쓰는 것
- 게이트 판정을 사용자가 원하는 쪽으로 기울이는 것
- 저장소 루트나 홈 디렉터리에 산출물을 만드는 것
