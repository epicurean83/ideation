# 팩트체크: 책 문장 소셜 주석 서비스 — 기술/법률/선례 (2026-09-22)

검색 예산: WebSearch 15건, WebFetch 2건 사용. 규칙대로 원문 요약만 여기 저장.

## 1. 선례 실패/종료

### Readmill (2014년 종료)
- Dropbox가 2014년 3월 인수(사실상 acquihire) 후 서비스 완전 종료. 신규 가입 즉시 중단, 2014년 7월 1일 앱 완전 폐쇄.
- 베를린 기반, 하이라이트·노트·공유·토론 기능의 소셜 리딩 앱. Adobe DRM 지원으로 Kobo/Nook 구매 도서를 읽을 수 있었음.
- Dropbox 목적은 인력·기술(HTML 리딩 경험, 분석, 동기화) 확보였고 서비스 자체 지속 의도 없었음.
- 신뢰도: High (다수 언론 보도 일치)
- 출처: https://www.androidpolice.com/2014/03/29/readmill-ebook-reader-and-service-shutting-down-after-dropbox-acquisition-data-export-available/ , https://thenextweb.com/news/readmill-acquired-dropbox-now-processs-closing-reading-platform-blog-post-company-said-joining-cloud-based-storage-provider-work-new-way (2014-03-29)

### Glose (2021년 Medium 인수, 이후 행방 불명확)
- 파리 기반 소셜 이북 플랫폼. 2021년 1월 Medium이 인수(금액 비공개). 인수 시점 이용자 100만 명 이상, 200개국, Penguin Random House/HarperCollins/Macmillan/Hachette/Simon&Schuster 등 대형 출판사 콘텐츠 취급.
- 인수 당시 "서비스 계속 운영, 종료 예정일 없음"으로 발표됨.
- 이후 실제 종료 여부는 검색 결과에서 확정하지 못함 — "확인 불가"(Medium이 2022년 별도 인수한 Projector는 종료됐으나 이는 Glose와 무관한 별개 서비스).
- 신뢰도: Medium (인수 사실은 High, 종료 여부는 확인 불가)
- 출처: https://techcrunch.com/2021/01/14/medium-acquires-social-book-reading-app-glose/ , https://sifted.eu/articles/glose-medium-acquisition (2021-01-14)

### Kindle Popular Highlights / Public Notes
- Popular Highlights(10명 이상이 같은 구절을 하이라이트하면 밑줄+인원수 표시)는 **폐지되지 않고 현재도 존재**하며 설정에서 껐다 켰다 가능. 위치는 세대별로 이동.
- 2025년 9월경 Amazon이 "My Notebook"에서 텍스트 선택·복사 기능을 제거했다는 언급 있음(하이라이트 자체는 유지). 11세대/12세대 Kindle에서 하이라이트/노트/사전 UI 변경.
- "Public Notes"(공개 프로필 공유) 자체의 폐지/축소 여부는 검색으로 확인 못함 — 확인 불가.
- 신뢰도: Medium
- 출처: https://www.bgr.com/2207377/popular-kindle-loopholes-that-amazon-killed/ , https://goodereader.com/blog/kindle/kindle-changes-how-highlighting-notes-and-definitions-work

### Goodreads Quotes
- 여전히 운영 중인 기능(종료 아님). 커뮤니티가 등록한 인용문에 "좋아요"로 인기도 표시. 최상위 인용문 예: "Don't cry because it's over..." 191,596 likes, 간디 인용 104,200 likes.
- 전체 인용문 수·활성 사용률 등 정량 규모는 확인 불가.
- 신뢰도: Medium
- 출처: https://blog.hptbydts.com/the-worlds-most-popular-quote-plus-70-of-the-most-liked-quotes-from-100-goodreads-pages

