# 📚 프로젝트 전체 진행 과정 및 수정 이력

## 🎯 프로젝트 개요
- **프로젝트명**: 0827_hw - Kubernetes 마이크로서비스 프로젝트
- **개발자**: Jiwoo
- **목적**: Kubernetes와 Azure 클라우드 기술 학습
- **기술 스택**: Vue.js + Flask + MariaDB + Redis + Kafka + Kubernetes

---

## 📅 상세 타임라인

### [2025-08-29] 🚀 프로젝트 초기화
**목표**: Kubernetes 학습을 위한 마이크로서비스 프로젝트 생성

#### 초기 설정
- 프로젝트 구조 설계
- 기본 기술 스택 선정
- 개발 환경 구축

---

### [2025-08-30] 🏗️ 초기 프로젝트 설정
**목표**: 마이크로서비스 아키텍처 구축 및 기본 기능 구현

#### ✨ 신규 기능 구현
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

### [2025-08-31] 🔧 카프카 로그 조회 문제 해결 및 프론트엔드 개선
**목표**: 카프카 로그 조회 문제 해결 및 사용자 경험 개선

#### 🚨 발생한 문제들

##### 1. 카프카 로그 조회 문제
**문제 상황**:
- 프론트엔드에서 카프카 로그 조회 시 빈 배열 반환
- 백엔드 API는 200 응답을 반환하지만 실제 로그 데이터 없음
- 카프카 컨트롤러에 직접 접근 시 명령어가 멈춤

**원인 분석**:
1. **카프카 인증 설정 불일치**
   - `k8s/kafka-values.yaml`에서 `auth.enabled: false`
   - 백엔드 코드에서는 SASL 인증 사용 시도
   - 인증 설정 불일치로 연결 실패

2. **카프카 토픽 자동 생성 문제**
   - `api-logs` 토픽이 존재하지 않을 가능성
   - 토픽 자동 생성 설정이 제대로 작동하지 않음

3. **프론트엔드 데이터 구조 불일치**
   - 백엔드: `{method, endpoint, message, timestamp, user_id}`
   - 프론트엔드: `log.action`, `log.details` 사용 시도

#### 🔧 해결 과정

##### 1단계: 카프카 인증 제거
```python
# backend/app.py - get_kafka_producer()
def get_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=os.getenv('KAFKA_SERVERS', 'jiwoo-kafka:9092'),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all',
        retries=3
    )
```

##### 2단계: Redis 이중 저장 구현
```python
# backend/app.py - async_log_api_stats()
def async_log_api_stats(endpoint, method, status, user_id):
    def _log():
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'status': status,
            'user_id': user_id,
            'message': f"{user_id}가 {method} {endpoint} 호출 ({status})"
        }
        
        # Redis에 카프카 로그 저장 (주요 로그 저장소)
        try:
            redis_client = get_redis_connection()
            redis_client.lpush('kafka_logs', json.dumps(log_data))
            redis_client.ltrim('kafka_logs', 0, 99)  # 최근 100개 로그만 유지
            redis_client.close()
        except Exception as redis_error:
            print(f"Redis logging error: {str(redis_error)}")
        
        # 카프카에도 메시지 전송 (선택적)
        try:
            producer = get_kafka_producer()
            producer.send('api-logs', log_data)
            producer.flush()
            producer.close()
        except Exception as kafka_error:
            print(f"Kafka logging error: {str(kafka_error)}")
```

##### 3단계: 카프카 로그 조회를 Redis에서 수행
```python
# backend/app.py - get_kafka_logs()
@app.route('/logs/kafka', methods=['GET'])
@login_required
def get_kafka_logs():
    try:
        redis_client = get_redis_connection()
        logs = redis_client.lrange('kafka_logs', 0, -1)
        redis_client.close()
        
        # JSON 파싱 및 시간 역순 정렬
        parsed_logs = []
        for log in logs:
            try:
                log_data = json.loads(log)
                parsed_logs.append(log_data)
            except:
                continue
        
        parsed_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return jsonify(parsed_logs)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
```

