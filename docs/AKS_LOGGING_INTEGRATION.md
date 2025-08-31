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

### [2025-08-31] - 4단계: Collector 연동 테스트 ✅
- [x] **새로운 이미지 빌드 및 배포**
  - 백엔드: OpenTelemetry 통합 완료, 구조화된 로깅 구현
  - 프론트엔드: 최신 OpenTelemetry 통합, Node 20 업그레이드
  - 옵셔널 체이닝 문제 해결로 빌드 성공

- [x] **롤아웃 완료**
  - `kubectl rollout restart deployment/jiwoo-backend -n jiwoo` ✅
  - `kubectl rollout restart deployment/jiwoo-frontend -n jiwoo` ✅
  - 새로운 Pod들이 성공적으로 실행 중

- [x] **OpenTelemetry 초기화 확인**
  - 백엔드 로그: "OpenTelemetry 설정 완료 - Collector: http://collector.lgtm.20.249.154.255.nip.io"
  - 로깅 설정: "로깅 설정 완료 - 레벨: INFO"
  - Flask 앱 정상 실행 중

- [ ] **실제 로그 및 트레이스 데이터 확인** (다음 단계)
- [ ] **Grafana에서 데이터 확인** (다음 단계)

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

### [2025-08-31] - 5단계: API 엔드포인트 수정 및 서비스명 로깅 개선 ✅
- [x] **API 엔드포인트 수정**
  - 백엔드 모든 엔드포인트에 `/api` 프리픽스 추가
  - 프론트엔드 호환성 문제 해결
  - `/logs/kafka` → `/api/logs/kafka` 등 모든 엔드포인트 수정

- [x] **서비스명 로깅 개선**
  - 백엔드: `logging_config.py`에 `service_name` 필드 추가
  - 프론트엔드: 사용자 액션 추적에 구조화된 로깅 추가
  - Loki에서 `service_name` 라벨로 서비스 구분 가능

- [x] **새로운 이미지 빌드 및 배포**
  - GitHub Actions를 통한 자동 빌드/배포
  - 백엔드: `jiwoo-backend:v1.0.2`
  - 프론트엔드: 최신 버전

- [ ] **Grafana에서 로그 확인** (다음 단계)
  - Loki에서 `service_name="jiwoo-backend"` 및 `service_name="jiwoo-frontend"` 확인
  - 구조화된 로그 형태로 데이터 수집 확인

### [2025-08-31] - 6단계: 카프카 로그 문제 최종 해결 ✅
- [x] **문제 진단**
  - Redis에서 예전 로그들만 계속 표시되는 문제
  - `jiwoo2` 사용자 로그인 후 새로운 로그가 생성되지 않는 문제
  - `async_log_api_stats` 함수에서 에러 발생

- [x] **Redis 로그 관리 개선**
  - 백엔드에서 최신 로그 50개만 가져오도록 수정 (`lrange('kafka_logs', -50, -1)`)
  - Redis의 `kafka_logs` 초기화로 오래된 로그 제거

- [x] **async_log_api_stats 함수 단순화**
  - 복잡한 로깅 구조로 인한 에러 해결
  - Kafka 관련 코드 제거 (Redis만 사용)
  - 간단한 `print` 문으로 디버깅 개선

- [x] **최종 테스트 완료**
  - `jiwoo2` 사용자 로그인 성공
  - DB 메시지 저장 시 새로운 로그 생성 확인
  - 카프카 로그 조회에서 최신 로그 정상 표시

### [2025-08-31] - 7단계: Promtail 설치 및 로그 수집 완료 ✅
- [x] **문제 진단**
  - 145 AKS의 Pod 로그가 144 AKS의 Grafana Loki로 전송되지 않는 문제
  - Promtail이 설치되지 않아서 로그 수집이 안됨

- [x] **Promtail 설치**
  - Grafana Helm 차트 저장소 추가
  - Promtail 설치: `helm install promtail grafana/promtail --namespace jiwoo`
  - Loki 엔드포인트 설정: `http://collector.lgtm.20.249.154.255.nip.io/loki`

- [x] **로그 수집 설정**
  - Kubernetes Pod 자동 발견
  - 서비스명 라벨링 (`service_name`)
  - 구조화된 JSON 로그 수집

- [x] **최종 테스트**
  - 프론트엔드/백엔드 롤아웃 완료
  - Promtail DaemonSet 실행 중
  - Grafana Loki에서 로그 확인 준비 완료

### [2025-08-31] - 8단계: Grafana 로그 확인 (최종 단계)
- [ ] **Grafana Loki에서 로그 확인**
  - `service_name="jiwoo-backend"` 및 `service_name="jiwoo-frontend"` 확인
  - 구조화된 JSON 로그 형태로 데이터 수집 확인
  - 사용자 액션 로그 확인

- [ ] **Grafana Tempo에서 트레이스 확인**
  - API 호출 트레이스 확인
  - 서비스 간 연결 관계 확인