### Genius의 책 주석 시도
- Genius(옛 Rap Genius)는 랩 가사 해설에서 출발해 웹 전체 텍스트 주석(News Genius, genius.it 프리픽스, 임베드 주석)으로 확장을 시도한 바 있음.
- 책 전용 주석 기능이 별도로 "종료"되었다는 구체적 근거는 검색에서 찾지 못함 — 확인 불가. (News Genius 관련해서는 "Citation, Appropriation, and Fair Use" 등 저작권·표절 논란 기사가 존재해 확장 시도가 순탄치 않았음을 시사하나 정량 근거는 없음)
- 신뢰도: Low
- 출처: https://glog.glennf.com/blog/2016/3/25/citation-appropriation-and-fair-use

### Hypothesis (여전히 운영 중, 종료 아님)
- 2011년 비영리로 출발, 오픈소스. 2024년 10월 기준 누적 주석 6,500만 건 이상, 300개+ 기관 채택.
- 2022년 ITHAKA로부터 250만 달러 투자를 받아 공공이익법인(PBC) "Anno"를 설립해 스케일업 중 — 비영리 순수 모델에서 투자 유치형 하이브리드로 전환.
- 신뢰도: High
- 출처: https://www.nature.com/articles/d41586-019-01427-9 , https://www.infodocket.com/2022/08/18/ithaka-announces-2-5-million-investment-to-open-annotation-provider-hypothesis/ (2024-10 활동 근거: newswire 기사들)

## 2. 한국어 OCR

### Tesseract / Tesseract.js 한국어 정확도
- 다수의 한국 개발자 후기(velog 등)에서 "한글 인식률이 기대에 못 미친다"는 공통 평가. 원인: (1) 한글 학습 데이터셋 자체가 영어 대비 적음, (2) 자동 전처리가 없어 저품질 이미지에서 인식률 급락, (3) 한글+영문+숫자 혼재 구간 오류 다발, (4) 세로쓰기는 사실상 인식 불가.
- 정량 벤치마크(정확도 %) 수치는 신뢰할 출처를 찾지 못함 — 확인 불가. 정성적 평가만 확보.
- 신뢰도: Medium (다수 개발자 블로그 일치하나 학술적 벤치마크 아님)
- 출처: https://velog.io/@agugu95/Tesseract-OCR , https://www.lido.app/kr/hangugeo-ocr , https://gseok.github.io/tech-talk-2022/2022-12-14-tesseract/

### iOS Live Text 한국어 지원
- Live Text는 한국어를 포함해 영어, 중국어, 프랑스어, 독일어, 스페인어, 이탈리아어, 포르투갈어, 일본어, 우크라이나어를 지원.
- 기기 요건: iPhone XS/XR 이상 + iOS 15 이상(정지 이미지). 동영상 Live Text는 iOS 16 이상 필요.
- iOS 15는 2021년 9월 출시 — 한국어 Live Text 지원은 그 시점부터로 추정되나, "한국어가 최초 출시(iOS 15)부터 지원됐는지 이후 업데이트로 추가됐는지"는 Apple 공식 문서에서 명확한 버전별 언어 추가 이력을 확인하지 못함. 신뢰도 Medium.
- 출처: https://support.apple.com/guide/iphone/live-text-interact-content-a-photo-video-iph37fdd714b/ios , https://support.apple.com/en-us/120004

### Android Google Lens 한국어 지원
- Google Lens는 200개 이상 언어의 텍스트 인식을 지원하며 한국어도 포함된다고 명시됨(무료). Android 기본 카메라 앱, Google Photos, iOS Google 앱에 내장.
- 다만 "복잡한 레이아웃의 한국어 문서에서는 한국어 특화 모델 대비 정확도가 낮을 수 있다"는 서술 있음(출처 신뢰도 낮은 블로그성 자료).
- Google Lens가 한국어 지원을 "언제부터" 시작했는지(최초 버전) 특정하는 공식 출처는 찾지 못함 — 확인 불가.
- 신뢰도: Low~Medium
- 출처: https://www.lido.app/kr/image-text-chuchul , https://ko.a7la-home.com/use-google-lens-to-copy-text-from-image/

