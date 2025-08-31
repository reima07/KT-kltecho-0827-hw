# 🔧 트러블슈팅 로그 - 2024년 12월 27일

## 📋 **오늘 해결한 문제들**

### 1. 🚨 **Redis 로그 최신화 문제**
**문제:** 프론트엔드에서 Redis 로그를 조회할 때 최신 로그가 제대로 표시되지 않음

**원인:** Redis 리스트 인덱스 오류
```python
# 문제가 있던 코드
redis_client.lpush('kafka_logs', json.dumps(log_data))  # 왼쪽에 추가
redis_client.ltrim('kafka_logs', 0, 99)  # 100개 유지
logs = redis_client.lrange('kafka_logs', -10, -1)  # 오른쪽에서 10개 조회 (오래된 것들)
```

**해결:** 조회 인덱스를 수정
```python
# 수정된 코드
logs = redis_client.lrange('kafka_logs', 0, 9)  # 왼쪽에서 10개 조회 (최신 것들)
```

**파일:** `backend/app.py` - `get_kafka_logs()` 함수

---

### 2. 🚨 **OTel 로그가 Loki로 전송되지 않는 문제**
**문제:** OpenTelemetry 로그가 Grafana Loki로 전송되지 않음

**원인 1:** 초기화 순서 문제
```python
# 문제가 있던 순서
tracer, meter = setup_telemetry(app)  # OTel 핸들러 추가
setup_logging()  # 모든 핸들러 제거 (OTel 핸들러도 삭제됨)
```

**해결 1:** 초기화 순서 변경
```python
# 수정된 순서
setup_logging()  # 먼저 로깅 설정
tracer, meter = setup_telemetry(app)  # 그 다음 OTel 설정 (핸들러 보존)
```

**원인 2:** OTel 핸들러가 제거되는 문제
```python
# 문제가 있던 코드 (logging_config.py)
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)  # OTel 핸들러도 제거됨
```

**해결 2:** OTel 핸들러 보존
```python
# 수정된 코드 (logging_config.py)
from opentelemetry.sdk._logs import LoggingHandler as OtelLoggingHandler

for handler in root_logger.handlers[:]:
    # OTel LoggingHandler는 보존
    if isinstance(handler, OtelLoggingHandler):
        continue
    root_logger.removeHandler(handler)
```

**원인 3:** 엔드포인트 포트 누락
```yaml
# 문제가 있던 설정
OTEL_EXPORTER_OTLP_ENDPOINT: "http://collector.lgtm.20.249.154.255.nip.io"
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT: "http://collector.lgtm.20.249.154.255.nip.io/v1/logs"
```

**해결 3:** 포트 명시
```yaml
# 수정된 설정
OTEL_EXPORTER_OTLP_ENDPOINT: "http://collector.lgtm.20.249.154.255.nip.io:4318"
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT: "http://collector.lgtm.20.249.154.255.nip.io:4318/v1/logs"
```

**파일들:**
- `backend/app.py` - 초기화 순서
- `backend/logging_config.py` - OTel 핸들러 보존
- `k8s/jiwoo-backend-deployment.yaml` - 엔드포인트 포트

---

## 🔍 **문제 진단 과정**

### **Redis 로그 문제 진단**
1. 프론트엔드에서 로그 조회 시 최신화 안 되는 현상 발견
2. Redis 리스트 구조 분석: `lpush` + `ltrim` + `lrange`
3. 인덱스 방향성 문제 발견: 왼쪽 추가 vs 오른쪽 조회
4. 조회 인덱스를 `(-10, -1)` → `(0, 9)`로 수정

### **OTel 로그 문제 진단**
1. Grafana Loki에서 로그가 보이지 않는 현상
2. ChatGPT 답변 참고하여 3가지 원인 파악:
   - 초기화 순서 문제
   - OTel 핸들러 제거 문제
   - 엔드포인트 포트 누락
3. 각 원인별로 순차적 수정

---

## 📝 **수정된 파일들**

### 1. `backend/app.py`
```diff
# 초기화 순서 변경
- tracer, meter = setup_telemetry(app)
- setup_logging()
+ setup_logging()  # 먼저 로깅 설정
+ tracer, meter = setup_telemetry(app)  # 그 다음 OTel 설정 (핸들러 보존)

# Redis 로그 조회 수정
- logs = redis_client.lrange('kafka_logs', -10, -1)
+ logs = redis_client.lrange('kafka_logs', 0, 9)
```

### 2. `backend/logging_config.py`
```diff
# OTel 핸들러 보존 로직 추가
+ from opentelemetry.sdk._logs import LoggingHandler as OtelLoggingHandler

for handler in root_logger.handlers[:]:
+     # OTel LoggingHandler는 보존
+     if isinstance(handler, OtelLoggingHandler):
+         continue
    root_logger.removeHandler(handler)
```

### 3. `k8s/jiwoo-backend-deployment.yaml`
```diff
# 엔드포인트 포트 명시
- value: "http://collector.lgtm.20.249.154.255.nip.io"
+ value: "http://collector.lgtm.20.249.154.255.nip.io:4318"

- value: "http://collector.lgtm.20.249.154.255.nip.io/v1/logs"
+ value: "http://collector.lgtm.20.249.154.255.nip.io:4318/v1/logs"
```

---

## 🚀 **배포 과정**

### **Git 커밋 및 푸시**
```bash
git add .
git commit -m "OTel 로그 핸들러 보존 및 엔드포인트 포트 수정"
git push origin main
```

### **Kubernetes 롤아웃**
```bash
kubectl rollout restart deployment/jiwoo-backend -n jiwoo
```

### **배포 확인**
```bash
kubectl get pods -n jiwoo -w
# 새 파드: jiwoo-backend-598c65d4c7-8w9xt
```

---

## ✅ **해결 결과**

### **Redis 로그 최신화**
- ✅ 프론트엔드에서 최신 10개 로그 정상 조회
- ✅ 로그 쌓여도 최신화 정상 작동

### **OTel 로그 전송**
- ✅ OpenTelemetry 로그가 Loki로 정상 전송
- ✅ Grafana에서 `{service_name="jiwoo-backend"}` 로그 조회 가능

---

## 📚 **학습한 내용**

### **Redis 리스트 동작 방식**
- `lpush`: 왼쪽(앞쪽)에 추가
- `ltrim(0, 99)`: 왼쪽에서 100개만 유지
- `lrange(0, 9)`: 왼쪽에서 10개 조회 (최신)
- `lrange(-10, -1)`: 오른쪽에서 10개 조회 (오래된 것)

### **OpenTelemetry 로깅**
- OTel 핸들러는 루트 로거에 추가됨
- `setup_logging()`이 모든 핸들러를 제거할 때 OTel 핸들러도 함께 삭제됨
- 초기화 순서와 핸들러 보존이 중요

### **Kubernetes 환경변수**
- OTLP 엔드포인트에 포트 명시 필요 (4318)
- 기본 80 포트는 Collector 인그레스로 제대로 매핑되지 않을 수 있음

---

## 🔮 **향후 개선 사항**

1. **로깅 설정 통합**: OTel과 일반 로깅 설정을 하나로 통합
2. **모니터링 대시보드**: Grafana 대시보드 구축
3. **로그 보존 정책**: Redis 로그 보존 기간 설정
4. **에러 핸들링**: 로그 전송 실패 시 대체 방안

---

## 📞 **참고 자료**

- ChatGPT 답변: OTel 로그 핸들러 문제 진단
- Redis 공식 문서: 리스트 명령어 동작 방식
- OpenTelemetry 문서: 로깅 설정 가이드
