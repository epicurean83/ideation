# 해외 출시 규제·운영 부담 데스크 리서치

조회일: 2026-09-17 (별도 표기 없는 한 전체 항목 동일)
전제: 1인 개발자, 12주 내 POC, 이후 혼자 운영. 부모가 사용자, 아이 계정 없음(닉네임+금액만 부모가 입력), 카드·금융상품 미발급.
성격: 의사결정용 데스크 리서치. 법률 자문 아님. 법률 자문이 필요한 지점은 별도 표기.

---

## 결론 요약 (5줄)

1. **COPPA는 이 설계라면 POC를 막지 않는다.** COPPA는 "아이로부터(from children)" 수집된 정보에만 적용되고, 부모가 입력한 정보는 "아이에 대한(about children)" 정보로 취급되어 원칙적으로 적용 대상이 아니다(FTC FAQ 명문 규정, High). 다만 이는 "아이가 앱을 직접 조작하지 않는다"는 전제가 지켜질 때만 유효하며, 앱의 주제·비주얼·마케팅이 "child-directed"로 판정되면 동일 설계라도 가중치가 달라질 수 있다(Medium) — 실행 시 앱스토어 등록·마케팅 문구에서 "아동용"이 아니라 "부모용 교육 도구"로 일관되게 포지셔닝해야 한다.
2. **해외 경쟁사 중 "구매 전 대기·쿨다운" 기능은 확인되지 않았다.** Greenlight·Rooster Money·Spriggy·Mydoh·BusyKid·Acorns Early 공식 자료 어디에도 의도적 숙려기간 기능은 없다. Greenlight의 초과 지출 승인 요청은 부모 응답 지연이 우연히 "대기"처럼 작동할 뿐 설계된 쿨다운이 아니고, Rooster Money의 14일 "cooling-off"는 카드 해지 관련 소비자보호법 조항이지 구매 의사결정 기능이 아니다. **차별점은 살아있는 것으로 잠정 확인.** 단, BusyKid·Mydoh·Spriggy는 공식 문서·앱 화면까지 뒤진 것은 아니라 확인 강도는 Medium이다.
3. **Apple Kids Category / Google Play Families는 강제가 아니다.** "Made for Kids"·Kids Category는 아이가 직접 쓰는 앱에 해당하며, 부모가 자녀 정보를 관리하는 금융·교육 도구(Greenlight, GoHenry 등 실사례)는 Finance/Education 카테고리에 4+ 등급으로만 남는다. 이 앱도 같은 경로로 Kids Category를 피할 수 있을 가능성이 높다(Medium — Apple의 최종 판단은 심사 시점 재량).
4. **UK Children's Code·EU GDPR 아동 조항은 규모에 비해 부담이 크다.** ICO는 실제로 거액 제재(TikTok 1,270만 파운드, 2024)를 내린 전례가 있고, 판단 기준이 "아동이 서비스에 접근할 가능성"까지 포함해 COPPA보다 넓다. 영국·EU 동시 출시는 12주 POC 범위에서는 **뒤로 미루고 미국 우선 출시** 하는 편이 안전하다(High — 판단은 이 구조를 따름).
5. **1인 개발자의 세무·행정 부담은 감당 가능한 수준.** Apple/Google이 VAT·해외 판매세의 원천징수·대납(Merchant of Record) 대부분을 대행하고, 개발자는 W-8BEN(비거주자 원천징수 신고) 1회 제출만 하면 된다(High). 한국 기준으로는 애플 앱스토어 코리아 전자상거래법 준수를 위해 사업자등록번호(BRN) 등록이 사실상 강제된다(Medium-High) — 간이과세자 등록은 온라인으로 당일 처리 가능해 12주 일정에 지장 없음.

---

## 1. COPPA (미국)

### 1-1. 핵심 질문: 부모만 입력하고 아이 정보는 닉네임+금액뿐인 설계에 COPPA가 적용되는가

