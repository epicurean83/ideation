# kids-economy 해외 도달 검증 — 데스크 리서치 (영어권 초등 모수 · 용돈 실태 · 아동 금융 앱 침투율)

조회일: 2026-09-17 (모든 항목 공통) · 목적: [reach-cost-gate.md](../reach-cost-gate.md) P2(해외 동시 출시) 경로의 "S1 재진입 시 확인할 것 1·2"에 대한 근거

---

## 1. 영어권 주요국 초등 학령 인구

| 국가 | 수치 | 연도 | 출처 | 신뢰도 |
|---|---|---|---|---|
| 미국 | 공립 K-8 전체 **3,250만 명** | 2022년 가을 | [NCES Fast Facts](https://nces.ed.gov/fastfacts/display.asp?id=372) | High (공식) |
| 미국 | 공립 K-5(초등)만: 2019년 가을 대비 2024년 가을 **-94만 명(-4%)** 감소. 역산하면 2019년 K-5 ≈ **2,350만 명**, 2024년 K-5 ≈ **2,256만 명** | 2024년 가을 | [FutureEd (NCES 데이터 인용)](https://www.future-ed.org/k-12-public-school-enrollment-declines-explained/) | Medium — **역산치**. NCES 원자료의 K-5 절대값 자체는 이 경로로 못 찾았다(원본 PDF 접근 실패) |
| 미국 | 공립학교 전체 K-12: 2019년 5,080만 → 2024년 4,940만, 2030년 4,700만 미만 전망 | 2024/2030 | [FutureEd](https://www.future-ed.org/k-12-public-school-enrollment-declines-explained/) | High |
| 영국(잉글랜드) | Primary school 재학생 약 **450만 명** | 2024년 1월 | [NFER 블로그](https://www.nfer.ac.uk/blogs/just-a-little-drop-pupil-numbers-are-falling-slower-than-previous-expectations/)(DfE 통계 인용) | Medium — 2차 인용. DfE 원자료(explore-education-statistics.service.gov.uk 2024/25판)에서 정확한 primary 전용 수치를 직접 뽑지 못했다 |
| 영국(잉글랜드) | 전체 학생 900만+, 전년 대비 -5만 9,600명(-0.7%) | 2024/25 | [GOV.UK DfE](https://explore-education-statistics.service.gov.uk/find-statistics/school-pupils-and-their-characteristics/2024-25) | High |
| 캐나다 | 공립 K-12 전체 **550만 명** (전년 대비 +12만 5,200명, +2.3%, 1997/98 이래 최대 증가) | 2023/24 | [Statistics Canada](https://www150.statcan.gc.ca/n1/daily-quotidien/251028/dq251028d-eng.htm) | High |
| 캐나다 | 초등(K-6)만 별도 집계 | — | **이 경로로는 못 찾았다.** StatCan 표 37-10-0109(elementary/secondary 학교급 분리 테이블)는 인터랙티브 다운로드가 필요해 직접 값을 못 뽑음(403/데이터 미표시). 학년 구조상(초등 7개 학년/전체 12~13개 학년) 비례 추정하면 약 **280만 명 내외** — **Low, 자체 비례추정** |
| 호주 | 전체 학생 **413만 2,006명**(2024) → **416만 918명**(2025) | 2024/2025 | [ABS Schools](https://www.abs.gov.au/statistics/people/education/schools/2024), [2025판](https://www.abs.gov.au/statistics/people/education/schools/latest-release) | High |
| 호주 | Primary만 별도 절대값 | — | **이 경로로는 못 찾았다.** ABS 발표는 전년 대비 증감(+9,859명 2024, -7,013명 2025)만 제공, 절대 총량은 데이터큐브 직접 조회가 필요. 학년 구조 비례 추정(초등 7개 학년/전체 13개 학년) 시 약 **220만~225만 명** — **Low, 자체 비례추정** |

### 합계 (영어권 4개국 초등 학령 인구)

| 구성 | 수치 | 신뢰도 |
|---|---|---|
| 미국 K-5(공립만) | 2,256만 | Medium(역산) |
| 영국 Primary | 450만 | Medium |
| 캐나다 초등(추정) | 280만 | Low(비례추정) |
| 호주 Primary(추정) | 220만 | Low(비례추정) |
| **4개국 합계** | **약 3,206만 명** | 혼합(가중 Medium~Low) |

미국 사립학교(전체 학생의 약 10% 내외로 알려짐, 이번 경로로 별도 검증 못함)까지 더하면 **3,400만~3,500만 명** 범위로 올라간다.

**한국 초등 전체(2025년 234.5만 명, [reach-sizing.md](../reach-sizing.md) 참조) 대비 약 14배.** "자릿수가 하나 크다"는 reach-cost-gate.md의 가설은 **성립한다.** 단, 캐나다·호주 수치는 비례추정이라 실제 값이 20~30% 벗어날 수 있음을 감안해도 자릿수 결론 자체는 바뀌지 않는다.

---

## 2. 대응 가구 수

**국가별 "초등 자녀가 있는 가구" 공식 통계는 이 경로로는 못 찾았다.** 미국 Census Bureau의 "America's Families and Living Arrangements" 보고서에 관련 표(F2, C3)가 존재하는 것은 확인했으나, 웹서치 경로로는 표 내부 수치에 접근하지 못했다(다운로드 필요).

**대안 추정(Low confidence, 방법만 명시):**
- 미국 합계출산율(2024년 약 1.6)이 한국(0.7~0.8대)보다 훨씬 높아 형제자매 동시 재학 비율이 더 크다. 가구당 초등 자녀 수를 1.3명으로 가정하면(자체 가정, 검증 안 됨) 미국 K-5 대응 가구는 **약 1,735만 가구**.
- 같은 가정(÷1.3)을 영국·캐나다·호주에 적용하면 영국 약 346만, 캐나다(추정) 약 215만, 호주(추정) 약 169만 가구.
- **4개국 합계 대응 가구(추정): 약 2,465만 가구** — 이 값은 국가별 실제 출산율·다자녀 분포를 반영하지 않은 단일 가정이므로 **Low, 방향성 참고용으로만 사용.**

---

## 3. 용돈(allowance / pocket money) 지급률·금액·주기

### 미국

- **71%의 미국 부모(자녀 5~17세)가 정기 용돈을 준다.** 평균 주당 **$37**(2025년), 중앙값 **$20/주**. 표본 1,587명, 2025.4.28~5.8 조사. 출처: [Wells Fargo 뉴스룸](https://newsroom.wf.com/news-releases/news-details/2025/New-Wells-Fargo-Study-Shows-Parents-Give-Their-Kids-an-Average-Weekly-Allowance-of-37/default.aspx) — **Medium**(자체 설문, 응답 편향 가능성 있으나 대형 은행의 공개 발표)
- **연령대별 주당 평균(Wells Fargo, 2025):** 5~8세 **$31.50** / 9~11세 $34.32 / 12~14세 $36.05 / 15~17세 $44.88. 본 프로젝트 타깃(6~9세)은 5~8세 구간에 가장 가깝다. — **Medium**
- **Greenlight 앱 자체 실사용 데이터(설문이 아닌 실거래 기반):** 5~19세 평균 주당 **$13.15**(2025년). 설문치($31~37)와 실거래치($13) 사이 약 2.5~3배 격차 — **실제 용돈은 자기보고 설문보다 낮을 가능성.** 출처: [Greenlight Learning Center](https://greenlight.com/learning-center/earning/average-allowance-by-age-for-kids) — **Medium**(자사 데이터, 자사 가입자 모집단으로 편향 가능)

### 영국

- **주당 평균 £9.90**(7~18세, 2026년 1~4월), 전년 동기 £9.78 대비 +1.2%. 6세는 £4.99(2024.3~2025.2), 17세는 £23.97. 출처: [LBC/GoHenry 데이터](https://www.lbc.co.uk/article/e818ae81cacd43f3a2c1f0f3d9114f11-5HjdbFk_2/), [RoosterMoney Pocket Money Essentials 2024-25](https://roostermoney.com/the-pocket-money-essentials-2024-2025/) — **Medium**(핀테크 앱 자체 데이터베이스, 자사 가입자 기준이라 전 국민 대표성 낮음)
- **연령별(RoosterMoney 데이터, 6~9세만 발췌):** 6세 £2.81/주, 7세 £2.85/주, 8세 £2.97/주, 9세 £3.13/주 — 미국 대비 절대액이 훨씬 낮다(6~9세 기준 미국의 1/10 수준). — **Medium**
- **몇 %의 영국 부모가 용돈을 주는지는 이 경로로는 못 찾았다.** 여러 2차 가이드(wecovr 등)가 "평균 금액"만 인용하고 지급률(%)이나 원 설문 출처·날짜를 명시하지 않아 신뢰할 수 없는 자료로 판단, 채택하지 않음.
- **한국 대비:** 한국 83.8% 지급률(윤선생 설문, reach-sizing.md 인용)과 직접 비교할 미국·영국 지급률 %는 미국만 확보(71%). 영국은 미확보.

---

## 4. 아동 금융 앱 실사용자 규모 및 침투율

| 앱 | 지역 | 사용자 규모 | 대상 모수 대비 침투율(계산) | 출처 | 신뢰도 |
|---|---|---|---|---|---|
| **Greenlight** | 미국 | **650만+** 부모+자녀 (2025년) | 미국 K-5 2,256만 대비 약 **29%**, 단 Greenlight는 5~19세 대상이라 모수를 K-5로 한정하는 것은 과대추정. 5~19세 전체 인구(약 6,700만, 미검증 자체 추정)로 나누면 약 **9.7%** | [Sacra](https://sacra.com/c/greenlight/), 자사 연간 리포트 | Medium(자사 발표) |
| **Acorns Early(구 GoHenry, 미국)** | 미국 | **약 100만~140만 명**(2025년 2월 100만 돌파 발표, 이후 140만+ 언급) | 미국 K-5 대비 4~6% | [PR Newswire](https://www.prnewswire.com/news-releases/acorns-marks-milestone-of-one-million-kids-served-in-us-expanding-family-financial-wellness-offerings-with-acorns-early-302367447.html) | Medium |
| **GoHenry(영국, Acorns 인수 전 글로벌 누적)** | 영국 중심 | **200만+**(누적, 인수 전 시점) | 영국 Primary 450만 대비 약 44%이나 **누적 가입 기준**(활성 아님) — 한국 사례에서 확인한 "누적≠MAU" 함정과 동일 | [Money Marketing](https://www.moneymarketing.co.uk/news/us-investment-platform-acquires-gohenry/) 등 | Medium(언론 인용, 활성/누적 구분 불명확) |
| **BusyKid** | 미국 | **100만+ 사용자**(누적, 시점 불명) | 정밀 계산 불가(모수·시점 불일치) | [BusyKid 자사 소개](https://www.educationtechnologyinsights.com/busykid) | Low(자사 발표, 활성/누적 불명) |
| **Mydoh(RBC, 캐나다)** | 캐나다 | 약 **20만 명**(2024년 9월) | 캐나다 초등 추정 280만 대비 약 **7%**(단, Mydoh는 8~17세 대상이라 초등 모수 대비 과소평가됨) | [보도자료 인용](https://www.newswire.ca/news-releases/) | Medium |
| **Spriggy** | 호주 | **130만+ 회원**(최신), 이전 시점 120만(2024.11) / 일부 기사는 30만+ 가구로 표현 — 표현 단위 혼재 | 호주 전체 학생 416만 대비 약 **31%**(단, 개인 회원 수 기준이라 부모+자녀 중복 포함 가능성 높음). 가구 단위(30만) 기준으로는 훨씬 낮음 | [Spriggy 자사 페이지](https://www.spriggy.com.au/pricing), [smallbizai 기사](https://smallbizai.au/spriggy-sydney-ai-kids-money-app-australia/) | Low(단위 불일치 — 개인 vs 가구 수치가 기사마다 다름, 정밀 재계산 보류) |
| **RoosterMoney(영국, NatWest)** | 영국 | **35만+ 명**(자사 Pocket Money Index 표본) | 영국 Primary 450만 대비 약 **8%**(단, RoosterMoney는 6~18세 전체 대상이라 초등만으로 보면 실제 침투율은 이보다 낮음) | [RoosterMoney 자사 리포트](https://roostermoney.com/the-pocket-money-essentials-2024-2025/) | Medium(자사 발표) |

### 침투율 기준선 — 결론

- **영어권 아동 금융 앱의 실현된 침투율은 대체로 모수 대비 한 자릿수(4~10%) 구간에 몰려 있다.** 예외적으로 Greenlight(미국, 약 10~29%대 계산치, 모수 정의에 따라 편차 큼)와 Spriggy(호주, 30%대로 계산되나 단위 불일치로 신뢰도 낮음)가 높게 나오는데, **둘 다 카드 발급 기반**이다. 이는 국내 리서치(reach-cost-gate.md)에서 이미 확인된 패턴 — "카드가 유통을 만든다" — 과 동일하게 재확인된다.
- **카드 미발급 순수 침투율 사례는 이번 조사에서 분리해내지 못했다.** RoosterMoney·BusyKid·Mydoh도 실질적으로 카드/선불결제 상품을 병행 판매하며, "카드 없는 순수 습관 앱만의 침투율"을 분리한 공개 수치는 찾지 못했다.
- **결론: 영어권에서 "카드 없이 습관만으로" 모수의 2~3%를 먹는다는 reach-cost-gate.md의 가정은, 카드 기반 제품들의 실현 침투율(4~30%)보다 낮게 잡은 것이라 보수적인 편이며 방향성은 유지된다.** 다만 이는 카드 없는 사례가 실제로 존재하고 검증됐다는 뜻이 아니라, **카드 있는 사례들의 하한선(4~10%)보다 낮게 목표를 잡았다는 의미일 뿐**이다.

---

## 5. 카드 미발급 용돈/습관 앱(영어권)

- **RoosterMoney(영국)**: 앱 자체는 NatWest 계열 선불카드(Rooster Card)를 핵심 상품으로 판매 중이나, **카드 없이 트래커만 쓰는 무료 티어가 존재하는 것으로 알려져 있다** (자사 웹사이트에 "가상 용돈 관리" 옵션 언급). **단, 카드 미사용 사용자만의 별도 규모는 이 경로로는 못 찾았다** — 전체 35만 명에 카드 미사용자가 몇 명 포함되는지 공개되지 않음.
- **iAllowance, Bankaroo** 등 카드 없이 가상 잔액·chore(집안일) 기반으로만 동작하는 앱이 존재한다는 것은 일반적으로 알려져 있으나(오랜 기간 앱스토어에 존재), **사용자 규모·활성 지표를 이번 검색 경로로는 전혀 찾지 못했다.** 이들은 공개 투자·언론 노출이 거의 없는 소규모 인디 앱으로 보이며, 규모를 추정할 근거 자체가 없다.
- **결론: "카드 미발급 + 규모가 검증된" 영어권 사례는 이번 조사에서 찾지 못했다.** 국내 리서치(alternatives-research.md)에서 확인된 것과 동일한 공백 — 대기 기능·비카드 습관 앱은 국내외 모두 시장에서 규모를 키운 사례가 확인되지 않는다.

---

## 확인하지 못한 것 (명시)

1. 미국 K-5의 NCES 공식 절대값(원본 PDF가 이 경로에서 읽기 불가 — 인코딩 문제). 대신 증감률로 역산.
2. 캐나다·호주의 초등/primary 전용 절대 학생 수(전체는 확보, 학교급 분리 표는 인터랙티브 다운로드 필요해 접근 못함). 비례추정치로 대체.
3. 4개국 공통의 "초등 학령 자녀가 있는 가구 수" 공식 통계 — 전부 방법론적 추정으로 대체(Low).
4. 영국 부모의 용돈 지급률(%) — 신뢰할 수 있는 1차 출처를 못 찾음.
5. 카드 미발급 아동 습관 앱(iAllowance, Bankaroo 등)의 사용자 규모 — 전혀 공개 자료를 찾지 못함.
6. Spriggy의 정확한 단위(개인 vs 가구)와 정확한 최신 시점 수치 — 기사마다 표현이 달라 정밀 계산 보류.
7. WebSearch 14건(예산 14건) 전량 사용, WebFetch 12건 사용 후 종료. 추가 원자료(StatCan 표 다운로드, ABS 데이터큐브, Census 상세표)는 웹서치/일반 fetch로 접근 불가해 추가 조회를 진행하지 않음.

---

## 핵심 요약 (reach-cost-gate.md로 반영할 수치)

- **영어권 4개국(미국·영국·캐나다·호주) 초등 학령 인구 합계 ≈ 3,200만 명**(미국 사립 포함 시 3,400만+) — 한국(234.5만)의 약 **14배**. "자릿수가 하나 크다"는 가설은 **성립**(미국 K-5, 캐나다·호주는 비례추정 포함이므로 Medium~Low 혼합).
- 미국 용돈 지급률 **71%**, 평균 주당 **$37**(설문) / 실거래 기준 **$13.15**(Greenlight 자사 데이터, 5~19세) — 설문과 실거래 간 2.5~3배 격차 주의. 영국 지급률(%)은 **못 찾음.**
- 영어권 아동 금융 앱 침투율은 대체로 모수의 **4~10%대**이며, 예외(Greenlight·Spriggy, 30%대 계산치)는 전부 **카드 기반**. 카드 없는 순수 습관 앱의 규모 검증 사례는 **국내와 마찬가지로 확보하지 못함.**
- reach-cost-gate.md가 가정한 "침투 2~3%로 RAU 100만"은 산술적으로 성립하며(3,200만 × 2.5% ≈ 80만~ 가구, 낙관 인당 2명 가정 시 100만+ 도달), 이는 실현된 카드 기반 앱들의 하한 침투율(4%)보다도 낮게 잡은 보수적 목표다.
- **P2(해외 동시 출시)의 "모수" 조건은 이번 조사로 뒷받침된다.** 다만 카드 없는 습관 앱이 실제로 그 침투율에 도달한 선례는 국내외 어디에도 없다는 점은 그대로 남는 리스크다.