## 3. Supabase / Cloudflare R2 가격

### Supabase Pro 플랜 MAU (공식 문서로 확인, WebFetch)
- Pro 플랜 기본료: $25/월(첫 프로젝트 포함)
- 포함 MAU: **100,000명** (조직 단위로 풀링, Pro/Team 공통)
- 초과 요금: **$0.00325 / MAU**
- 100만 MAU 가정 시 Auth 비용 추정: (1,000,000 − 100,000) × $0.00325 = **$2,925/월** (기본료 $25 별도 → 합계 약 $2,950/월 ≈ 약 410만 원/월, 환율 1,400원/달러 가정 [Assumption])
- 신뢰도: High (Supabase 공식 문서 직접 확인, 2026-09-22 fetch)
- 출처: https://supabase.com/docs/guides/platform/manage-your-usage/monthly-active-users

### Cloudflare R2 가격
- Standard 스토리지: $0.015/GB-월, Infrequent Access: $0.01/GB-월
- Class A 오퍼레이션(쓰기 등): $4.50/백만 건 (Standard), IA는 $9.00/백만 건
- Class B 오퍼레이션(읽기 등): $0.36/백만 건 (Standard), IA는 $0.90/백만 건 + $0.01/GB 검색비용
- Egress(트래픽) 무료 — R2 최대 강점
- 무료 티어: 10GB-월 스토리지, Class A 100만 건, Class B 1,000만 건, egress 무료
- 신뢰도: Medium (다수 3자 요약 블로그 근거, Cloudflare 공식 페이지는 검색결과 목록에만 잡히고 직접 fetch는 안 함 — 필요시 재확인 권장)
- 출처: https://egresscost.com/cloudflare/ , https://filebase.com/blog/cloudflare-r2-pricing-costs-savings-and-alternatives-in-2026/

## 4. 한국 저작권법 — 책 문장 인용 이미지 대량 저장/공개

### 법 조문
- **제28조(공표된 저작물의 인용)**: 보도·비평·교육·연구 등을 위해 "정당한 범위 안에서 공정한 관행에 합치되게" 인용 가능. 출처 명시 의무. 공표되지 않은 저작물 인용 시 공표권 침해 소지.
- **제35조의5(저작물의 공정한 이용)**: 포괄적 공정이용 조항. 저작물의 통상적 이용 방식과 충돌하지 않고 저작자의 정당한 이익을 부당하게 해치지 않는 경우 허락 없이 이용 가능. 제28조와의 관계(보충성)는 학계에서 논의 중인 주제.
- 신뢰도: High (국가법령정보센터·이지로 정부 사이트 기반)
- 출처: https://easylaw.go.kr/CSP/CnpClsMain.laf?popMenu=ov&csmSeq=695&ccfNo=3&cciNo=2&cnpClsNo=2 , https://www.law.go.kr/lsEfInfoP.do?lsiSeq=148848

### 쟁점 (본 서비스에 대한 적용, [Assumption]으로 추론 — 법률 자문 아님)
- "문장 → 타이포 카드 → SNS 공유 → DB에 영구 저장·공개 열람"은 일회적 비평·인용이 아니라 **대량·반복적으로 원문 발췌를 이미지화해 서비스 핵심 콘텐츠로 축적**하는 구조라, 제28조의 "정당한 범위" 요건(양적 종속성, 인용의 부수성)을 충족하는지 불확실함. 제35조의5 포괄적 공정이용도 "저작물의 통상적 이용 방식과 충돌하지 않을 것"을 요구하는데, 카드 이미지가 SNS에서 유통되며 실질적으로 "책을 안 사도 되는 대체재"처럼 작동할 경우 이 요건과 충돌 가능성이 있음. — 이 판단은 확인된 사실이 아니라 추론이며, 실제 결론은 변호사 자문이나 판례 확인이 필요함.

