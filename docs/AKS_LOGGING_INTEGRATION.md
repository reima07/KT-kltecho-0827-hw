## 📝 진행 기록

### [2025-08-31] - 1단계: OpenTelemetry 의존성 추가 ✅
- [x] **백엔드 의존성 추가**
  - `requirements.txt`에 OpenTelemetry 라이브러리 추가
  - `opentelemetry-api`, `opentelemetry-sdk` 추가
  - `opentelemetry-instrumentation-*` 라이브러리들 추가
  - `opentelemetry-exporter-otlp-*` 라이브러리들 추가

- [x] **프론트엔드 의존성 추가**
  - `package.json`에 OpenTelemetry 라이브러리 추가
  - `@opentelemetry/api`, `@opentelemetry/sdk-web` 추가
  - `@opentelemetry/instrumentation-*` 라이브러리들 추가
  - `@opentelemetry/exporter-otlp-http` 추가

- [x] **백엔드 설정 파일 생성**
  - `backend/telemetry.py`: OpenTelemetry 설정 및 초기화
  - `backend/logging_config.py`: 구조화된 JSON 로깅 설정
  - Collector 엔드포인트: `http://collector.lgtm.20.249.154.255.nip.io`

- [x] **프론트엔드 설정 파일 생성**
  - `frontend/src/telemetry.js`: OpenTelemetry 설정 및 초기화
  - 자동 계측: Document Load, User Interaction, Fetch
  - 커스텀 추적 함수: API 호출, 사용자 액션, 페이지 뷰

### [2025-08-31] - 4단계: Collector 연동 테스트 🔄
- [x] **버전 호환성 수정**
  - 백엔드: Python 3.8 호환 OpenTelemetry 라이브러리 버전으로 수정
    - `opentelemetry-api==1.20.0`, `opentelemetry-sdk==1.20.0`
    - `opentelemetry-instrumentation-*==0.42b0`
    - Kafka instrumentation 제거 (수동 추적으로 대체)
  - 프론트엔드: Vue.js 2.6 호환 OpenTelemetry 라이브러리 버전으로 수정
    - `@opentelemetry/api==1.4.1`, `@opentelemetry/sdk-web==0.33.0`
    - `@opentelemetry/instrumentation-*==0.33.0`

- [ ] **새로운 이미지 빌드 및 배포**
- [ ] **Collector 연결 테스트**
- [ ] **로그 및 트레이스 데이터 확인**

### [2025-08-31] - 3단계: 프론트엔드 로깅 코드 구현 ✅
- [x] **OpenTelemetry 초기화**
  - `frontend/src/main.js`에 OpenTelemetry 초기화 추가
  - `frontend/src/telemetry.js` 설정 파일 활용

- [x] **사용자 행동 추적**
  - 모든 버튼 클릭에 `@click.native="trackUserAction()"` 추가:
    - 로그인/회원가입 버튼
    - DB 저장/조회 버튼
    - 로그 조회 버튼
    - 검색 버튼
    - 로그아웃 버튼

- [x] **API 호출 추적**
  - 주요 API 호출 메서드에 응답 시간 측정 추가:
    - `saveToDb()`: DB 저장 API 호출 추적
    - `login()`: 로그인 API 호출 추적
  - 성공/실패 상태 및 응답 시간 기록

- [x] **페이지 뷰 추적**
  - `mounted()` 훅에 페이지 뷰 추적 추가
  - 앱 초기 로딩 시 자동 추적

- [x] **추적 메서드 구현**
  - `trackUserAction()`: 사용자 액션 추적
  - `trackApiCall()`: API 호출 성능 추적
  - OpenTelemetry와 연동하여 Collector로 전송

- [x] **Kubernetes 환경변수 추가**
  - `k8s/jiwoo-frontend-deployment.yaml`에 OpenTelemetry 환경변수 추가:
    - `VUE_APP_OTEL_EXPORTER_OTLP_ENDPOINT`: Collector 엔드포인트
    - `VUE_APP_OTEL_SERVICE_NAME`: 서비스 이름
    - `VUE_APP_OTEL_RESOURCE_ATTRIBUTES`: 리소스 속성

### [2025-08-31] - 2단계: 백엔드 로깅 코드 구현 ✅
- [ ] 4단계: Collector 연동 테스트
- [ ] 5단계: Grafana에서 데이터 확인