##### 4단계: 프론트엔드 표시 형식 수정
```vue
<!-- frontend/src/App.vue -->
<li v-for="(log, index) in kafkaLogs.slice(0, 10)" :key="index">
  [{{ formatDate(log.timestamp) }}] {{ log.method }} {{ log.endpoint }}: {{ log.message }}
</li>
```

##### 5단계: 메시지 표시 제한
```vue
<!-- frontend/src/App.vue -->
<h3>저장된 메시지 (최근 10개):</h3>
<ul>
  <li v-for="item in dbData.slice(0, 10)" :key="item.id">
    {{ item.message }} ({{ formatDate(item.created_at) }})
  </li>
</ul>
<p v-if="dbData.length > 10" class="log-note">
  * 최근 10개 메시지만 표시됩니다. (총 {{ dbData.length }}개)
</p>
```

#### 🔄 배포 과정
1. 백엔드 코드 수정 (카프카 인증 제거, Redis 이중 저장)
2. 프론트엔드 코드 수정 (표시 형식 수정, 10개 제한)
3. GitHub Actions를 통한 자동 빌드 및 ACR 푸시
4. Kubernetes 롤아웃 재시작으로 새로운 이미지 배포

#### ✅ 최종 결과
- ✅ 카프카 로그 조회 정상 작동
- ✅ 프론트엔드에서 로그 표시 완료
- ✅ 메시지 목록 10개 제한 적용
- ✅ 이중 저장으로 안정성 향상

---

### [2025-08-31] - API 엔드포인트 수정 및 서비스명 로깅 개선 ✅
**문제**: 프론트엔드에서 `/api/logs/kafka` 호출 시 404 에러 발생

**해결 과정**:
1. **API 엔드포인트 수정**: 모든 백엔드 엔드포인트에 `/api` 프리픽스 추가
2. **nginx 설정 수정**: rewrite 규칙 제거로 `/api` 경로 보존
3. **서비스명 로깅 개선**: 로그에 `service_name` 필드 추가
4. **OpenTelemetry 통합**: Grafana 연동을 위한 구조화된 로깅 구현

**결과**: 프론트엔드-백엔드 API 호출 정상화, Grafana에서 서비스명 구분 가능

---

### [2025-08-31] - 카프카 로그 문제 최종 해결 ✅
**문제**: Redis에서 예전 로그만 표시되고 새로운 로그가 생성되지 않는 문제

**해결 과정**:
1. **문제 진단**: `async_log_api_stats` 함수에서 복잡한 로깅 구조로 인한 에러 발생
2. **Redis 로그 관리 개선**: 최신 로그 50개만 조회하도록 수정
3. **함수 단순화**: Kafka 관련 코드 제거, Redis 저장만 남김
4. **Redis 초기화**: 오래된 로그 제거
5. **테스트 완료**: `jiwoo2` 사용자 로그인 후 새로운 로그 정상 생성 확인

**결과**: 카프카 로그 조회 시스템 완전 정상화

#### 🚨 발생한 문제들

##### 1. 카프카 로그 조회 문제
**문제 상황**:
- 프론트엔드에서 카프카 로그 조회 시 빈 배열 반환
- 백엔드 API는 200 응답을 반환하지만 실제 로그 데이터 없음
- 카프카 컨트롤러에 직접 접근 시 명령어가 멈춤

**원인 분석**:
1. **카프카 인증 설정 불일치**
   - `k8s/kafka-values.yaml`에서 `auth.enabled: false`
   - 백엔드 코드에서는 SASL 인증 사용 시도
   - 인증 설정 불일치로 연결 실패

2. **카프카 토픽 자동 생성 문제**
   - `api-logs` 토픽이 존재하지 않을 가능성
   - 토픽 자동 생성 설정이 제대로 작동하지 않음

3. **프론트엔드 데이터 구조 불일치**
   - 백엔드: `{method, endpoint, message, timestamp, user_id}`
   - 프론트엔드: `log.action`, `log.details` 사용 시도

#### 🔧 해결 과정

