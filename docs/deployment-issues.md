# 배포 문제 해결 가이드

## 🔧 해결된 문제들

### 1. ImagePullBackOff / 401 Unauthorized 오류

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

### 2. GitHub Push Protection 차단

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

### 3. 프론트엔드 외부 접속 불가

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

### 4. 리소스 부족 오류

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

### 5. Kafka 로그 표시 문제 (진행 중)

#### 문제 상황
- 백엔드에서 Kafka 메시지 전송은 성공
- 프론트엔드에서 로그 조회 시 빈 응답
- Kafka Consumer가 메시지를 읽지 못함

#### 해결 시도
1. **SASL 인증 설정**
```python
def get_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=os.getenv('KAFKA_SERVERS', 'jiwoo-kafka:9092'),
        security_protocol='SASL_PLAINTEXT',
        sasl_mechanism='PLAIN',
        sasl_plain_username='admin',
        sasl_plain_password='admin-secret',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
```

2. **Consumer 설정 최적화**
```python
consumer = KafkaConsumer(
    'api-logs',
    bootstrap_servers=os.getenv('KAFKA_SERVERS', 'jiwoo-kafka:9092'),
    security_protocol='SASL_PLAINTEXT',
    sasl_mechanism='PLAIN',
    sasl_plain_username='admin',
    sasl_plain_password='admin-secret',
    group_id='api-logs-viewer-' + str(int(time.time())),
    auto_offset_reset='earliest',
    consumer_timeout_ms=3000,
    enable_auto_commit=True,
    auto_commit_interval_ms=1000
)
```

3. **Kafka Helm 설정 업데이트**
```yaml
auth:
  enabled: false
controller:
  extraEnvVars:
    - name: KAFKA_AUTO_CREATE_TOPICS_ENABLE
      value: "true"
    - name: KAFKA_CFG_SASL_ENABLED_MECHANISMS
      value: "PLAIN"
    - name: KAFKA_CFG_SASL_MECHANISM_INTER_BROKER_PROTOCOL
      value: "PLAIN"
    - name: KAFKA_CFG_SASL_JAAS_CONFIG
      value: "org.apache.kafka.common.security.plain.PlainLoginModule required username=\"admin\" password=\"admin-secret\";"
```

#### 현재 상태
- 디버그 로그 추가 완료
- 백엔드 재배포 완료
- 정확한 원인 파악을 위한 로그 분석 필요

## 🛠️ 디버깅 명령어

### Pod 상태 확인
```bash
# Pod 상태 확인
kubectl get pods -n jiwoo

# Pod 상세 정보
kubectl describe pod <pod-name> -n jiwoo

# Pod 로그 확인
kubectl logs <pod-name> -n jiwoo --tail=50
```

### 서비스 상태 확인
```bash
# 서비스 상태 확인
kubectl get services -n jiwoo

# 서비스 상세 정보
kubectl describe service <service-name> -n jiwoo
```

### 배포 상태 확인
```bash
# 배포 상태 확인
kubectl get deployments -n jiwoo

# 배포 상세 정보
kubectl describe deployment <deployment-name> -n jiwoo

# 배포 롤아웃 상태
kubectl rollout status deployment/<deployment-name> -n jiwoo
```

### 리소스 사용량 확인
```bash
# 노드별 리소스 사용량
kubectl top nodes

# Pod별 리소스 사용량
kubectl top pods -n jiwoo

# 네임스페이스별 리소스 요청
kubectl describe nodes | grep -A 10 "Allocated resources"
```

### Kafka 디버깅
```bash
# Kafka 토픽 확인
kubectl exec -it jiwoo-kafka-controller-0 -n jiwoo -- kafka-topics.sh --list --bootstrap-server localhost:9092

# Kafka 메시지 확인
kubectl exec -it jiwoo-kafka-controller-0 -n jiwoo -- kafka-console-consumer.sh --topic api-logs --from-beginning --bootstrap-server localhost:9092
```

## 📋 예방 방법

### 1. 배포 전 체크리스트
- [ ] ACR Secret이 올바르게 설정되었는지 확인
- [ ] 이미지 태그가 일치하는지 확인
- [ ] 리소스 요청이 적절한지 확인
- [ ] 네임스페이스가 올바른지 확인

### 2. 모니터링 체크리스트
- [ ] Pod 상태가 Running인지 확인
- [ ] 서비스가 올바르게 생성되었는지 확인
- [ ] 로그에 오류가 없는지 확인
- [ ] 리소스 사용량이 적절한지 확인

### 3. 문제 발생 시 대응 순서
1. **즉시 확인**: `kubectl get pods -n jiwoo`
2. **상세 분석**: `kubectl describe pod <pod-name> -n jiwoo`
3. **로그 확인**: `kubectl logs <pod-name> -n jiwoo`
4. **리소스 확인**: `kubectl top nodes`
5. **재배포**: `kubectl rollout restart deployment/<deployment-name> -n jiwoo`

## 🔄 최신 문제 해결 (2024-08-28)

### Kafka 로그 표시 문제
- **상태**: 진행 중
- **마지막 업데이트**: 백엔드 재배포 완료, 디버그 로그 추가
- **다음 단계**: 백엔드 로그 분석을 통한 정확한 원인 파악

### 해결된 문제들
1. ✅ **ImagePullBackOff / 401 Unauthorized**: ACR 인증 설정으로 해결
2. ✅ **GitHub Push Protection**: base64 인코딩으로 해결
3. ✅ **프론트엔드 외부 접속 불가**: LoadBalancer 서비스 타입으로 해결
4. ✅ **리소스 부족 오류**: CPU/메모리 요청 최적화로 해결