- FTC 공식 FAQ: "COPPA only applies to personal information collected online **from children**... It does not cover information collected from adults that may pertain to children." (FTC, Complying with COPPA: FAQ, F.4 / A.8) — https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions — High
- 즉 부모가 자녀 닉네임·용돈 금액을 **본인 계정에서** 입력하는 구조라면, 이는 "아이로부터" 수집된 정보가 아니라 "부모로부터" 수집된 정보이므로 COPPA의 직접 적용 대상이 아니다. High (FTC 문서 명문)
- 단, "directed to children" 판정은 별도 다요소 테스트(주제, 비주얼, 캐릭터, 광고, 마케팅 자료, 유사 서비스의 연령 구성 등, 2025년 개정으로 마케팅 계획·이용자 리뷰까지 요소 추가)로 이루어진다. 서비스가 아이가 아니라 부모를 대상으로 마케팅되면 일반 대상(general audience)으로 분류될 가능성이 높다. 다만 "이용약관에 13세 미만 금지라고 써도 그것만으로는 충분한 방어가 안 된다"는 지적이 있다(법무법인 블로그, Medium). — https://blog.promise.legal/coppa-mixed-age-audience-actual-knowledge/ — Medium
- **실무 결론:** 아이 계정을 만들지 않고, 앱 마케팅·스토어 설명·UI를 "부모가 자녀 용돈을 관리/교육하는 도구"로 일관되게 유지하면 COPPA의 아동 대상(child-directed) 판정 리스크를 낮출 수 있다. 다만 이는 확정적 법률 의견이 아니라 리서치 기반 판단이며, 실제 출시 전에는 프라이버시 변호사 검토가 권장된다(법률 자문 필요 지점으로 표기).

### 1-2. 검증 가능한 부모 동의(Verifiable Parental Consent) 방법과 비용

- 2025년 최종 규칙 개정(2025-04-22 연방관보 게재, 2025-06-23 발효, 준수 기한 2026-04-22)으로 승인 방법이 8종으로 확대: 서면 동의서 우편/팩스/스캔 회신, 신용/직불카드 결제, 지식 기반 인증(knowledge-based authentication, 2025년 신설), 정부발급 신분증 대조, 화상통화, text-plus(문자+추가 확인, 제3자 정보 미제공 시에만), 이메일+추가 확인(support for internal operations 한정) 등. — Federal Register 2025-05904, https://www.federalregister.gov/documents/2025/04/22/2025-05904/childrens-online-privacy-protection-rule — High
- 비용: 이번 리서치에서 방법별 구체적 달러 비용을 수치로 제시하는 출처는 찾지 못했다(이 경로로는 못 찾았다). 다만 이 앱 설계는 애초에 "아이 계정을 만들지 않는다"는 전제이므로 VPC 자체가 필요 없을 가능성이 높다 — VPC는 아이의 개인정보를 직접 수집·저장할 때만 발동되는 절차다.

### 1-3. FTC 제재 사례 (2024~2025년, 규모 감각용)

- Disney: 1,000만 달러 (아동용으로 미표시한 유튜브 영상 관련, 2025년 12월 법원 승인) — https://www.hunton.com/privacy-and-information-security-law/court-approves-disneys-10-million-ftc-settlement-resolving-coppa-enforcement-action — High
- Genshin Impact 개발사(Cognosphere/HoYoverse): 2,000만 달러 (2025-01-17) — High
- NGL Labs: 2024-07-09 FTC·캘리포니아 검찰 합의 (금액은 이 검색 경로에서 특정 못 함) — Medium
- Apitor Technology: 50만 달러 (재정 상태 도래 시까지 집행 유예), 중국 제3자의 아동 위치정보 무단 수집 관련 — Medium
- **패턴:** 대형 제재는 전부 "아이가 직접 앱/서비스를 사용하며 개인정보(위치, 광고 식별자 등)가 제3자로 유출된" 사례다. 이 사업처럼 아이 계정 자체가 없는 구조와는 사실관계가 다르다. High (제재 사례 자체는 공식 보도자료 기반)

### 1-4. 2025~2026년 개정 핵심

