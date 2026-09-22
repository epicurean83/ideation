# POC 범위 정의서 (POC Scope - S3)

## 1. POC의 핵심 목적
> **"1인이 12주 안에 기성 부품으로 구현하여, 데스크 리서치 추정치를 '실사용 데이터'로 교체하고 핵심 가설을 검증한다."**

## 2. 검증할 3대 핵심 가설 (Core Assumptions)
1. **바이럴 가설**: 사용자가 생성한 감성 타이포 카드를 실제로 인스타그램 스토리나 스레드에 업로드하여 자발적 오가닉 유입($K > 1.0$)이 발생하는가?
2. **리텐션 가설**: 문장 단위의 소셜 마진(주석)과 무음 독서방이 텍스트힙 유저의 W4 리텐션($\ge 25\%$)을 견인하는가?
3. **원가 가설**: 브라우저 온디바이스(Wasm/Canvas) 연산으로 실제 사용자 1인당 월 인프라 원가가 $5\text{원}$ 이하(CPU_월 $\le 30\text{원}$)로 유지되는가?

---

## 3. 포함 범위 (In-Scope - 12주 내 구현 대상)

| 모듈 | 세부 기능 명세 | 기술 스택 |
|---|---|---|
| **M1. Typo-Card Engine** | • 카메라 촬영/이미지 업로드 $\rightarrow$ 브라우저 OCR (Tesseract.js)<br>• 1:1(스레드/피드) 및 9:16(인스타 스토리) 규격 캔버스 렌더링<br>• 고급 세리프 폰트 4종 및 여백/종이 질감 템플릿 3종<br>• 워터마크 & 딥링크 QR 자동 각인 및 이미지 내보내기 | HTML5 Canvas, Tesseract.js, Lucide Icons |
| **M2. Social Margin Core** | • 소셜 간편 로그인 (카카오, Google)<br>• 문장 등록 및 특정 문장별 포스트잇 주석(Margin Note) CRUD<br>• 공감(좋아요) 및 딥링크 착륙 페이지 (SEO 오픈그래프 지원) | Next.js App Router, Supabase Auth & PostgreSQL |
| **M3. Book Discovery & Vibe** | • 알라딘 Open API 도서 검색 및 ISBN 메타데이터 Edge KV 캐싱<br>• 감정/상황별 Vibe 태그 필터링 (`#새벽2시`, `#도파민디톡스` 등) | Cloudflare Workers KV, 알라딘 Open API |
| **M4. Silent Reading Room** | • 뽀모도로 무음 독서 타이머 (25분 집중 / 5분 휴식)<br>• 현재 접속자 수 및 읽고 있는 책 표지 실시간 공유<br>• 세션 종료 시 '오늘의 문장 1줄' 등록 연동 | Supabase Realtime, LocalStorage Timer |
| **M5. PWA & 모니터링** | • 모바일 반응형 웹 앱 + 홈 화면 추가(PWA) 지원<br>• 3회 신고 시 자동 블라인드 규칙 + Sentry 에러 트래킹 | PWA Manifest, Sentry, Tailwind CSS |

---

## 4. 제외 범위 (Out-of-Scope - 스코프 컷)

* ❌ **모바일 네이티브 앱 (iOS/Android 스토어 등록)**: 심사 지연 및 1인 개발 공수 절감을 위해 PWA 모바일 웹으로 완결.
* ❌ **서버 생성형 AI/LLM 추천 엔진**: 고비용 API 배제 원칙에 따라 무드 태그 기반 통계 정렬로 대체.
* ❌ **유료 PG 결제 모듈**: POC 단계에서는 전 기능 무료 개방. 결제 의향은 '프리미엄 폰트 잠금 해제 클릭 시 사전 신청 모달(Fake Door Test)'로 검증.
* ❌ **출판사/작가 전용 B2B 포털**: 초기 1~2건 제휴는 구글 폼 및 수동 온보딩으로 대응.