### 국내 유사 사례
- 직접적으로 "출판사가 문장 카드/인용 앱에 문제 제기한 국내 사례"는 검색으로 찾지 못함 — **확인 불가**.
- 인접 사례로 국립국어원의 문어 빅데이터 서비스가 출판사 측 저작권 문제 제기로 중단된 사례가 있음(TDM 데이터 수집·제공 단계의 저작권 문제). 이는 텍스트마이닝 목적이라 본 서비스(소셜 주석 카드)와는 성격이 다르지만, "출판사가 대량 텍스트 수집·재공개에 문제를 제기해 서비스가 중단된 선례가 국내에 존재한다"는 점에서 참고할 근거는 됨.
- 신뢰도: Low~Medium (2차 요약 자료, 원 판결문·기사 미확인)
- 출처: https://www.moj.go.kr/bbs/moj/166/450511/download.do (TDM 면책규정 논단, 국립국어원 사례 언급)

## 5. 상업용 한글 세리프 폰트 — 웹앱 이미지 생성 서비스 라이선스

### 산돌구름 (Sandoll Cloud)
- 2020년 4월부터 인쇄/출판/영상 등 용처 구분을 없애고 "사용범위 제한 없는" 통합 라이선스로 전환했다는 정보 확인(출처: 나무위키/위키백과 요약, 1차 공식 자료 미확인).
- 과거 개인 구독형으로 월 9,900원에 365종 폰트 무제한 사용 요금제가 있었다는 언급(시점 불명).
- **비즈니스/기업 요금제의 정확한 가격, 그리고 "웹앱에서 사용자 요청마다 이미지 생성에 폰트 임베딩"하는 서비스에 필요한 라이선스 종류·가격은 웹페이지 구조상(스토어가 브랜드별 하위 페이지로 분기) 확인 불가.** 직접 문의(1688-4001) 또는 견적 요청 필요.
- 신뢰도: Low (가격 미확인)
- 출처: https://ko.wikipedia.org/wiki/%EC%82%B0%EB%8F%8C%EA%B5%AC%EB%A6%84 , https://www.sandollcloud.com/store (2026-09-22 fetch, 가격 미기재)

### 윤디자인 (YoonDesign) / FONCO
- 폰코(FONCO) 클라우드 서비스는 "로그인 한 번으로" 사용 가능한 구독형 라이선스 모델 제공(다운로드 불필요).
- 윤멤버십 연 결제 가격대: White 88,000원 / Red 286,000원 / Black(가격 미확인) — 등급별로 라이선스 범위·폰트 종수 차등.
- 대한체 등 일부 폰트는 무료로 인쇄·출판·영상·웹·모바일 전 매체 상업적 사용 가능.
- **웹폰트 임베딩(웹앱에 폰트 파일을 직접 넣어 서버사이드/클라이언트사이드 렌더링하는 용도) 전용 라이선스의 구체적 가격은 검색으로 확인 불가.** font.co.kr 직접 문의 필요.
- 신뢰도: Low~Medium (연 멤버십 가격은 확인, 웹폰트 임베딩 전용 가격은 확인 불가)
- 출처: https://font.co.kr/policy/license , https://yoondesign.com/font

## 요약 — 확인 못 한 항목 목록
- Glose 서비스 현재 생존 여부
- Kindle Public Notes(공개 프로필) 폐지 여부
- Genius 책 주석 기능 종료 사실 여부
- Tesseract.js 한국어 정량 정확도(%) 벤치마크
- iOS Live Text/Android Google Lens 한국어 지원 "최초 시작 버전" 정확한 시점
- Cloudflare 공식 가격 페이지 1차 확인(3자 요약만 사용)
- 국내에서 출판사가 문장카드/인용 앱에 실제로 문제제기한 사례
- 산돌구름 비즈니스 요금제 정확 가격, 웹앱 폰트 임베딩 라이선스 가격
- 윤디자인 웹폰트 임베딩 전용 라이선스 가격
