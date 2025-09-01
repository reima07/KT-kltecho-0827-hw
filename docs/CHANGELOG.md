# CHANGELOG - 0827_hw 프로젝트

## 📋 프로젝트 개요
- **목표**: Full-stack 웹 애플리케이션을 로컬 Rancher Desktop Kubernetes에 배포 후 Azure로 CI/CD
- **기술 스택**: Python Flask (Backend) + Vue.js (Frontend) + MariaDB + Redis + Kafka
- **현재 상태**: 로컬 K8s에서 완전히 동작 중

---

## 📅 주요 변경사항 (시간순)

### [2025-09-01] - OpenTelemetry 통합 완료 및 코드 정리 ✅
- **목표**: OpenTelemetry를 통한 구조화된 로깅 및 트레이싱 구현
- **완료된 작업**:
  - Flask 자동 계측 활성화 (`FlaskInstrumentor`)
  - PyMySQL 자동 계측 활성화 (`PyMySQLInstrumentor`)
  - Redis 자동 계측 활성화 (`RedisInstrumentor`)
  - OTLP HTTP 익스포터 설정 (포트 4318)
  - 로그-트레이스 연동 (trace_id, span_id 포함)
  - **코드 정리**: 수동 트레이스 제거, 자동 계측만 사용
  - **보안 강화**: 사용자별 메시지 필터링 추가 (`WHERE user_id = %s`)
  - **인증 복원**: `@login_required` 데코레이터 정상화, 실제 사용자 ID 사용
- **해결된 문제들**:
  - pymysql 모듈 누락으로 인한 CrashLoopBackOff
  - Flask application context 오류
  - `@login_required` 데코레이터로 인한 트레이스 미생성
  - Redis LTRIM만 보이는 문제
  - **들여쓰기 오류** (IndentationError) 수정
  - **"test_user" 하드코딩** 제거
- **결과**: 완전한 트레이스 체인 생성 (Flask → DB → Redis), 실제 사용자별 데이터 분리

### [2025-08-31] - Promtail 설치 및 로그 수집 완료 ✅
- **문제**: 145 AKS의 Pod 로그가 144 AKS의 Grafana Loki로 전송되지 않는 문제
- **해결**: 
  - Promtail 설치로 Kubernetes Pod 로그 자동 수집
  - Loki 엔드포인트 설정으로 원격 로그 전송
  - 서비스명 라벨링으로 로그 구분 가능
- **결과**: 이제 Grafana Loki에서 `jiwoo-backend`와 `jiwoo-frontend` 로그 확인 가능

### [2025-08-31] - OpenTelemetry 에러 수정 ✅
- **문제**: 프론트엔드에서 `SpanStatusCode` 관련 에러 발생
- **해결**: 
  - `@opentelemetry/api`에서 `SpanStatusCode` import 추가
  - `trace.SpanStatusCode` → `SpanStatusCode`로 수정
- **결과**: 프론트엔드 OpenTelemetry 정상 작동

### [2025-08-31] - 카프카 로그 문제 최종 해결 ✅
- **문제**: Redis에서 예전 로그만 표시되고 새로운 로그가 생성되지 않는 문제
- **해결**: 
  - `async_log_api_stats` 함수 단순화 (복잡한 로깅 구조 제거)
  - Redis 로그 관리 개선 (최신 50개만 조회)
  - Kafka 관련 코드 제거하여 안정성 향상
- **결과**: `jiwoo2` 사용자 로그인 후 새로운 API 호출 로그가 정상적으로 생성되고 표시됨

### [2025-08-31] - API 엔드포인트 수정 및 서비스명 로깅 개선 ✅
- **문제**: 프론트엔드에서 `/api/logs/kafka` 호출 시 404 에러 발생
- **해결**: 
  - 백엔드 모든 엔드포인트에 `/api` 프리픽스 추가
  - nginx 설정에서 rewrite 규칙 제거
  - 로깅에 `service_name` 필드 추가
- **결과**: 프론트엔드-백엔드 API 호출 정상화, Grafana에서 서비스명 구분 가능

### [2025-08-31] 🔧 카프카 로그 조회 문제 해결 및 프론트엔드 개선

#### 🔧 수정사항
- **카프카 로그 조회 문제 해결**
  - 카프카 SASL 인증 제거 (인증 없이 평면 연결 사용)
  - Redis를 통한 카프카 로그 저장 구현 (이중 저장 방식)
  - 카프카 연결 실패 시에도 Redis에서 로그 조회 가능
  - 토픽 자동 생성 로직 개선

