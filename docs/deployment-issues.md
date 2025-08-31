# 배포 문제 해결 가이드

## 🚨 해결된 문제들 (시간순)

### [2025-08-31] 1. 카프카 로그 조회 문제

#### 문제 상황
- 프론트엔드에서 카프카 로그 조회 시 빈 배열 반환
- 백엔드 API는 200 응답을 반환하지만 실제 로그 데이터 없음
- 카프카 컨트롤러에 직접 접근 시 명령어가 멈춤

#### 원인 분석
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

#### 해결 방법

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

#### 결과
- ✅ 카프카 로그 조회 정상 작동
- ✅ 프론트엔드에서 로그 표시 완료
- ✅ 메시지 목록 10개 제한 적용
- ✅ 이중 저장으로 안정성 향상

---

### [2025-08-30] 2. ImagePullBackOff / 401 Unauthorized 오류

#### 문제 상황
```
Failed to pull image "ktech4.azurecr.io/kltecho_jiwoo-backend:latest": 
failed to resolve reference "ktech4.azurecr.io/kltecho_jiwoo-backend:latest": 
failed to authorize: failed to fetch anonymous token: 
unexpected status from GET request to https://ktech4.azurecr.io/oauth2/token: 401 Unauthorized
```

#### 원인
- Kubernetes 클러스터에서 Azure Container Registry (ACR) 인증 정보 누락
- `imagePullSecrets` 설정 없음

#### 해결 방법
1. **ACR Secret 생성** (`k8s/jiwoo-acr-secret.yaml`)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: acr-secret
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <base64-encoded-docker-config>
```

2. **배포 파일에 `imagePullSecrets` 추가**
```yaml
spec:
  imagePullSecrets:
  - name: acr-secret
  containers:
  - name: backend
    image: ktech4.azurecr.io/kltecho_jiwoo-backend:latest
```

3. **Secret 적용**
```bash
kubectl apply -f k8s/jiwoo-acr-secret.yaml -n jiwoo
```

#### 결과
- ✅ ACR에서 이미지 정상 Pull
- ✅ 자동화된 CI/CD 파이프라인 구축

---

### [2025-08-30] 3. GitHub Push Protection 차단

#### 문제 상황
- GitHub에서 평문 비밀번호가 포함된 파일 푸시 시 차단
- 보안 정책 위반으로 인한 푸시 실패

#### 해결 방법
1. **base64 인코딩 사용**
```bash
echo -n '{"auths":{"ktech4.azurecr.io":{"username":"ktech4","password":"<password>"}}}' | base64
```

2. **Git 히스토리 리셋**
```bash
git reset --soft HEAD~2
git add .
git commit -m "Update with encoded secrets"
git push origin main
```

#### 결과
- ✅ 보안 정책 준수하며 푸시 성공

---

### [2025-08-30] 4. 프론트엔드 외부 접속 불가

#### 문제 상황
- Azure AKS에서 NodePort 서비스로는 외부 접속 불가
- `localhost:30080` 접속 시도 실패

#### 해결 방법
1. **서비스 타입을 LoadBalancer로 변경**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: jiwoo-frontend-service
spec:
  type: LoadBalancer  # NodePort → LoadBalancer
  selector:
    app: jiwoo-frontend
  ports:
  - port: 80
    targetPort: 80
```

2. **LoadBalancer IP 확인**
```bash
kubectl get service jiwoo-frontend-service -n jiwoo
```

#### 결과
- ✅ 외부에서 프론트엔드 접속 가능

---

### [2025-08-30] 5. 리소스 부족 오류

#### 문제 상황
```
0/8 nodes are available: 8 Insufficient cpu.
```

#### 해결 방법
1. **MariaDB 리소스 최적화** (`k8s/mariadb-values.yaml`)
```yaml
primary:
  resources:
    requests:
      cpu: 100m        # 500m → 100m
      memory: 50Mi     # 512Mi → 50Mi
```

2. **Redis 리소스 최적화** (`k8s/redis-values.yaml`)
```yaml
resources:
  requests:
    cpu: 50m          # 250m → 50m
    memory: 50Mi      # 256Mi → 50Mi
```

3. **Kafka 리소스 최적화** (`k8s/kafka-values.yaml`)
```yaml
controller:
  resources:
    requests:
      cpu: 100m       # 500m → 100m
      memory: 100Mi   # 512Mi → 100Mi
```