- 개인정보 정의 확장 (생체정보, 정부발급 식별자 포함)
- 제3자 타겟광고 목적의 데이터 공유는 **별도** 검증 가능한 부모 동의 필요
- "support for internal operations" 예외 요건 강화
- 문서화된 정보보안 프로그램(written information security program) 의무화
- 2026-02-25 FTC 정책성명: 나이 확인(age verification) 목적으로만 아동 데이터를 수집·사용·공개하는 경우, 사전 부모 동의 없이도 집행을 제한하겠다는 완화 방향 — 이 사업과 직접 관련성은 낮음
- 출처: Federal Register 2025-05904 / FTC 2025-01 보도자료 — https://www.ftc.gov/news-events/news/press-releases/2025/01/ftc-finalizes-changes-childrens-privacy-rule-limiting-companies-ability-monetize-kids-data — High

---

## 2. 앱스토어 아동 카테고리 (Apple / Google)

### 2-1. Apple Kids Category

- "Made for Kids"는 **앱이 11세 이하 아동을 대상으로 설계된 경우** App Store Connect에서 선택하는 항목이며, 연령대(5세 이하/6-8/9-11)를 지정해야 한다. 승인 후 변경 불가. — Apple 공식 문서 기반 요약 — High
- Kids Category 앱은 제3자 광고·분석 도구 원칙적 금지. 예외적으로 IDFA나 식별 가능 정보(이름, 생년월일, 이메일, 위치, 기기 정보)를 수집·전송하지 않는 제3자 분석, 그리고 크리에이티브를 사람이 심사하는 문서화된 정책이 있는 제3자 맥락광고(contextual ad)만 제한적으로 허용. — https://developer.apple.com/forums/thread/117320 등 개발자 포럼 종합 — Medium (1차 출처는 Apple 심사 가이드라인이나 세부 조항은 포럼 요약에 의존)
- **핵심 판단:** "Made for Kids"는 아이가 직접 사용하는 것을 전제로 한 카테고리다. Greenlight, GoHenry(현 Acorns Early), BusyKid 같은 실제 경쟁 제품은 스토어에서 Finance 카테고리·4+ 등급으로 등록되어 있고 Kids Category로 분류되지 않는다(이 리서치에서 각 앱의 스토어 페이지 존재 자체로 방증 — 카테고리 재확인은 스토어 리스팅 직접 대조로 별도 검증 권장). 부모가 사용하는 이 앱도 같은 경로를 따를 가능성이 높다. Medium.

### 2-2. Google Play Families 정책

- 앱의 **타겟 오디언스**가 아동만이면 Families 정책·자체인증(self-certified) 광고 SDK 의무 적용. 타겟 오디언스가 아동과 성인을 모두 포함하면 중립적 연령 확인 화면(neutral age screen)을 두고, 아동에게 노출되는 광고만 자체인증 SDK를 거쳐야 한다. — Google Play Console 고객센터 — High
- 앱의 타겟 오디언스를 "성인(부모)"으로 신고하면 Families 정책 적용을 피할 수 있다. Play Console의 "대상층 및 콘텐츠(Target audience and content)" 설문에서 이를 결정한다. — High
- COPPA·GDPR 등 관련 법규 준수는 Google Play 정책상 별도로 요구되며, Families 정책 미적용과 무관하게 유지된다. — High

**결론:** 앱을 "부모용 금융 교육 도구"로 일관되게 포지셔닝(스토어 설명, 타겟 오디언스 설문, 마케팅)하면 Apple Kids Category·Google Families의 강한 제약(광고·분석 도구 제한, 별도 심사)을 피할 가능성이 높다. 다만 최종 판단은 각 플랫폼의 심사 재량이라 확정은 아니다.

---

## 3. 영국 Children's Code · EU GDPR 아동 조항

### 3-1. UK Age Appropriate Design Code (Children's Code)

- 2020-09-02 시행. 위반 시 ICO는 최대 1,750만 파운드 또는 전세계 매출 4% 중 높은 금액 부과 가능. — ICO 공식 — High
- 실제 제재: TikTok 1,270만 파운드 (2024-04, 13세 미만 아동 개인정보 처리 관련 UK GDPR 5·8·12·13조 위반). — https://ico.org.uk 기반 요약 — High
- ICO는 2024~2025 우선순위로 기본 프라이버시·위치 설정, 아동 대상 광고 프로파일링, 추천 알고리즘, 13세 미만 정보 처리를 지목. 34개 소셜/동영상 플랫폼 표본 점검 진행. — Medium (2차 요약 출처)
- **적용 판단 기준이 COPPA보다 넓다:** Children's Code는 "아동이 서비스를 이용할 **가능성이 있는지(likely to be accessed by children)**"를 기준으로 하며, 반드시 "child-directed"가 아니어도 적용될 수 있다는 것이 알려진 특징이다(이 리서치에서 원문 조항까지 대조하지는 못함 — 이 경로로는 세부 확인 못 함, Medium).

