# Jiwoo Backend API

FastAPI 기반 회원가입/로그인/CRUD 서비스 with OpenTelemetry 모니터링

## 🚀 기능

- **인증**: 회원가입, 로그인 (Bearer Token)
- **CRUD**: 아이템 생성, 조회, 수정, 삭제
- **모니터링**: OpenTelemetry 자동 계측 + 구조화된 액세스 로그
- **API 문서**: Swagger UI 자동 생성

## 📋 요구사항

- Python 3.8+
- pip

## 🛠️ 설치

```bash
# 의존성 설치
pip install -r requirements.txt
```

## ⚙️ 환경변수 설정

```bash
# OpenTelemetry 설정
export OTEL_SERVICE_NAME=jiwoo-backend
export OTEL_EXPORTER_OTLP_ENDPOINT=http://collector.lgtm.20.249.154.255.nip.io
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_TRACES_EXPORTER=otlp
export OTEL_METRICS_EXPORTER=none
export OTEL_LOGS_EXPORTER=none

# 서비스 설정 (선택사항)
export OTEL_SERVICE_NAMESPACE=default
export OTEL_DEPLOYMENT_ENVIRONMENT=dev
```

## 🏃‍♂️ 실행

```bash
# 개발 모드로 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 또는 Python으로 직접 실행
python main.py
```

## 📖 API 사용법

### 1. 회원가입
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 2. 로그인
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### 3. 아이템 생성 (인증 필요)
```bash
curl -X POST "http://localhost:8000/items" \
  -H "Authorization: Bearer token_1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Item",
    "description": "This is a test item"
  }'
```

### 4. 아이템 조회 (인증 필요)
```bash
curl -X GET "http://localhost:8000/items" \
  -H "Authorization: Bearer token_1"
```

## 📊 모니터링 확인

### 1. 로그 확인
```bash
# 애플리케이션 로그 확인
tail -f /var/log/your-app.log

# 또는 표준 출력 확인
docker logs your-container-name
```

### 2. Grafana Loki 확인
```bash
# Loki 라벨 확인
curl -s "http://loki.20.249.154.255.nip.io/loki/api/v1/labels"

# 특정 서비스 로그 조회
curl -s "http://loki.20.249.154.255.nip.io/loki/api/v1/query_range" \
  -G \
  -d 'query={service_name="jiwoo-backend"}' \
  -d 'start=2024-01-01T00:00:00Z' \
  -d 'end=2024-01-02T00:00:00Z'
```

### 3. Grafana Tempo 확인
- Grafana UI에서 Tempo 데이터소스 접속
- 서비스명: `jiwoo-backend`
- 트레이스 ID로 상세 분석 가능

## 🔍 로그 형식

### 액세스 로그 예시
```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "logger": "app",
  "message": "HTTP request processed",
  "event": "http_access",
  "method": "POST",
  "path": "/items",
  "status": 201,
  "duration_ms": 45.23,
  "user": "jwt_user",
  "remote_addr": "127.0.0.1",
  "user_agent": "curl/7.68.0",
  "trace_id": "1234567890abcdef1234567890abcdef",
  "span_id": "1234567890abcdef"
}
```

### 애플리케이션 로그 예시
```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "logger": "app",
  "message": "Item created",
  "item_id": 1,
  "user_id": 1,
  "title": "My First Item"
}
```

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │───▶│  OTLP Collector  │───▶│   Grafana       │
│                 │    │                  │    │   (Loki/Tempo)  │
│ - HTTP Access   │    │ - Traces         │    │                 │
│ - App Logs      │    │ - Logs           │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🔧 개발

### 로컬 개발 환경
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
uvicorn main:app --reload
```

### API 문서
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🐛 문제 해결

### 1. OpenTelemetry 연결 실패
```bash
# OTLP 엔드포인트 확인
curl -v http://collector.lgtm.20.249.154.255.nip.io:4318/health

# 환경변수 확인
echo $OTEL_EXPORTER_OTLP_ENDPOINT
```

### 2. 로그가 Loki에 나타나지 않음
```bash
# 로그 형식 확인
tail -f your-app.log | jq .

# Loki 쿼리 테스트
curl -s "http://loki.20.249.154.255.nip.io/loki/api/v1/query_range" \
  -G \
  -d 'query={service_name="jiwoo-backend"}' \
  -d 'start=2024-01-01T00:00:00Z' \
  -d 'end=2024-01-02T00:00:00Z' | jq .
```

### 3. 트레이스가 Tempo에 나타나지 않음
- OTLP 엔드포인트 포트 확인 (4318)
- 네트워크 연결 확인
- 서비스명 환경변수 확인

## 📝 라이센스

MIT License 