- **프론트엔드 표시 개선**
  - 카프카 로그 표시 형식 수정 (`log.action`, `log.details` → `log.method`, `log.endpoint`, `log.message`)
  - MariaDB 메시지 표시를 최근 10개로 제한
  - 모든 로그/메시지 표시에 일관된 10개 제한 적용

#### 🐛 버그 수정
- 카프카 로그 조회 시 빈 배열 반환 문제 해결
- 프론트엔드에서 카프카 로그가 표시되지 않는 문제 해결
- 메시지 목록이 너무 많이 표시되는 문제 해결

#### 📝 기술적 개선사항
- **이중 저장 방식**: 카프카 + Redis 동시 저장으로 안정성 향상
- **에러 처리 강화**: 카프카 연결 실패 시에도 Redis에서 로그 조회 가능
- **사용자 경험 개선**: 모든 목록을 최근 10개로 제한하여 가독성 향상

#### 🔄 배포 과정
1. 백엔드 코드 수정 (카프카 인증 제거, Redis 이중 저장)
2. 프론트엔드 코드 수정 (표시 형식 수정, 10개 제한)
3. GitHub Actions를 통한 자동 빌드 및 ACR 푸시
4. Kubernetes 롤아웃 재시작으로 새로운 이미지 배포

---

### [2025-08-30] 🏗️ 초기 프로젝트 설정

#### ✨ 신규 기능
- **마이크로서비스 아키텍처 구축**
  - Frontend: Vue.js + Nginx
  - Backend: Python Flask
  - Database: MariaDB
  - Cache: Redis
  - Message Queue: Apache Kafka

- **Kubernetes 배포 환경**
  - Helm을 통한 Kafka, MariaDB, Redis 설치
  - LoadBalancer 서비스를 통한 외부 접근
  - 자동화된 초기화 Job

- **CI/CD 파이프라인**
  - GitHub Actions를 통한 자동 빌드
  - Azure Container Registry (ACR) 연동
  - Docker 이미지 자동 푸시

#### 🔐 인증 시스템
- 사용자 회원가입/로그인 기능
- 세션 기반 인증
- Redis를 통한 세션 관리

#### 📊 로깅 시스템
- Redis를 통한 API 호출 로그 저장
- Kafka를 통한 API 통계 로그 저장
- 실시간 로그 조회 기능

#### 🔍 검색 기능
- MariaDB 메시지 검색
- 페이지네이션 지원
- 사용자별 메시지 관리

---

### [2025-08-29] 🚀 프로젝트 초기화

#### 🚀 프로젝트 시작
- Kubernetes 학습을 위한 마이크로서비스 프로젝트 생성
- Azure 클라우드 환경에서 CI/CD 구축 목표
- 개발자: Jiwoo
- 목적: Kubernetes와 Azure 클라우드 기술 학습

---

## 🔧 해결된 문제들

### 1. ImagePullBackOff / 401 Unauthorized 오류
**문제**: ACR 인증 설정 누락으로 인한 이미지 Pull 실패
**해결**: ACR Secret 생성 및 배포 파일에 `imagePullSecrets` 추가
**결과**: ✅ ACR에서 이미지 정상 Pull

### 2. GitHub Push Protection 차단
**문제**: 평문 비밀번호가 포함된 파일 푸시 시 차단
**해결**: base64 인코딩 사용 및 Git 히스토리 리셋
**결과**: ✅ 보안 정책 준수하며 푸시 성공

### 3. 프론트엔드 외부 접속 불가
**문제**: NodePort 서비스로는 외부 접속 불가
**해결**: 서비스 타입을 LoadBalancer로 변경
**결과**: ✅ 외부에서 프론트엔드 접속 가능

### 4. 리소스 부족 오류
**문제**: `Insufficient cpu` 오류로 인한 Pod 스케줄링 실패
**해결**: CPU/메모리 요청량 최적화
**결과**: ✅ 리소스 효율적 사용

### 5. 데이터베이스 연결 문제
**문제**: `Unknown database 'testdb'` 오류
**해결**: 환경변수로 데이터베이스 이름 변경 (`jiwoo_db`)
**결과**: ✅ MariaDB 정상 연결

### 6. 테이블 없음 문제
**문제**: `Table 'jiwoo_db.users' doesn't exist`
**해결**: 자동화된 초기화 Job 생성
**결과**: ✅ 자동 초기화 완료

