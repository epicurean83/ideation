# 신사업 발굴 · 기획 하네스

이 저장소는 신사업 아이디어를 **발굴 → 검증 → 기획서 → 실증 → 심의**까지 끌고 가는 작업 공간이다.
`.claude/skills/`에 설치된 20개 스킬을 아래 프로세스 순서대로 조합해 쓴다.
스킬은 도구이고, 이 문서가 운영 규칙이다. 충돌하면 이 문서가 우선한다.

## 운영 원칙

- **출력 언어는 한국어.** 스킬 본문이 영어여도 산출물·대화는 한국어로 쓴다. 고유명사, 프레임워크 이름, 코드 식별자는 원문 유지.
- **증거 없는 주장은 쓰지 않는다.** 모든 수치에 출처·날짜·신뢰도(High/Medium/Low)를 붙인다. 웹 검색이 막히면 `[Knowledge-Based — 검증 필요]` 표시를 달고 신뢰도를 한 단계 낮춘다.
- **게이트는 정직하게.** 각 단계 끝의 Go/No-Go는 사용자가 듣고 싶은 답이 아니라 근거가 지지하는 답을 낸다. 스킬의 Radical Honesty Protocol을 그대로 적용한다.
- **한 아이디어 = 한 디렉터리.** 산출물은 전부 `ideas/<slug>/` 아래에 쌓는다. 채팅에만 남기고 끝내지 않는다.
- **비싼 스킬은 주간엔 명시 호출만, 야간 루프에선 자동.** `crucible` Decision 모드, `startup-design` Full 모드, 딥 리서치 웨이브, `deepdive` deep은 사용자가 근무하는 시간(09:00~22:00 KST)에는 사용자가 지시했을 때만 돌린다. 야간 자동 루프(`harness/nightshift`) 안에서는 사전 승인된 것으로 보고 필요할 때 돌린다. 22:00 이후라도 **대화형 세션**에서는 여전히 사용자가 지시했을 때만 돌린다. 자동 실행은 루프만 한다. 자세한 시간·한도 규칙은 「야간 자동 루프」 절.
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
    03-brand/ 04-product/     # Full 모드에서만. 단 04-product/prototype.md는 S5 실증에서 만든다
    05-financial/             # 수익 모델, 3년 추정
    06-validation/            # 스코어카드, 실험 설계
    discovery/                # product-discovery 산출물 (brief, interview-guide, synthesis, one-pager)
    research/<topic-slug>/    # deepdive 실행 1건당 폴더 1개 (plan.md, sources/, claims.csv, memo.md, 보고서)
    papers/                   # paper-lookup 검색 로그와 초록·전문 (query-log.md, <id>.md)
    crucible/                 # crucible 토론 전문 (YYYY-MM-DD-<slug>.md)
    docs/                     # 기획서(PRD/RFC), 피치 스크립트, 심의 자료, references.bib