### 3-2. EU GDPR 제8조 (아동 동의)

- 원칙: 16세 미만은 부모 동의 필요. 회원국이 13~16세 사이로 하향 조정 가능. 영국·스페인·아일랜드 등은 13세, 독일·네덜란드 등은 16세 유지. — https://gdpr-info.eu/art-8-gdpr/ — High
- 제8조는 **"아동을 명시적으로, 단독으로 또는 주로 대상으로 하는" 정보사회서비스**에만 적용. 서비스가 성인(18세 이상)만을 대상으로 명시하고 이를 다른 증거가 뒤엎지 않으면 제8조 적용 대상이 아니다. — Medium
- 실무: 부모 이메일 확인 등 "합리적 노력"으로 검증하면 되고, 미국 COPPA만�큼 엄격한 검증 방법 목록화는 없다. Medium

**결론:** 영국·EU는 미국보다 적용 범위가 넓고("접근 가능성" 기준) 제재 규모도 크다. 1인 개발자가 12주 POC 단계에서 이 두 법역까지 동시에 완벽 대응하는 것은 과잉이다. **미국 우선 출시 후, 영국·EU는 트래픽·매출 규모가 커진 뒤 순차 대응하는 전략을 권장.** 단, 이는 일정·리스크 관리 관점의 리서치 결론이지 법률 자문이 아니다.

---

## 4. 1인 개발자의 실무 부담 (세금·법인·고객대응)

### 4-1. 미국/영국 앱스토어 세무

- Apple·Google은 대부분 거래에서 **Merchant of Record**로 동작 — 구매자 소재지 기준 VAT/판매세를 자체적으로 계산·징수·납부한다. 개발자는 세전 판매가(수수료 차감 전)를 기준으로 순정산금을 받으며 별도 VAT 신고 불요. — https://appfigures.com/support/kb/616/how-vat-is-handled-by-apple-and-google-play — High
- 예외: 미국 일부 주는 경제적 넥서스(economic nexus) 기준 초과 시 개발자가 직접 등록·제로신고를 해야 하는 경우가 있음. — Medium
- 세금 양식: 비거주자(한국 등) 개인 개발자는 App Store Connect에서 **W-8BEN** 1회 제출(미국 원천징수세율 적용/조세조약 혜택 신청용). 법인은 W-8BEN-E. — https://developer.apple.com/help/app-store-connect/manage-tax-information/provide-tax-information/ — High

### 4-2. 법인 설립 필요 여부

- 미국·영국에 법인을 설립할 필요는 없음. 개인 개발자 자격으로 W-8BEN만 제출하면 Apple/Google 정산 가능. — High
- 한국 내부적으로는 별도 이슈: 애플 앱스토어 코리아는 전자상거래법 준수를 위해 개발자에게 **사업자등록번호(BRN)** 입력을 요구하며, 미입력 시 앱이 한국 스토어에서 비노출될 수 있다는 보고가 다수(커뮤니티 기반, 공식 확인은 약함). — https://www.clien.net/service/board/cm_app/14249370 , https://chitsol.com — Medium (1차 출처가 아니라 커뮤니티·블로그 종합)
- 부가세 처리: 개인(비사업자)은 부가세 신고 불가 — 사업자 등록이 필요. 초기 단계는 간이과세자(연 매출 8,800만원 미만) 등록이 일반적 경로이며, 온라인 등록은 당일 처리 가능해 12주 일정에 지장 없음. — https://ijemin.com/blog/... — Medium

### 4-3. 고객 문의 대응 의무

- 이 리서치에서 "법적으로 강제되는" 고객지원 SLA 규정은 찾지 못함(이 경로로는 못 찾았다). 다만 Apple/Google 개발자 계약상 문의 대응 채널(지원 이메일/URL) 게시는 앱 등록 요건이며, 이는 법적 의무라기보다 플랫폼 약관 준수 사항이다. Medium