### 7. Kafka CrashLoopBackOff
**문제**: 컨트롤러 수 불일치 및 SASL 인증 문제
**해결**: 컨트롤러 수 조정 및 SASL 인증 비활성화
**결과**: ✅ Kafka 정상 작동

### 8. 사용자 정보 미저장 문제
**문제**: 메시지 저장 시 "사용자 없음" 표시
**해결**: SQL 쿼리에 `user_id` 추가
**결과**: ✅ 사용자별 메시지 관리 가능

### 9. 배포 시간 최적화
**문제**: 300초 타임아웃으로 인한 긴 배포 시간
**해결**: 120초/60초로 최적화
**결과**: ✅ 효율적인 배포 시간

---

## 📊 현재 상태

### 접속 정보
- **프론트엔드**: http://4.230.144.92
- **백엔드 API**: 내부 클러스터에서만 접근 가능 (포트 5000)

### 서비스 상태
- ✅ Frontend: Running (LoadBalancer)
- ✅ Backend: Running (ClusterIP)
- ✅ MariaDB: Running
- ✅ Redis: Running
- ✅ Kafka: Running (3개 컨트롤러)
- ✅ 초기화 Job: Completed

### 주요 기능
- ✅ 로그인/회원가입
- ✅ 메시지 저장 (사용자 정보 포함)
- ✅ 메시지 검색
- ✅ Redis 로그 조회
- ✅ Kafka API 통계 로깅 (Redis 기반)

### CI/CD 파이프라인
- ✅ GitHub Actions 워크플로우
- ✅ Azure Container Registry 연동
- ✅ 자동 빌드 및 푸시

---

## 🚀 다음 단계 (CI/CD)

1. **Git 저장소 설정** ✅
2. **GitHub Actions 워크플로우 생성** ✅
3. **Azure Container Registry 설정** ✅
4. **Azure Kubernetes Service 배포** (예정)

---

## 📝 학습 내용

### Kubernetes 개념
- **Job vs Deployment**: 일회성 작업 vs 지속적 서비스
- **서비스 디스커버리**: 내부 DNS를 통한 서비스 연결
- **Helm**: 패키지 매니저를 통한 인프라 관리

### 아키텍처 패턴
- **마이크로서비스**: 독립적인 서비스 구성
- **API Gateway**: Nginx를 통한 프록시
- **이벤트 기반**: Kafka를 통한 비동기 로깅

### 자동화
- **초기화 자동화**: Job을 통한 DB/Redis 초기화
- **배포 자동화**: 스크립트를 통한 일관된 배포
- **타임아웃 최적화**: 효율적인 배포 시간 관리
- **CI/CD 자동화**: GitHub Actions를 통한 Azure 클라우드 배포

---

## 📁 프로젝트 구조 (최종)

```
0827_hw/
├── backend/                    # Flask 백엔드
│   ├── app.py                 # 메인 애플리케이션
│   ├── requirements.txt       # Python 의존성
│   └── Dockerfile            # 백엔드 이미지
├── frontend/                  # Vue.js 프론트엔드
│   ├── src/                  # 소스 코드
│   ├── package.json          # Node.js 의존성
│   ├── nginx.conf           # Nginx 설정
│   └── Dockerfile           # 프론트엔드 이미지
├── db/                       # 데이터베이스
│   └── init.sql             # 초기화 스크립트
├── k8s/                      # Kubernetes 배포 파일
│   ├── jiwoo-*-deployment.yaml  # 애플리케이션 배포
│   ├── jiwoo-*-secret.yaml      # 시크릿 설정
│   ├── jiwoo-*-init-job.yaml    # 초기화 Job
│   └── *-values.yaml           # Helm 차트 설정
├── .github/workflows/        # GitHub Actions 워크플로우
│   └── build-and-push.yml   # Docker 빌드 및 ACR 푸시
├── docs/                    # 문서화
│   ├── CHANGELOG.md         # 변경사항 기록 (이 파일)
│   ├── deployment-issues.md # 배포 문제 해결 가이드
│   └── PROJECT_HISTORY.md   # 전체 진행 과정
├── deploy-to-jiwoo-namespace.sh    # 배포 스크립트
├── cleanup-jiwoo-namespace.sh      # 정리 스크립트
└── README.md               # 기본 문서
```

---

## 🔗 링크

- **GitHub 저장소**: https://github.com/reima07/KT-kltecho-0827-hw
- **개발자**: Jiwoo
- **목적**: Kubernetes 학습 및 Azure CI/CD 구축

---

**이 프로젝트는 Kubernetes와 Azure 클라우드 기술을 학습하기 위한 실습 프로젝트입니다.**