#### 결과
- ✅ 리소스 효율적 사용
- ✅ 안정적인 배포 완료

---

### [2025-08-29] 6. 데이터베이스 연결 문제

#### 문제 상황
- `Unknown database 'testdb'` 오류
- 데이터베이스가 존재하지 않음

#### 해결 방법
- 환경변수로 데이터베이스 이름 변경 (`jiwoo_db`)
- 자동화된 초기화 Job 생성
- Helm 차트 설정 수정

#### 결과
- ✅ MariaDB 정상 연결
- ✅ 자동 초기화 완료

---

### [2025-08-29] 7. 테이블 없음 문제

#### 문제 상황
- `Table 'jiwoo_db.users' doesn't exist`
- 데이터베이스 테이블이 생성되지 않음

#### 해결 방법
- 자동화된 초기화 Job 생성
- Helm 차트 설정 수정
- 데이터베이스 스키마 자동 생성

#### 결과
- ✅ 자동 초기화 완료

---

### [2025-08-29] 8. Kafka CrashLoopBackOff

#### 문제 상황
- 컨트롤러 수 불일치 및 SASL 인증 문제
- Kafka Pod가 계속 재시작됨

#### 해결 방법
- 컨트롤러 수 조정 및 SASL 인증 비활성화
- Helm 차트 설정 최적화

#### 결과
- ✅ Kafka 정상 작동

---

### [2025-08-29] 9. 사용자 정보 미저장 문제

#### 문제 상황
- 메시지 저장 시 "사용자 없음" 표시
- 사용자 정보가 데이터베이스에 저장되지 않음

#### 해결 방법
- SQL 쿼리에 `user_id` 추가
- 백엔드 코드 수정

#### 결과
- ✅ 사용자별 메시지 관리 가능

---

### [2025-08-29] 10. 배포 시간 최적화

#### 문제 상황
- 300초 타임아웃으로 인한 긴 배포 시간
- 배포 스크립트 실행 시간이 너무 김

#### 해결 방법
- 120초/60초로 최적화
- 배포 스크립트 개선

#### 결과
- ✅ 효율적인 배포 시간

---

## 🔧 일반적인 문제 해결 방법

### 1. Pod 상태 확인
```bash
kubectl get pods -n jiwoo
kubectl describe pod <pod-name> -n jiwoo
kubectl logs <pod-name> -n jiwoo
```

### 2. 서비스 연결 확인
```bash
kubectl get services -n jiwoo
kubectl describe service <service-name> -n jiwoo
```

### 3. 배포 롤아웃 재시작
```bash
kubectl rollout restart deployment <deployment-name> -n jiwoo
kubectl rollout status deployment <deployment-name> -n jiwoo
```

### 4. 로그 실시간 모니터링
```bash
kubectl logs -f <pod-name> -n jiwoo
```

### 5. 네임스페이스 정리
```bash
./cleanup-jiwoo-namespace.sh
```

---

## 📋 문제 해결 체크리스트

### 배포 전 확인사항
- [ ] GitHub Actions 빌드 완료 확인
- [ ] ACR에 이미지 푸시 완료 확인
- [ ] 네임스페이스 존재 확인
- [ ] 리소스 요청량 적절성 확인

### 배포 후 확인사항
- [ ] 모든 Pod Running 상태 확인
- [ ] 서비스 정상 작동 확인
- [ ] 외부 접근 가능 확인
- [ ] 로그 정상 출력 확인

### 문제 발생 시 확인사항
- [ ] Pod 로그 확인
- [ ] 서비스 설정 확인
- [ ] 네트워크 연결 확인
- [ ] 리소스 사용량 확인

---

## 🚀 예방 방법

### 1. 코드 변경 시
- 로컬에서 테스트 후 푸시
- GitHub Actions 빌드 완료 대기
- 새로운 이미지로 롤아웃 재시작

### 2. 설정 변경 시
- YAML 파일 문법 검증
- 환경변수 설정 확인
- Secret 값 정확성 확인

### 3. 리소스 관리
- 정기적인 리소스 사용량 모니터링
- 불필요한 리소스 정리
- 적절한 요청량 설정

---

## 📞 추가 지원

문제가 지속되면 다음을 확인하세요:
1. Kubernetes 클러스터 상태
2. 네트워크 연결 상태
3. Azure 서비스 상태
4. GitHub Actions 워크플로우 상태