```

스킬별 경로 오버라이드:

- `startup-design`, `startup-competitors`, `startup-positioning`, `startup-pitch`의 `{project-name}/`은 항상 `ideas/<slug>/`다. 저장소 루트에 프로젝트 디렉터리를 만들지 않는다.
- `product-discovery`, `interview-snapshot`의 `discovery/{name}/`은 `ideas/<slug>/discovery/`다.
- `crucible` 전문은 `~/Documents/...`가 아니라 `ideas/<slug>/crucible/`에 쓴다. 중복 판정용 glob도 그 경로를 본다.
- `market-sizing`, `synthesize-interviews`가 참조하는 `context/*.md`는 없다. 대신 `ideas/<slug>/00-intake/brief.md`와 `01-discovery/*.md`를 읽는다.
- `lenny-podcast`는 트랜스크립트 아카이브가 없으므로 framework-only 모드로 답한다. 인용을 만들어내지 않는다.
- `deepdive`의 research 폴더는 `ideas/<slug>/research/`다. 스킬이 `research/`·`docs/research/`·`~/deepdive/`를 후보로 고르지만 이 프로젝트에서는 항상 이 경로다. 교차 실행 위키(`~/.claude/research/wiki/`)와 applications ledger는 홈 디렉터리에 두는 스킬 기본값을 따른다.
- `paper-lookup` 결과는 `ideas/<slug>/papers/`에 남긴다. 검색마다 `query-log.md`에 데이터베이스, 엔드포인트, 파라미터, 조회일, 건수를 적어 재현 가능하게 한다.
- `citation-management`의 BibTeX는 `ideas/<slug>/docs/references.bib` 하나로 모은다.

## 리서치 스킬 라우팅

조사 요청이 들어오면 먼저 **어떤 질문인가**로 스킬을 고른다. 세 스킬은 역할이 겹치지 않는다.

| 질문 유형 | 스킬 | 예 |
|---|---|---|
| 시장·업계·경쟁 구조를 **넓게** 훑는다 | `startup-design` Wave 1·2, `startup-competitors` | "이 시장 규모와 주요 플레이어는?" |
| **하나의 결정**에 답하기 위한 데스크 리서치 | `deepdive` | "B2B로 갈까 B2C로 갈까", "X 기술은 실제로 어떻게 동작하나", "이 가설이 맞나" |
| 논문·학술 근거·기술 타당성 | `paper-lookup` | "이 방식의 정확도를 검증한 연구가 있나", "이 DOI 전문 가져와" |
| 인용 정리·검증·서지 | `citation-management` | "PRD 참고문헌을 BibTeX로", "이 인용 정보가 맞나" |

**deepdive 사용 규칙**

- 명시 호출만: `/deepdive <질문>`. description이 러시아어라 자연어 트리거는 기대하지 않는다. 대화·산출물은 한국어로 쓴다.
- 깊이는 게이트의 무게에 맞춘다. **shallow**(5~7 소스, 15분): S0·S1의 탐색 질문, "X가 뭔가". **medium**(12~18 소스, 1시간): S2·S3의 가설 검증, 게이트 근거. **deep**(25~35 소스, 3시간): G3 판정이나 S4 심의 준비처럼 틀리면 비싼 결정. deep은 Plan-review gate에서 사용자의 명시적 "OK"를 기다린다. 야간 루프에서는 사용자 대신 독립 서브에이전트가 plan을 검토한다(「야간 자동 루프」 절). 이 문서가 스킬 규칙보다 우선한다.
- deepdive는 Decision Spec에 **if-then 포크**가 하나 이상 있어야 medium 이상으로 돈다. 포크가 안 나오면 이 질문은 결정과 무관하다는 뜻이니 shallow로 낮추거나 `issue-tree`로 질문부터 다시 세운다.
- 같은 질문을 `startup-design` 리서치 웨이브와 `deepdive` 양쪽에 돌리지 않는다. 웨이브가 지형을 그리고, deepdive는 그 지형 위의 특정 갈림길에 답한다.
- Phase 6.9 보고서 내보내기(HTML/PDF/DOCX)는 pandoc·mmdc가 없어 실패한다. 마크다운 보고서와 `memo.md`가 산출물이다. `finish.py`가 6.9 때문에만 빨간불이면 그 사실을 적고 진행한다. 다른 phase 빨간불은 스킬 규칙대로 되돌아가 채운다.
- deepdive `memo.md`의 권고와 포크 결과는 해당 게이트 판정 문서(`research-gate.md`, `scorecard.md`)에 `[research/<topic-slug>]`로 인용한다.

**paper-lookup 사용 규칙**

- 기술 기반 아이디어에서 "이게 되긴 하나"를 물을 때 쓴다. 벤더 자료나 블로그가 아니라 peer-reviewed 근거가 필요한 주장이 대상이다.
- 결과에는 어떤 DB에 어떤 질의를 던졌는지 provenance를 남긴다. 한 DB가 비어 있으면 "없다"가 아니라 "여기엔 색인 안 됨"이라고 쓴다.
- 1,000건·50콜을 넘길 검색은 사용자에게 먼저 묻는다.
- API 키는 전부 선택이다. 없으면 낮은 rate limit으로 진행하고, 어떤 키가 도움이 되는지 한 줄만 알린다. `.env`가 있어도 지정된 4개 변수 외에는 읽지 않는다.

**citation-management 사용 규칙**

- S4에서 `docs/prd.md`와 `docs/one-pager.md`에 인용된 논문·보고서를 `references.bib`로 모으고 `validate_citations.py`로 검증한 뒤 심의에 올린다.
- Google Scholar 스크립트는 `scholarly` 미설치로 쓰지 않는다. OpenAlex와 PubMed로 대체한다.

## 프로세스: 6단계 + 6게이트

```
S0 문제 정의 ─G0─▶ S1 기회 탐색 ─G1─▶ S2 시장 검증 ─G2─▶ S3 전략·모델 ─G3─▶ S4 기획서·심의 ─G4─▶ ┃ S5 실증 ─G5─▶ 본 심의
                                                                                           ┃
                                                  여기까지 자동 (야간 루프 가능) ─────────────────┛ 여기부터 사람 (프로토타입·인터뷰)
```

원칙은 **싸고 빠른 검증을 먼저, 비싼 리서치는 나중에, 사람이 직접 해야 하는 실증은 맨 마지막에**다. 앞 단계에서 죽일 수 있는 아이디어를 뒤 단계까지 끌고 가지 않는다.
각 단계는 아래 표의 스킬을 순서대로 쓴다. 표에 없는 스킬을 끼워 넣어도 되지만, 표에 있는 필수 스킬은 건너뛰지 않는다.

### 실증은 맨 마지막 (사람 단계 분리 규칙)

아이템을 먼저 확립하고 **프로토타입을 만든 뒤** 그것을 들고 고객 인터뷰를 한다. 사람이 직접 해야 하는 일(인터뷰, 사용자 리포트 수집, 현장 관찰, 사전 판매)은 전부 S5로 모은다.

- **S0~S4는 인터뷰 없이 끝까지 진행한다.** 인터뷰가 없다는 이유로 단계를 멈추거나, 감점하거나, 보류하지 않는다. `startup-design` Phase 3.7은 "Defer and continue"를 고른 것으로 처리한다.
- **데스크로 못 푸는 질문은 장부에 쌓는다.** `PROGRESS.md`의 「인터뷰 대기 질문」에 질문과 *왜 데스크로 못 푸는지* 한 줄을 적는다. S5 인터뷰 가이드의 원재료다.
- **실증 부재로 인한 보류·조건부는 통과로 본다.** 판정 사유가 "고객 확인 필요", "인터뷰로 검증해야 함"뿐이면 그 게이트는 통과다. 실증과 무관한 사유(시장 크기, 경쟁, 수익성, 실행 가능성)의 조건부·보류는 그대로 조건부·보류다. 사유를 섞어 쓰지 말고 둘을 분리해 적는다.
- **G4를 통과한 아이템의 판정은 `통과(실증 대기)`다.** 이것이 자동 루프의 "완성" 기준이다. G5를 통과하기 전까지 본 심의에 올리지 않는다.

### S0. 문제 정의 (반나절)

목적: "무엇을 풀려는가"를 MECE하게 적고, 즉시 탈락 사유가 없는지 본다.

| 순서 | 스킬 | 용도 | 산출물 |
|---|---|---|---|
| 1 | `issue-tree` (Why/What) | 막연한 기회 영역을 원인·구성요소 트리로 분해 | `00-intake/issue-tree.md` |
| 2 | `startup-design` Phase 0.5만 | 지배적 기존 해법, 선례 실패, 규제 즉사 요인 3건 검색 | `00-intake/preflight.md` |
| 3 | `deepdive` shallow (선택) | 도메인이 낯설 때 "X는 어떻게 돌아가나" 한 번. 트리에서 모르는 가지가 있을 때만 | `research/<topic>/memo.md` |
| 4 | `crucible --council` | 5인 페르소나 30초 돌 던지기 | 채팅 (파일 불필요) |

**PIPELINE 등록:** S0를 시작할 때 `PIPELINE.md`에 행을 추가한다(현재 단계 `S0`, 판정 `진행 중`). 게이트를 넘을 때마다 같은 행을 갱신한다. 등록되지 않은 아이디어는 이어받을 수 없다.

**G0 통과 조건:** 한 문장 문제 정의 + 대상 고객 가설 + 프리플라이트에 빨간불 없음. 빨간불이면 `PIPELINE.md`에 사유를 적고 종료.

### S1. 기회 탐색 (1일)

목적: 첫 아이디어에 성급히 수렴하지 않고 변형을 넓게 본 뒤, 검증할 하나를 고른다.

| 순서 | 스킬 | 용도 | 산출물 |
|---|---|---|---|
| 1 | `startup-design` Phase 1~2 (Fast Track) | 인테이크 인터뷰 + 변형 3~8개 발산·수렴 | `00-intake/brief.md`, `brainstorm.md`, `PROGRESS.md` |
| 2 | `blue-ocean-strategy` Six Paths + ERRC | 대체 산업·비고객·보완재에서 미개척 공간 탐색 | `02-strategy/errc-grid.md` |
| 3 | `jobs-to-be-done` | 고객이 "고용"하는 일(기능·감정·사회적)로 문제 재정의 | `01-discovery/jtbd.md` |
| 4 | `prioritize` (Value/Effort 또는 ICE) | 변형 후보 스택랭킹 | `00-intake/variant-ranking.md` |

**G1 통과 조건:** 검증 대상 변형 1개 확정, JTBD 한 문장, 핵심 가정 5개 이내로 목록화. `PIPELINE.md` 행의 한 줄 문제 정의를 확정한 변형 기준으로 고친다.

### S2. 시장 검증 (2~3일)

목적: 시장이 충분히 크고, 타이밍이 맞고, 이길 틈이 있는지 숫자로 확인한다.

| 순서 | 스킬 | 용도 | 산출물 |
|---|---|---|---|
| 1 | `startup-design` Phase 2.5~3 (Wave 1·2) | 리서치 깊이 결정 후 시장·경쟁 병렬 리서치 | `01-discovery/market-analysis.md`, `competitor-landscape.md`, `industry-trends.md`, `confidence-dashboard.md` |
| 2 | `market-sizing` | TAM/SAM/SOM을 top-down·bottom-up 양쪽으로 계산, 범위 제시 | `01-discovery/market-sizing.md` |
| 3 | `startup-competitors` | 상위 경쟁사 3~5곳 배틀카드, 가격 지형, 기능 매트릭스 | `01-discovery/competitors-report.md`, `pricing-landscape.md` |
| 4 | `market-research` | 리뷰 사이트·뉴스 기반 보완 조사 (필요 시) | `01-discovery/market-research.md` |
| 5 | `deepdive` medium | 웨이브가 끝난 뒤 남은 **핵심 가정 1~2개**만 골라 결정 포크로 검증. 예: "규제가 2년 내 완화되나", "기존 유통망이 우리 제품을 받나" | `research/<topic>/` |
| 6 | `paper-lookup` (기술 아이디어만) | 핵심 기술의 성능·안전성·한계를 peer-reviewed 근거로 확인 | `papers/query-log.md`, `01-discovery/tech-feasibility.md` |
| 7 | `startup-design` Phase 3.5a~3.5 | 검증 에이전트 실행 후 Research Gate. deepdive `memo.md`와 기술 타당성을 판정 근거에 포함 | `01-discovery/verification-report.md`, `research-gate.md` |

`startup-design`의 Wave 3(고객 목소리, 데스크 리서치)·Wave 4(유통)는 G2를 통과한 뒤 S3에서 필요할 때 실행한다. Wave 3는 인터뷰의 대체가 아니라 「인터뷰 대기 질문」을 뽑는 재료다.

**G2 통과 조건:** SOM이 사업 규모 기준을 넘고, 경쟁사 취약점 또는 미충족 세그먼트가 문서로 특정됨, 신뢰도 대시보드에서 핵심 주장의 절반 이상이 Medium 이상. 미달이면 피벗(S1로) 또는 종료.

### S3. 전략 · 사업 모델 (2~3일)

목적: 어디에 서고, 무엇을 뺄지, 첫 실험이 무엇인지 정한다.

| 순서 | 스킬 | 용도 | 산출물 |
|---|---|---|---|
| 1 | `startup-positioning` | 경쟁 대안 맵, 카테고리 선택, 포지셔닝 문장 (Dunford + Moore + Onliness Test) | `02-strategy/positioning.md` |
| 2 | `obviously-awesome` | 포지셔닝 캔버스로 팀 워크숍용 재정리 (내부 설득 자료) | `02-strategy/positioning-canvas.md` |
| 3 | `blue-ocean-strategy` Strategy Canvas | 경쟁사 대비 가치 곡선 그리기, ERRC 확정 | `02-strategy/strategy-canvas.md` |
| 4 | `startup-design` Phase 4 + 7 (Stage A) | 린 캔버스, 가정 기반 수익 모델 | `02-strategy/lean-canvas.md`, `05-financial/revenue-model.md` |
| 5 | `lean-startup` | 가정 지도 → 가장 위험한 가정부터 MVP·실험 설계, 혁신 회계 지표 정의. 프로토타입 인터뷰는 실험 #1로 둔다 | `06-validation/assumptions.md`, `experiments.md` |
| 6 | `prioritize` (RICE 또는 WSJF) | 실험·MVP 범위 스택랭킹, 스코프 컷 | `06-validation/experiment-ranking.md` |
| 7 | `deepdive` deep (조건부) | 스코어카드가 6~7점 경계이거나, 사업 모델 선택지가 둘로 갈릴 때. 포크 결과가 곧 G3 판정 근거. 주간에는 사용자 OK 후 실행, 야간 루프에서는 독립 서브에이전트의 plan 검토 후 실행 | `research/<topic>/memo.md`, `application.md` |
| 8 | `startup-design` Phase 8 | 7개 차원 스코어카드 + 판정. **인터뷰 부재를 감점 사유로 쓰지 않는다.** Problem severity는 데스크 증거(리뷰·민원·지출 흔적)로 채점한다 | `06-validation/scorecard.md` |

**G3 통과 조건:** 스코어카드 6점 이상, 포지셔닝 문장 1개, 3개월 안에 돌릴 수 있는 실험 3개와 각 실험의 성공·실패 기준이 숫자로 적혀 있음. 4~5점이면 조건부(우려 사항 해소 계획 첨부), 3점 이하면 종료. 조건부 사유가 실증 부재뿐이면 통과로 본다. `startup-design` 스코어카드의 자체 라벨(6~7점 conditional)은 문서에 그대로 적되, G3 판정은 이 문서의 기준(6점 이상 통과)을 따른다.

### S4. 기획서 · 심의 준비 (2~3일)

목적: 의사결정자가 읽고 결정할 수 있는 문서를 만들고, 스스로 가장 강하게 반박한다. 고객 증거가 들어갈 자리는 비워 두고 「실증 대기」로 표시한다.

| 순서 | 스킬 | 용도 | 산출물 |
|---|---|---|---|
| 1 | `prd` | 깊이 선택: one-pager(경영진) → brief(사업부) → full PRD/RFC(실행팀). 앞 단계 산출물을 전부 읽고 쓴다 | `docs/one-pager.md`, `docs/prd.md` |
| 2 | `critique` | 논리 공백, 근거 없는 가정, 빠진 관점 압박 테스트. 지적은 문서에 반영 | `docs/critique-round-N.md` |
| 3 | `crucible` (Decision 모드) | 9~11인 페르소나 토론 후 판정. 주간에는 사용자 명시 호출, 야간 루프에서는 자동 실행 | `crucible/YYYY-MM-DD-<slug>.md` |
| 4 | `citation-management` | PRD·원페이저에 인용된 논문·보고서를 `references.bib`로 모으고 DOI·메타데이터 검증. 깨진 인용은 심의에서 신뢰를 깎는다 | `docs/references.bib`, `docs/citation-report.json` |
| 5 | `startup-pitch` | 10분/5분/2분 스크립트, 예상 Q&A, 채점 루브릭. 투자자 대신 경영진·심의위원 대상으로 톤 조정 | `docs/pitch-10min.md`, `pitch-qa.md` |
| 6 | `critique` 2회차 | 피치 스크립트 대상으로 반복 | `docs/critique-round-N.md` |

**G4 통과 조건:** 아래 산출물 세트가 갖춰지고, `crucible` 판정이 종료·피벗이 아니며, `PROGRESS.md`의 「인터뷰 대기 질문」이 3개 이상 정리됨. 통과하면 `PIPELINE.md` 판정을 `통과(실증 대기)`로 적는다.

**산출물 세트:** `docs/one-pager.md`(1장 요약) + `docs/prd.md`(본문) + `06-validation/scorecard.md`(판정) + `docs/pitch-10min.md`(발표) + `crucible/` 판정문 + `docs/references.bib`(검증된 서지).

### S5. 실증 — 프로토타입 · 고객 인터뷰 (사람 단계, 1~3주)

목적: `통과(실증 대기)` 아이템 중 사용자가 고른 것을 프로토타입으로 만들고, 그 물건을 들고 실제 고객의 과거 행동으로 문제를 확인한다. **자동 루프는 이 단계를 실행하지 않는다.** 착수는 사용자가 아이템을 지목했을 때만 한다.

| 순서 | 스킬 | 용도 | 산출물 |
|---|---|---|---|
| 1 | (사람 + Claude) 프로토타입 제작 | S3 `experiments.md`의 실험 #1을 돌릴 수 있는 최소 물건 | `04-product/prototype.md` (링크·범위·한계) |
| 2 | `product-discovery` (Mode 1) | 「인터뷰 대기 질문」 장부를 문제 가설·리서치 질문·성공 기준 브리프로 | `discovery/brief.md` |
| 3 | `mom-test` + `product-discovery` (Mode 2) | 유도 질문 없는 인터뷰 가이드. 과거 행동·구체적 사례·약속(commitment) 질문 중심. 프로토타입 시연은 과거 행동 질문 **뒤에** 둔다 | `discovery/interview-guide.md` |
| 4 | 사람이 인터뷰 진행 (최소 5건, 권장 8~12건) | 체크포인트에서 세션 중단. `PROGRESS.md`에 대기 상태 기록 | `00-intake/interviews/interview-N.md` |
| 5 | `interview-snapshot` | 인터뷰 1건당 스냅샷 1개 | `discovery/interviews/YYYY-MM-DD-<name>.md` |
| 6 | `synthesize-interviews` + `product-discovery` (Mode 3) | 스냅샷을 테마·페인포인트·기회 트리로 종합 | `discovery/synthesis.md`, `00-intake/interview-synthesis.md` |
| 7 | `startup-design` Phase 3.7 Interview Gate | 문제 확인율, 행동 신호(돈 냈나, 우회책 만들었나), 가정 감사 | `PROGRESS.md` 갱신 |
| 8 | `product-discovery` (Mode 4) | 고객 증거 중심 이해관계자 원페이저 (PRD 부록). 스코어카드·PRD의 「실증 대기」 칸을 채운다 | `discovery/one-pager.md` |

**G5 통과 조건:** 인터뷰 대상의 과반이 문제를 자발적으로 언급, 최소 2명이 돈이나 시간을 이미 쓰고 있음, 핵심 가정 중 반증된 것이 있으면 브리프·스코어카드·PRD 갱신 완료. 확인율이 낮으면 세그먼트를 바꿔 S5를 반복하거나 종료. 통과하면 본 심의에 올린다.

## 빠른 경로 (Fast Track)

"빠른 검증", "일주일 안에", "일단 감만"이라고 하면 아래로 압축한다.

1. S0 전체
2. S1: `startup-design` Fast Track (변형 3개) + `jobs-to-be-done` 한 문장
3. S2: Wave 1·2만, `market-sizing` 생략하고 startup-design의 TAM/SAM/SOM 사용
4. S3: 린 캔버스 + 스코어카드 + 실험 3개
5. S4: `prd` one-pager + `critique` 1회 → 판정 `통과(Fast Track)`. `통과(실증 대기)`가 아니며 야간 루프의 목표 개수에 들어가지 않는다
6. S5 (사람 단계): 프로토타입 + 인터뷰 3건 이상. 기존 고객 대화 5건 이상 있으면 문서화로 대체 가능

Fast Track으로 통과한 아이디어는 `PROGRESS.md`에 Fast Track임을 남기고, S5·본 심의 전에 Full로 확장해 G4를 다시 받는다. 야간 루프는 Fast Track을 쓰지 않는다.

## 수시 호출 스킬

단계와 무관하게 언제든 쓴다.

- `issue-tree` How 트리: 실행 계획을 짤 때, 여러 액션 중 순서를 정할 때
- `crucible --council`: 새 아이디어가 떠오를 때 30초 sanity check. 파일 안 남김
- `crucible --solo <persona>`: 한 관점만 필요할 때 (Contrarian, First Principles, Operator 등)
- `critique`: 어떤 문서든 남에게 보내기 전
- `lenny-podcast`: PM 실무 관행 질문. framework-only 모드
- `prioritize`: 후보가 3개 이상 쌓이면 즉시
- `/deepdive` shallow: 대화 중 "X가 뭐지", "요즘 X 어떻게 됐지"가 나오면. 15분, 파일은 `research/`에 남김
- `paper-lookup`: 누군가 "연구에 따르면"이라고 말했는데 출처가 없을 때. DOI·PMID 하나면 바로 조회
- `citation-management`: 문서에 인용이 5개 넘게 쌓이면 그때부터 `references.bib`로 관리 시작

## 야간 자동 루프 (`harness/nightshift`)

사용자가 퇴근한 뒤에만 S0~S4를 자동으로 돌려 `통과(실증 대기)` 아이템을 쌓는다. 목표 개수(`nightshift.toml`의 `target_passed`, 기본 10)에 도달하면 멈춘다.

**불변식: 사용자가 09:00에 출근했을 때 5시간 창과 그날 몫의 주간 한도가 루프 때문에 줄어 있으면 안 된다.**

- **시작:** systemd 타이머가 22:00(Asia/Seoul)에 러너를 띄운다. 근무 시간(09:00~22:00)이면 러너는 API를 한 번도 부르지 않고 끝난다. 동시에 두 개가 돌지 않도록 잠금 파일을 쓴다.
- **5시간 창 규칙:** D = 다음 근무 시작 − 5분(08:55).
  - 새 창을 열 수 있는 마지막 시각은 D − 5h = **03:55**다.
  - 이미 열린 창의 종료 시각이 D 이전이면 그 창이 끝나기 5분 전까지 계속한다.
  - 22:00에 시작하면 창 2개(22:00~03:00, 03:00~08:00)를 쓰고 **08:00 전후에 멈춘다.**
  - 창 종료 시각은 2026-09-14 로컬 기록 복원 결과 "시작을 정시로 내림 + 5h"였다. 계산은 내림 없이 시작 + 5h로 잡아 보수적이다.
- **주간 한도 규칙:** 주간 초기화까지 남은 근무일마다 사용자 몫을 예약한다.
  - 사용자 몫은 초기 11%/일이다. 야간 종료~다음 야간 시작 사이 증가분을 실측해 3개 이상 쌓이면 실측값(p75 × 1.2)으로 바꾼다.
  - 남은 몫을 남은 야간 수로 나눈 만큼이 이번 야간 상한이다. 주간 초기화 직전 야간에는 어차피 사라질 잔량을 모두 쓸 수 있다.
  - **새 작업은 상한까지 여유가 작업 1건 예상 비용(초기 1%p, 작업 전후 실측으로 학습) 이상일 때만 시작한다.**
  - 여유가 5% 미만이면 `crucible` Decision·`deepdive` medium·deep을 hook으로 막는다(`deepdive` shallow, `crucible --council`·`--solo`는 허용). 기본 설정에서 평소 야간 여유는 약 2.5%라, **무거운 스킬은 사실상 주간 초기화 직전 야간에 몰려서 돈다.** 막힌 아이디어는 `PROGRESS.md`에 「무거운 스킬 대기」로 적고, 진행 중 개수에서 빼서 새 아이디어로 넘어간다.
  - `ideas/` 아래를 하나도 바꾸지 않은 작업이 2번 연속이면 할 일이 막힌 것으로 보고 그날 밤을 끝낸다.
- **fail-closed:** 주간 사용률 정보가 없거나, 10분 넘게 갱신되지 않았거나, 주간 초기화 시각이 지났으면 probe로 다시 읽는다. 그래도 못 읽으면 멈춘다.
- **감시:** 한도 상태는 Agent SDK `RateLimitEvent`에서 읽는다. 이 이벤트는 세션 시작·상태 변화 때만 오므로, 작업 중에는 **3분마다 Haiku 최소 호출(probe)로 주간 사용률을 새로 읽는다.** 판정은 probe·이벤트·메시지 수신 때와 30초마다 다시 해서, 규칙을 넘으면 interrupt한다. interrupt가 실패하면 세션을 끊는다. 근무일 08:57에는 별도 타이머가 서비스를 강제 종료한다.
  - 초과분은 probe 간격(최대 3분) 동안의 소비와 사용률 해상도(1%)만큼 생길 수 있고, `reserve_safety` 3%가 흡수한다.
- **자기 보호:** 작업 세션은 `bypassPermissions`로 돌지만, 권한 거부 규칙과 PreToolUse hook이 다음을 막는다.
  - `harness/nightshift`·`state`·설정·지시문, `~/.config/systemd` 수정
  - 프로젝트·사용자 `settings*.json`, `harness/.venv`·`uv.lock` 수정
  - 자격증명 읽기, `git push`, `systemctl`
  - 거부 규칙은 세션 전체에, hook은 서브에이전트 도구 호출에도 적용된다(SDK 문서 기준, 서브에이전트 경로는 실측 안 함). 웹 원자료의 프롬프트 인젝션을 완전히 막지는 못한다.
- **긴 스킬:** 작업 1건은 최대 90분이다.
  - `deepdive` deep의 Plan-review gate는 사람의 답을 기다리게 되어 있지만, 사용자는 S0~S4를 사람 없이 돌리기로 했다(2026-09-14). 그래서 야간에는 사용자 대신 **독립 서브에이전트**가 plan을 검토한다. 검토 기준은 포크가 결정에 연결되는지, 소스 계획이 한쪽으로 치우치지 않았는지다. 검토 결과는 `research/<topic>/plan-review.md`에 남기고 진행한다. 최종 `memo.md` 머리에 「plan 검토: 서브에이전트(사람 아님)」를 적어 나중에 읽는 사람이 사람 검토로 오해하지 않게 한다.
  - deep이 한 작업(90분)에 끝나지 않으면 다음 작업이 기존 `research/<topic>/`에서 이어간다. 새로 시작하지 않는다.
  - `deepdive` medium도 기존 `research/<topic>/`가 있으면 새로 시작하지 않고 이어간다.
  - `crucible` Decision의 intake 확인은 야간에는 intake를 판정문 파일 머리에 적는 것으로 대신한다.
- **확인:** `uv run --project harness python -m nightshift plan`은 API 호출 없이 오늘 밤 시간표와 주간 상한을 보여 준다. 실행 기록은 `harness/state/`(git 제외)에 있다.
- **설치:** `harness/install-systemd.sh --enable` / `--disable`.
- **작업 1건의 지시문:** `harness/prompts/night-job.md`.
- **구독 인증:** 루프는 claude.ai 구독 로그인으로 돈다. 서비스 유닛은 `ANTHROPIC_API_KEY`를 지운다.
- 사용자가 야간에 직접 Claude를 쓰면 같은 한도를 나눠 쓴다. 러너는 이벤트로 보이는 사용률만 알고 누가 썼는지는 모른다.

## 세션 운영

- **시작 시:** `ideas/PIPELINE.md`를 읽고, 작업 중인 `<slug>`의 `PROGRESS.md`를 읽는다. 마지막 미완료 단계에서 이어간다. "이전 세션에서 [단계]까지 완료. [다음 단계]부터 진행합니다"라고 알린다.
- **단계 완료 시:** `PROGRESS.md`와 `PIPELINE.md`의 단계 열을 갱신한다. 게이트 판정과 근거를 한 줄로 남긴다.
- **종료·보류 시:** `PIPELINE.md`에 사유를 적는다. 디렉터리는 지우지 않는다. 죽은 아이디어의 리서치는 다음 아이디어의 프리플라이트 자료다.
- **커밋:** 게이트를 하나 넘을 때마다 `ideas/<slug>/`를 커밋한다. 메시지는 `<slug>: G2 통과 — SOM 1,200억, 경쟁사 3곳 취약점 특정` 형식으로 판정과 근거를 담는다.

## PIPELINE.md 형식

```markdown
| slug | 한 줄 문제 정의 | 현재 단계 | 마지막 게이트 | 판정 | 다음 액션 | 갱신일 |
|---|---|---|---|---|---|---|
| ai-care-robot | 독거노인 낙상 감지 | S3 | G2 | 통과(조건부) | 포지셔닝·린 캔버스 작성 | 2026-09-08 |
| cafe-waste | 카페 원두 찌꺼기 처리비 | S0 | - | 진행 중 | 프리플라이트 | 2026-09-14 |
| pet-meds-sub | 반려동물 상비약 정기배송 | S5 | G4 | 통과(실증 대기) | 사용자가 프로토타입 착수 여부 결정 | 2026-09-12 |
```

## 하지 말 것

- 리서치 없이 시장 규모 숫자를 쓰는 것
- 인터뷰 없이 G5를 통과시키는 것. 데스크 리서치의 "고객 목소리"는 인터뷰 대체가 아니다
- 인터뷰가 없다는 이유로 S0~S4를 멈추거나 감점하는 것. 실증 부재는 「인터뷰 대기 질문」에 적고 진행한다
- 스코어카드 없이 기획서를 쓰는 것
- 게이트 판정을 사용자가 원하는 쪽으로 기울이는 것
- 저장소 루트나 홈 디렉터리에 산출물을 만드는 것
