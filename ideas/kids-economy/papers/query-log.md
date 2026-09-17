# paper-lookup 검색 로그 — 대기 시간 설계

조회일: **2026-09-17** · 목적: S2 "사기 전 대기" 규칙의 시간 길이를 근거로 정하기
API 키: 없음 (OpenAlex·Europe PMC 모두 무키 rate limit으로 진행). `OPENALEX_API_KEY`가 있으면 검색 한도가 올라간다.

## 질의 목록

| # | DB | 엔드포인트 | 파라미터 | 결과 |
|---|---|---|---|---|
| 1 | OpenAlex | `GET /works` | `search=delay discounting children age differences developmental`, `sort=cited_by_count:desc`, `per_page=6` | 16,520건 — **전문(fulltext)까지 검색해 노이즈 과다. 폐기** |
| 2 | OpenAlex | `GET /works` | `filter=title_and_abstract.search:"delay discounting" AND children`, `sort=cited_by_count:desc`, `per_page=8` | **196건** |
| 3 | OpenAlex | `GET /works` | `filter=title_and_abstract.search:"delay of gratification" AND children` | **606건** |
| 4 | OpenAlex | `GET /works` | `filter=title_and_abstract.search:"time perception" AND children AND duration` | **85건** |
| 5 | OpenAlex | `GET /works` | `filter=title_and_abstract.search:"cooling-off" AND (purchase OR consumer OR buying)` | **218건** |
| 6 | OpenAlex | `GET /works` | `filter=title_and_abstract.search:"episodic future thinking" AND (children OR child OR adolescent)` | **115건** |
| 7 | OpenAlex | `GET /works` | `filter=title_and_abstract.search:"delay of gratification" AND (strategy OR distraction OR abstract OR attention)` | **467건** |
| 8 | OpenAlex | `GET /works` | `filter=title_and_abstract.search:children AND (snack OR food) AND delay AND reward AND choice` | **37건** |
| 9 | OpenAlex | `GET /works` | `filter=title_and_abstract.search:"waiting period" AND (purchase OR consumer) AND impulse` | **4건 — 사실상 빈 결과** |
| 10 | OpenAlex | `GET /works` | `filter=title_and_abstract.search:"delay discounting" AND (food OR consumable) AND (money OR monetary)` | **136건** |
| 11 | OpenAlex | `GET /works/doi:{doi}` | 4건 개별 조회 + `scripts/openalex_abstract.py` | 2건 초록 확보, **2건은 `abstract_inverted_index` 없음** |
| 12 | Europe PMC | `GET /search` | `query=DOI:"..."`, `format=json`, `resultType=core` | 6건 조회, **6건 초록 확보** |

## 재현 시 주의 (실제로 겪은 실패)

- **OpenAlex `search=`는 전문까지 훑어 노이즈가 심하다.** 질의 1이 그랬다 — 인용순 정렬과 겹치면 주제와 무관한 초고인용 논문(Lancet, 당뇨 가이드라인)이 상위를 채운다. `filter=title_and_abstract.search:`로 좁혀야 쓸 만해진다.
- **Europe PMC에 `--data-urlencode 'format=json&resultType=core&pageSize=1'`로 묶어 넘기면 실패한다.** `&`가 인코딩돼 단일 파라미터가 되고, 응답이 JSON이 아니라 XML `errorBean`으로 온다(HTTP 200). 각각 `-d 'format=json' -d 'resultType=core'`로 분리해야 한다.
- **Europe PMC 필드 질의에서 `TITLE:"..." AND (ABSTRACT:x OR ABSTRACT:y)` 조합이 `errorBean`을 반환**했다. 같은 검색을 OpenAlex로 우회했다.
- **OpenAlex에 초록이 없는 레코드가 있다.** Daniel 2015, Zélanti 2011 모두 `abstract_inverted_index`가 null이었고 Europe PMC에는 있었다. "초록 없음"이 "논문 없음"이 아니다.

## 확인하지 못한 것

- Mischel(1970, 1972)의 초록 — 두 논문 모두 초록이 색인돼 있지 않다(1970년대 APA 논문). 주의 기제에 관한 내용은 **2차 인용으로만** 다뤘고 본문 대조는 못 했다.
- 6~9세 **구매 맥락**의 지연 연구 — 실험실 과제(마시멜로·지연 할인)는 풍부하나, 실제 매장·용돈 상황의 무작위 실험은 이 경로로 찾지 못했다.
- 아동 대상 **분 단위 지연**의 용량-반응(얼마나 짧아도 효과가 있는지) — 직접 다룬 연구를 특정하지 못했다.