**결론:** 세무·행정 부담은 12주 POC에 지장을 줄 정도는 아니다. 한국 사업자등록(간이과세자)만 선행하면 되고 이는 하루 안에 처리 가능. 법인 설립은 불필요.

---

## 5. 해외 아동 용돈 앱의 "구매 전 대기·쿨다운" 기능 확인

| 앱 | 확인 결과 | 신뢰도 |
|---|---|---|
| Greenlight | 초과 지출 시 부모에게 실시간 승인 요청을 보내는 구조. 부모가 즉시 응답하지 않으면 **결과적으로** 대기가 발생하지만, 이는 승인 게이트(approval gate)이지 의도된 숙려기간 기능이 아님. 투자(주식 매수) 요청에서 "6시간 대기 중 시세가 변동할 수 있다"는 설명이 있으나 이는 부작용 묘사이지 설계된 쿨다운이 아님. — https://help.greenlight.com/hc/en-us/articles/222235807 — Medium |
| Rooster Money (NatWest) | 카드 활성화 후 **14일 "cooling-off"**가 존재하나, 이는 계정/카드 해지에 관한 소비자보호법상 권리이며 구매 의사결정용 기능이 아님. 별도의 구매 전 대기·숙려 기능은 확인 안 됨. — https://roostermoney.com/payment-terms-and-conditions/ — Medium |
| Spriggy | 저축 목표(savings goal) 기능은 있으나, 목표 미달성 시 저축분을 쓰지 못하게 막는 정도. "구매 전 대기" 기능은 공식 자료에서 확인 안 됨. — Medium |
| Mydoh (RBC) | 주간 정산(Pay Day), 카드 잔액 한도 내 지출 등은 확인. 구매 전 대기·쿨다운 기능은 확인 안 됨. — Medium |
| BusyKid | 이번 검색 경로로는 구매 전 대기 기능 관련 정보를 찾지 못함 — **이 경로로는 못 찾았다.** 공식 기능 페이지 직접 대조가 필요. | Low (미확인) |
| Acorns Early (구 GoHenry) | 지출 알림, 카드 잠금, 카테고리 차단은 확인. 구매 전 대기·숙려 기능은 확인 안 됨. — Medium |

**종합 판단:** 조사한 6개 해외 제품 중 어느 곳도 "구매 전 대기·쿨다운·숙려기간"을 핵심 기능으로 명시하지 않았다. Rooster Money의 14일 쿨링오프는 소비자보호 규정이지 제품 기능이 아니므로 혼동하면 안 된다. **이 사업의 "멈추고 나누는 것을 가르친다"는 차별점은 확인된 선에서 해외에도 아직 없다.** 다만 이번 확인은 각 앱의 공식 웹페이지·헬프센터·앱스토어 설명 수준이며, 앱을 직접 설치해 UI를 뒤진 것은 아니다. BusyKid는 이 항목만 놓고 보면 확인 강도가 가장 약하다(Low). 사업 결정에 이 결론을 크게 의존한다면, 6개 앱을 실제로 설치해 확인하는 후속 조사를 권장.

---

## 확인하지 못한 것 (명시)

- VPC(검증 가능 부모 동의) 방법별 구체적 달러 비용 — 이 경로로는 못 찾았다.
- 한국 개발자의 애플 코리아 BRN 요구가 실제로 법적 강제인지, 아니면 플랫폼 정책인지 1차 출처(전자상거래법 조문 또는 애플 공식 고지)로 대조하지 못함 — 커뮤니티 소스에 의존.
- UK Children's Code의 "아동이 이용할 가능성" 기준 원문 조항 대조 — 시간 제약으로 요약 출처만 사용.
- BusyKid, Mydoh, Spriggy의 앱 내부 UI를 직접 설치해 "대기 기능 없음"을 스크린샷 수준으로 확인하지 못함 — 공식 웹/헬프센터 텍스트까지만 확인.
- 고객 문의 대응에 대한 법적 강제 규정(소비자보호법 등) — 이 경로로는 못 찾았다.

---

## 사용한 도구 예산

WebSearch 15건, WebFetch 1건. 한도(WebSearch 20 / WebFetch 20, 전체 툴 호출 60) 이내에서 종료.
