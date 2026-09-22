# 구현 명세 — kids-economy POC Phase 1

2026-09-22 · **1인 · 8주 · 기성 부품만**
읽는 순서: [scenarios.md](scenarios.md)(무엇을) → **이 문서**(어떻게) → [poc-scope.md](poc-scope.md)(언제까지)
화면 그림: [게시본](https://claude.ai/artifact/9X44vCj3K2yqCzqvgjzNnh)

---

## 0. 범위

| 넣는다 | 뺀다 |
|---|---|
| 온보딩 1~5 · 보여주기 · 홈 · 나누기 · 돌아보기 | 결제·구독 · 영문판 · 아이 계정 · 설정 화면 · 위시리스트 · 대기 타이머 · 사진 서버 업로드 |

**원칙 세 가지가 구현을 지배한다.**
1. **아이 계정 없음** — 계정은 부모 하나. 아이 정보는 닉네임과 연령대뿐
2. **목표 사진은 기기 안에만** — 서버 업로드 없음 ([ops-autonomy D1](ops-autonomy.md))
3. **「샀어요」가 유일한 기록 입구** — 안 산 것은 저장하지 않는다

---

## 1. 기술 스택 (권장)

| 층 | 선택 | 이유 |
|---|---|---|
| 앱 | **React Native + Expo** | 1인이 iOS·Android를 동시에. EAS Build로 서명·배포 간소화 |
| 백엔드 | **Supabase** (Postgres + Auth + Row Level Security) | 무료 티어로 POC 충분. RLS로 가구별 격리를 DB가 보장 |
| 알림 | **Expo Push Notifications** → FCM/APNs | 서버 코드 없이 스케줄 발송 |
| 사진 | **expo-file-system** (앱 문서 디렉터리) | 서버에 안 올린다. `expo-image-manipulator`로 긴 변 800px 리사이즈 |
| 상태 | 로컬 우선(SQLite/AsyncStorage) + 서버 동기화 | **오프라인에서도 보여주기가 떠야 한다** — 마트 지하는 신호가 약하다 |
| 계측 | 자체 이벤트 테이블 (외부 SDK 없음) | 아동 관련 서비스에서 서드파티 SDK는 COPPA 리스크 |

> **오프라인 동작이 필수다.** 보여주기는 마트에서 쓰인다. 목표·잔액·사진이 전부 로컬에 있어야 하고, 서버는 동기화만 한다.

---

## 2. 데이터 모델

```sql
-- 부모 계정 (Supabase auth.users와 1:1)
profile        (id PK, email, locale, timezone, push_token, created_at)

-- 아이 — 실명·생일·사진 없음
child          (id PK, profile_id FK, nickname, age_band SMALLINT, created_at)
               -- age_band: 6|7|8|9

-- 용돈 설정
allowance      (child_id FK, amount INT, period TEXT, payday SMALLINT, next_payout_at DATE)
               -- period: 'weekly'|'biweekly'|'monthly', payday: 0(일)~6(토)

-- 두 칸
bucket         (child_id FK, type TEXT, ratio SMALLINT, balance INT)
               -- type: 'spend'|'save'  ratio 합은 항상 100

-- 목표
goal           (id PK, child_id FK, name TEXT, target_amount INT,
                photo_local_uri TEXT NULL,   -- 기기 경로. 서버에는 이 문자열만
                status TEXT, created_at, achieved_at NULL)
               -- status: 'active'|'achieved'|'replaced'

-- 주차 기록
week           (id PK, child_id FK, week_of DATE,        -- 그 주 월요일
                allocated_spend INT, allocated_save INT,
                counted_spend INT NULL,                   -- 주말에 센 실제 잔액
                carried_over INT NULL,                    -- 모을 돈으로 넘긴 금액
                closed_at TIMESTAMPTZ NULL)

-- 「샀어요」 — 유일한 지출 기록
purchase       (id PK, child_id FK, week_id FK, amount INT,
                label TEXT NULL,                          -- 선택 입력
                created_at TIMESTAMPTZ)

-- 주말 회고 (질문 노출 여부만. 답은 저장하지 않는다)
reflection     (child_id FK, week_id FK, question_key TEXT, shown_at TIMESTAMPTZ)

-- 계측
event          (id PK, profile_id FK, name TEXT, props JSONB, created_at)
```

**저장하지 않는 것:** 아이 실명·생일·사진 · 안 산 물건 · 회고 답변 · 위치 · 광고 식별자

**RLS:** 모든 테이블에 `profile_id = auth.uid()` 정책. 가구 간 데이터는 DB 레벨에서 차단한다.

---

## 3. 핵심 계산 — 한 곳에 모은다

**이 네 함수가 제품의 전부다. 별도 모듈로 빼고 단위 테스트를 붙인다.**

```ts
/** 주당 모을 돈 (배분액 기준, 이월은 제외) */
weeklySaving(child): number
  = bucket('save').ratio / 100 * allowance.amount
    * (period === 'weekly' ? 1 : period === 'biweekly' ? 0.5 : 12/52)

/** 목표까지 남은 주 — 올림 */
weeksLeft(goal, saveBalance, weeklySaving): number
  if (weeklySaving <= 0) return Infinity          // 배분 0% → "언제 살 수 있을지 몰라요"
  const left = max(0, goal.target_amount - saveBalance)
  return ceil(left / weeklySaving)

/** 보여주기 — "이거 사면 몇 주" */
weeksIfSpend(amount): number
  = weeksLeft(goal, saveBalance - amount, weeklySaving)
  // 쓸 돈을 쓰면 주말 이월액이 그만큼 줄어드는 것과 같다

/** 진행률 (사진 선명도·막대) */
progress(goal, saveBalance): number = clamp(saveBalance / goal.target_amount, 0, 1)
```

### 보여주기 슬라이더 구간 계산

트랙 아래 `3주 ┊ 4주 ┊ 5주`는 **경계를 역산해서** 그린다.

```ts
/** 슬라이더 0~max에서 주 수가 바뀌는 지점들 */
weekBoundaries(max: number): {amount: number, weeks: number}[]
  // w주가 유지되는 최대 금액 = w * weeklySaving - (target - saveBalance)
  // 예) target 12,800 · save 6,800 · weekly 2,500
  //     3주 유지 최대 = 3*2500 - 6000 = 1,500원
  //     4주 유지 최대 = 4*2500 - 6000 = 4,000원
```

**슬라이더 스펙:** 범위 `0 ~ max(5000, 쓸 돈 잔액)` · 스텝 **100원** · 초기값 **0** · 핸들 최소 44×44 터치 영역

> ### ⚠ 쓸 돈은 모을 수 없다
> `closeWeek()`에서 **쓸 돈 잔액은 매주 0으로 리셋되고 남은 금액은 모을 돈으로 넘어간다.**
> 따라서 **쓸 돈으로 살 수 있는 상한은 주당 배분액**이고, "몇 주 참아서 쓸 돈을 모으는" 경로는 존재하지 않는다.
> 비싼 것은 오직 **모을 돈 목표**로만 갈 수 있다 — 이것이 규칙 A의 구현상 의미다. EC-4가 여기 걸린다.

### 주말 정산 (돌아보기 확인 시)

```ts
closeWeek(week, countedSpend):
  carried = max(0, countedSpend)            // 쓸 돈에 남은 실제 금액
  bucket('save').balance += carried
  bucket('spend').balance = 0               // 쓸 돈은 매주 리셋 (규칙 A와 일관)
  week.counted_spend = countedSpend
  week.carried_over  = carried
  week.closed_at     = now()
  if (saveBalance >= goal.target_amount) goal.status = 'achieved'
```

### 배분일 (나누기 확정 시)

```ts
payout(child, spendRatio):
  bucket('spend').balance += allowance.amount * spendRatio/100
  bucket('save').balance  += allowance.amount * (100-spendRatio)/100
  week.allocated_spend / allocated_save 기록
  allowance.next_payout_at = 다음 payday
```

---

## 4. 화면 명세

### 4-1. 보여주기 `/show` ★

| 영역 | 내용 | 상태 |
|---|---|---|
| 배지 | "{닉네임}이가 보는 화면" | 고정 |
| **목표 사진** | 로컬 이미지. **하단 `progress`만 선명**, 상단은 `rgba(250,247,240,.93)` 오버레이 | 사진 없으면 → **§5 EC-3** |
| 되돌아가는 구간 | 슬라이더 금액이 0보다 크면 빗금 띠 표시. 높이 = `amount / target` | `amount = 0`이면 숨김 |
| 주 수 | `weeksLeft` → `weeksIfSpend`. **같으면 화살표·빨간 숫자를 숨기고 현재 주 수만** | `amount = 0`이거나 주 수 동일 시 단순 표시 |
| 문구 | 차이 1주 → "토요일이 한 번 더 지나야 해" / 2주 이상 → "토요일이 {n}번 더 지나야 해" | |
| **슬라이더** | §3 스펙. **부모가 조작** | |
| 구간 라벨 | `weekBoundaries`로 폭 계산 | 경계가 화면 밖이면 마지막 구간을 "더" 로 표기 |
| 오늘 쓸 수 있는 돈 | `bucket('spend').balance` | |
| 부모 대사 | 5~8개 중 순환. 금액·근접도에 따라 가중 | |
| **[샀어요]** | `amount > 0`일 때만 활성. 누르면 **라벨 입력(선택, 건너뛰기 가능)** → `purchase` 생성 + `spend.balance -= amount` | `amount = 0`이면 비활성 |
| [닫기] | **아무것도 저장하지 않는다.** 이벤트만 `show_closed` | |

**계측 이벤트:** `show_opened` · `slider_moved`(최종값만) · `show_bought`(amount, has_label) · `show_closed`(amount)
→ `show_opened` 대비 `show_bought` 비율이 **A5**, 주간 `show_opened` 횟수가 **A3′**

### 4-2. 홈 `/`

목표 카드(탭 → 목표 편집) · 큰 [보여주기] 버튼 · 두 칸 카드 · 이번 주 쓴 돈 · 하단 [나누기] [돌아보기]

배분일이 오늘이거나 지났으면 **[나누기]를 강조**하고, 토요일이면 **[돌아보기]**를 강조한다.

### 4-3. 나누기 `/allocate`

슬라이더 하나(쓸 돈 비율, 스텝 5%) · 프리셋 [지난주와 같이] [반반] · *"이대로면 {goal}까지 {n}주"* · [이렇게 줄게요] → `payout()`

### 4-4. 돌아보기 `/review`

`purchase` 목록(요일·라벨·금액) → 합계 → **늦어짐/앞당김 두 줄** → 목표 막대 → **질문 한 줄**(`reflection` 기록) → 잔액 입력 → [확인] → `closeWeek()`

**늦어짐 계산:** `weeksLeft(정산 후)` vs `weeksLeft(지출이 0이었다면)`. 차이가 0이면 늦어짐 줄을 숨기고 앞당김만 보여준다.

**질문 순환:** 고정 배열 8개를 `week_of` 기준으로 순환. 답은 받지 않는다.

### 4-5. 온보딩 `/onboarding/[1-5]`

| 단계 | 입력 | 검증 |
|---|---|---|
| 1 | 닉네임(1~10자), 나이(6~9) | 실명 안내 문구 노출 |
| 2 | 금액(500~50,000, 100 단위), 주기, 주는 날 | |
| 3 | 두 칸 비율(5% 스텝) | 합 100% 강제 |
| 4 | 목표 이름·금액 | **`weeksLeft` 즉시 표시. 6주 초과 시 경고**(진행은 허용) |
| 5 | 사진(카메라/사진첩) + 지갑 준비 | **사진 건너뛰기 허용** → EC-3 |

각 단계 이탈 지점을 `onboarding_step_{n}_done`으로 계측 → **온보딩 통과율**(획득 산수의 첫 칸)

---

## 5. 엣지 케이스 — 여기서 버그가 난다

| # | 상황 | 처리 |
|---|---|---|
| **EC-1** | 목표 금액 ≤ 모을 돈 (이미 달성) | 보여주기에 **"살 수 있어!"** 상태. 사진 전부 선명. [샀어요] → 목표 `achieved`, 다음 목표 설정 유도 |
| **EC-2** | `weeklySaving = 0` (모을 돈 0% 배분) | 주 수 대신 **"이대로면 언제 살 수 있을지 몰라요"**. 나누기 화면으로 유도 |
| **EC-3** | **사진 없음** (건너뜀 / 기기 변경) | 사진 자리에 **"목표 사진을 넣어주세요"** + 카메라 버튼. **진행 막대는 회색으로 그려 기능은 유지.** 앱 실행 시 `photo_local_uri`가 가리키는 파일이 없으면 즉시 이 상태 |
| **EC-4** | 금액 > 쓸 돈 잔액 | 슬라이더는 허용. **"쓸 돈으로는 못 사"** 표시. 주 수는 **모을 돈을 깬다고 가정하고 같은 식으로** 계산해 보여준다(그만큼 목표가 멀어지는 것이 교육 내용이다). **[샀어요]는 비활성**, 대신 **[이걸 목표로 바꿀래?]** 를 제시(규칙 A). ~~"n주 모으면 살 수 있어"~~ — **쓸 돈은 모을 수 없으므로 이 문구는 틀렸다**(§3 경고 참조) |
| **EC-5** | 첫 주 (week 레코드 없음) | 돌아보기 진입 차단. "첫 용돈을 먼저 주세요" |
| **EC-6** | 배분일을 여러 주 건너뜀 | **밀린 주를 자동 지급하지 않는다.** "지난주를 건너뛰었어요" 안내 후 이번 주만 지급 |
| **EC-7** | 주말 정산 잔액 > 배분액 | 입력값 검증(0 ~ 배분액). 초과 시 경고 후 배분액으로 클램프 |
| **EC-8** | 목표 변경 | `save.balance`는 **유지**. 새 목표로 `weeksLeft` 재계산 |
| **EC-9** | 오프라인 | 보여주기·홈은 로컬 데이터로 완전 동작. 쓰기는 큐에 쌓아 복귀 시 동기화 |
| **EC-10** | 같은 주에 나누기 두 번 | 이번 주 `week`가 있으면 재지급 대신 **배분 비율만 수정** |
| **EC-11** | 자녀 2명 이상 | **Phase 1에서는 1명만.** 온보딩에서 추가 자녀 입력을 막고 "곧 지원합니다" 표시 |
| **EC-12** | 시간대·서머타임 | 모든 날짜 계산은 `profile.timezone` 기준 로컬 날짜로. UTC 저장, 표시만 변환 |

---

## 6. 알림 — 두 종류뿐

| 알림 | 시각 | 문구 | 중단 조건 |
|---|---|---|---|
| 배분일 | payday 09:00 | "용돈 주는 날이에요. 둘로 나눠볼까요?" | 그 주 `week`가 이미 생성됨 |
| 주말 돌아보기 | 토요일 19:00 | "이번 주 5분만. 질문 하나 준비해뒀어요" | 그 주가 이미 `closed` |

**3주 연속 무반응이면 발송을 멈추고** 앱 실행 시 복귀 안내를 띄운다. (알림 피로 = 삭제)

---

## 7. 구현 순서 (8주)

| 주 | 할 일 | 끝나면 |
|---|---|---|
| 1 | Expo 프로젝트 · Supabase 스키마 + RLS · 인증 | 로그인해서 빈 홈이 뜬다 |
| 2 | 온보딩 1~3 · 로컬 저장소 · 동기화 뼈대 | 계정 만들고 용돈·비율이 저장된다 |
| 3 | **§3 계산 모듈 + 단위 테스트** · 온보딩 4~5(사진 로컬 저장) | **주 수 계산이 EC-1·2·4를 통과한다** |
| 4 | **보여주기** — 사진 진행바 · 슬라이더 · 구간 라벨 | **핵심 화면이 손에서 돈다** |
| 5 | 보여주기 「샀어요」 · 홈 | 기록이 쌓이고 홈에 보인다 |
| 6 | 나누기 · 배분 로직 · 알림 2종 | 주간 루프가 한 바퀴 돈다 |
| 7 | 돌아보기 · 주말 정산 · 질문 순환 | **루프가 닫힌다** |
| 8 | 계측 이벤트 · 엣지 케이스 · 베타 배포(TestFlight/내부 테스트) | 실사용 관찰 가능 |

**버퍼 0.3주.** 부족하면 [컷 옵션](poc-scope.md) 1순위 — **홈을 보여주기에 통합**(0.5주 회수).

> **3주차가 분기점이다.** 계산 모듈이 틀리면 나머지 화면이 전부 거짓말을 한다. 여기에만 단위 테스트를 붙인다.

---

## 8. 만들지 않는 것 (요청이 와도)

| | 왜 |
|---|---|
| 아이 로그인 | COPPA·문의 폭증. 아이 화면은 부모 폰을 건네는 것으로 충분 |
| 사진 서버 업로드 | 모더레이션이 사용자 수에 비례하는 사람 손을 만든다 |
| 지출 자동 기록·영수증 촬영 | 기록 축은 무료로 포화. 입력 부담이 A1을 죽인다 |
| 퀴즈·레벨·뱃지 | 지식은 오르고 행동은 안 바뀐다 |
| 또래 비교·랭킹 | 소비가 사회적 비교에 붙으면 필요/욕구 구분이 무너진다 |
| 조르기·자동충전 | **제약을 지우는 기능.** 경쟁 제품의 실패 지점 |

---

## 부록. 계산 검산 (구현 시 이 표를 단위 테스트로)

**입력:** 목표 12,800원 · 모을 돈 6,800원 · 주당 모을 돈 2,500원 · 주당 쓸 돈 2,500원

### A. 보여주기 — 금액별 주 수

| 금액 | 0 | 500 | 1,000 | 1,500 | **1,600** | 2,000 | 4,000 | **4,100** |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 주 | 3 | 3 | 3 | 3 | **4** | 4 | 4 | **5** |

**경계는 1,500원과 4,000원.** 슬라이더 트랙(max 5,000)에서 **30% / 50% / 20%** 로 갈린다.

### B. 주말 정산 — 늦어짐

| 이번 주 지출 | 이월 | 정산 후 모을 돈 | 주 수 | 안 썼다면 | **차이** |
|---:|---:|---:|:--:|:--:|:--:|
| 0원 | 2,500 | 11,800 | 1 | 1 | **0** ← 늦어짐 줄 숨김 |
| 500원 | 2,000 | 11,300 | 1 | 1 | **0** |
| **2,000원** | 500 | 9,800 | 2 | 1 | **1주** |
| 2,500원 | 0 | 9,300 | 2 | 1 | **1주** |

> **작은 지출은 주 수에 안 나타난다.** 이건 버그가 아니라 사실이다 — 500원은 실제로 목표를 밀지 못한다.
> 그때는 **앞당김만** 보여준다(§4-4).

### C. 반드시 테스트할 것

```
weeksLeft(save >= target)          → 0        (EC-1)
weeksLeft(weeklySaving = 0)        → null     (EC-2)
weeksIfSpend(0) === weeksLeft()               (금액 0이면 변화 없음)
weekBoundaries(max) 가 오름차순이고 마지막이 max 이상
closeWeek 후 spend.balance === 0              (쓸 돈 리셋)
closeWeek 후 save.balance 증가분 === carried
timezone 이 다른 두 사용자의 "이번 주"가 각자 로컬 기준
```