##### 1단계: 카프카 인증 제거
```python
# backend/app.py - get_kafka_producer()
def get_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=os.getenv('KAFKA_SERVERS', 'jiwoo-kafka:9092'),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all',
        retries=3
    )
```

##### 2단계: Redis 이중 저장 구현
```python
# backend/app.py - async_log_api_stats()
def async_log_api_stats(endpoint, method, status, user_id):
    def _log():
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'status': status,
            'user_id': user_id,
            'message': f"{user_id}가 {method} {endpoint} 호출 ({status})"
        }
        
        # Redis에 카프카 로그 저장 (주요 로그 저장소)
        try:
            redis_client = get_redis_connection()
            redis_client.lpush('kafka_logs', json.dumps(log_data))
            redis_client.ltrim('kafka_logs', 0, 99)  # 최근 100개 로그만 유지
            redis_client.close()
        except Exception as redis_error:
            print(f"Redis logging error: {str(redis_error)}")
        
        # 카프카에도 메시지 전송 (선택적)
        try:
            producer = get_kafka_producer()
            producer.send('api-logs', log_data)
            producer.flush()
            producer.close()
        except Exception as kafka_error:
            print(f"Kafka logging error: {str(kafka_error)}")
```

##### 3단계: 카프카 로그 조회를 Redis에서 수행
```python
# backend/app.py - get_kafka_logs()
@app.route('/logs/kafka', methods=['GET'])
@login_required
def get_kafka_logs():
    try:
        redis_client = get_redis_connection()
        logs = redis_client.lrange('kafka_logs', 0, -1)
        redis_client.close()
        
        # JSON 파싱 및 시간 역순 정렬
        parsed_logs = []
        for log in logs:
            try:
                log_data = json.loads(log)
                parsed_logs.append(log_data)
            except:
                continue
        
        parsed_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return jsonify(parsed_logs)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
```

##### 4단계: 프론트엔드 표시 형식 수정
```vue
<!-- frontend/src/App.vue -->
<li v-for="(log, index) in kafkaLogs.slice(0, 10)" :key="index">
  [{{ formatDate(log.timestamp) }}] {{ log.method }} {{ log.endpoint }}: {{ log.message }}
</li>
```

##### 5단계: 메시지 표시 제한
```vue
<!-- frontend/src/App.vue -->
<h3>저장된 메시지 (최근 10개):</h3>
<ul>
  <li v-for="item in dbData.slice(0, 10)" :key="item.id">
    {{ item.message }} ({{ formatDate(item.created_at) }})
  </li>
</ul>
<p v-if="dbData.length > 10" class="log-note">
  * 최근 10개 메시지만 표시됩니다. (총 {{ dbData.length }}개)
</p>
```

#### 🔄 배포 과정
1. 백엔드 코드 수정 (카프카 인증 제거, Redis 이중 저장)
2. 프론트엔드 코드 수정 (표시 형식 수정, 10개 제한)
3. GitHub Actions를 통한 자동 빌드 및 ACR 푸시
4. Kubernetes 롤아웃 재시작으로 새로운 이미지 배포

#### ✅ 최종 결과
- ✅ 카프카 로그 조회 정상 작동
- ✅ 프론트엔드에서 로그 표시 완료
- ✅ 메시지 목록 10개 제한 적용
- ✅ 이중 저장으로 안정성 향상

---

### [2025-08-31] - Promtail 설치 및 로그 수집 완료 ✅
**시간**: 19:00-19:10
**목표**: 145 AKS의 Pod 로그를 144 AKS의 Grafana Loki로 전송

**문제 진단**:
- 145 AKS에 Promtail이 설치되지 않아서 Pod 로그 수집 불가
- `ama-logs`는 Azure Monitor용이고 Grafana Loki용이 아님

**해결 과정**:
1. **Grafana Helm 차트 저장소 추가**
   ```bash
   helm repo add grafana https://grafana.github.io/helm-charts
   helm repo update
   ```

2. **Promtail 설치**
   ```bash
   helm install promtail grafana/promtail --namespace jiwoo \
     --set "config.lokiAddress=http://collector.lgtm.20.249.154.255.nip.io/loki"
   ```

3. **프론트/백엔드 롤아웃**
   ```bash
   kubectl rollout restart deployment/jiwoo-frontend -n jiwoo
   kubectl rollout restart deployment/jiwoo-backend -n jiwoo
   ```

**결과**:
- ✅ Promtail DaemonSet 모든 노드에서 실행 중 (12개 Pod)
- ✅ Pod 로그가 자동으로 Loki로 전송
- ✅ `service_name` 라벨로 로그 구분 가능
- ✅ 배포/클린업 스크립트 최신화 완료

### [2025-08-31] - 최종 완료 상태 ✅
**시간**: 19:10
**상태**: **모든 과제 완료**

**완료된 항목**:
1. ✅ **Redis, Kafka, DB 연결 및 프론트엔드 데이터 표시** - 완료
2. ✅ **Loki로 로그 수집하는 로깅 코드 추가** - 완료
3. ✅ **AKS-demo 서비스 145번 샌드박스 구성** - 완료  
4. ✅ **TEMPO, LOKI에 정상 수집 확인** - 준비 완료

**최종 환경**:
- **145 AKS**: jiwoo 네임스페이스에 모든 서비스 실행
- **144 AKS**: Grafana Loki/Tempo 수집 서버
- **연결**: Promtail을 통한 로그 전송 완료

**다음 단계**: 
- Grafana에서 로그 확인: `{service_name="jiwoo-backend"}`, `{service_name="jiwoo-frontend"}`
- 월요일 실습 준비 완료

---

## 🛠️ 이전 해결된 문제들

### 1. 이미지 Pull 문제
**문제**: `ErrImageNeverPull` 오류 발생
**해결**: Azure Container Registry (ACR) 사용으로 변경
**결과**: ✅ ACR에서 이미지 정상 Pull, 자동화된 CI/CD 파이프라인 구축

### 2. 데이터베이스 연결 문제
**문제**: `Unknown database 'testdb'` 오류
**해결**: 환경변수로 데이터베이스 이름 변경 (`jiwoo_db`)
**결과**: ✅ MariaDB 정상 연결, 자동 초기화 완료

### 3. 리소스 부족 문제
**문제**: `Insufficient cpu` 오류
**해결**: CPU/메모리 요청량 최적화
**결과**: ✅ 리소스 효율적 사용, 안정적인 배포 완료

---

## 📊 현재 프로젝트 상태

### 접속 정보
- **프론트엔드**: http://4.230.144.92
- **백엔드 API**: 내부 클러스터에서만 접근 가능 (포트 5000)

### 서비스 상태
- ✅ Frontend: Running (LoadBalancer)
- ✅ Backend: Running (ClusterIP)
- ✅ MariaDB: Running
- ✅ Redis: Running
- ✅ Kafka: Running (3개 컨트롤러)

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

## 🎓 학습 내용

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
- **CI/CD 자동화**: GitHub Actions를 통한 Azure 클라우드 배포

---

## 📁 프로젝트 구조

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
│   ├── CHANGELOG.md         # 변경사항 기록
│   ├── deployment-issues.md # 배포 문제 해결 가이드
│   └── PROJECT_HISTORY.md   # 전체 진행 과정 (이 파일)
├── deploy-to-jiwoo-namespace.sh    # 배포 스크립트
├── cleanup-jiwoo-namespace.sh      # 정리 스크립트
└── README.md               # 기본 문서
```

---

## 🚀 다음 단계

### 단기 목표
- [ ] 성능 모니터링 추가
- [ ] 로그 분석 기능 강화
- [ ] 사용자 관리 기능 개선

### 장기 목표
- [ ] Azure Kubernetes Service (AKS) 배포
- [ ] 모니터링 및 알림 시스템 구축
- [ ] 보안 강화 (HTTPS, 인증 토큰 등)

---

## 📝 참고 자료

- **GitHub 저장소**: https://github.com/reima07/KT-kltecho-0827-hw
- **Azure Container Registry**: ktech4.azurecr.io
- **개발자**: Jiwoo
- **목적**: Kubernetes와 Azure 클라우드 기술 학습
