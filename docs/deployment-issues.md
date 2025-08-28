# 배포 문제 해결 가이드

## 개요
이 문서는 Kubernetes 배포 과정에서 발생할 수 있는 문제들과 해결 방법을 정리합니다.

## 🔥 최신 문제 해결 (2024-08-28)

### 1. ImagePullBackOff / 401 Unauthorized 오류

#### 문제 상황
```
Events: Type Reason Age From Message
Normal Scheduled 104s default-scheduler Successfully assigned jiwoo/jiwoo-backend-688d545856-p2hw6 to aks-agentpool-33969586-vmss000001
Normal BackOff 24s (x5 over 103s) kubelet Back-off pulling image "ktech4.azurecr.io/kltecho_jiwoo_20250828_032716-backend"
Warning Failed 24s (x5 over 103s) kubelet Error: ImagePullBackOff
Normal Pulling 9s (x4 over 104s) kubelet Pulling image "ktech4.azurecr.io/kltecho_jiwoo_20250828_032716-backend"
Warning Failed 9s (x4 over 104s) kubelet Failed to pull image "ktech4.azurecr.io/kltecho_jiwoo_20250828_032716-backend": failed to pull and unpack image "ktech4.azurecr.io/kltecho_jiwoo_20250828_032716-backend:latest": failed to resolve reference "ktech4.azurecr.io/kltecho_jiwoo_20250828_032716-backend:latest": failed to authorize: failed to fetch anonymous token: unexpected status from GET request to https://ktech4.azurecr.io/oauth2/token?scope=repository%3Akltecho_jiwoo_20250828_032716-backend%3Apull&service=ktech4.azurecr.io: 401 Unauthorized
Error: ErrImagePull
```

#### 원인 분석
1. **ACR 인증 문제**: Kubernetes 클러스터가 ACR에서 이미지를 가져올 때 인증 실패
2. **이미지 이름 불일치**: GitHub Actions와 배포 파일의 이미지 이름이 다름
3. **GitHub Actions vs Kubernetes 인증 차이**: 
   - GitHub Actions: ACR에 이미지 푸시용 인증
   - Kubernetes: ACR에서 이미지 풀링용 인증

#### 해결 방법

##### 1단계: ACR 시크릿 생성
```yaml
# k8s/jiwoo-acr-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: acr-secret
type: kubernetes.io/dockerconfigjson
stringData:
  .dockerconfigjson: |
    {
      "auths": {
        "ktech4.azurecr.io": {
          "username": "ktech4",
          "password": "YOUR_ACR_PASSWORD"
        }
      }
    }
```

##### 2단계: 배포 파일에 imagePullSecrets 추가
```yaml
# k8s/jiwoo-backend-deployment.yaml
spec:
  template:
    spec:
      imagePullSecrets:
      - name: acr-secret
      containers:
      - name: backend
        image: ktech4.azurecr.io/kltecho_jiwoo-backend:latest
```

##### 3단계: 이미지 이름 통일
- **GitHub Actions**: `kltecho_jiwoo-backend:latest`
- **배포 파일**: `kltecho_jiwoo-backend:latest`

##### 4단계: 배포 스크립트에 ACR 시크릿 적용 추가
```bash
# deploy-to-jiwoo-namespace.sh
echo "   - Secret 적용 중..."
kubectl apply -f k8s/jiwoo-backend-secret.yaml -n jiwoo -v=1
kubectl apply -f k8s/jiwoo-acr-secret.yaml -n jiwoo -v=1  # 추가
echo "   ✅ Secret 적용 완료"
```

#### 검증 방법
```bash
# ACR 시크릿 확인
kubectl get secrets -n jiwoo

# Pod 상태 확인
kubectl get pods -n jiwoo

# Pod 상세 정보 확인
kubectl describe pod <pod-name> -n jiwoo
```

## 🚨 이전 문제들과 해결 방법

### 1. MariaDB 스케줄링 실패

#### 문제 상황
```
Warning FailedScheduling ... Insufficient cpu
```

#### 원인 분석
- **CPU 요구량**: MariaDB 기본값 500m이 너무 높음
- **클러스터 상황**: 다른 사용자들의 서비스들이 많은 CPU 사용
- **노드 부족**: 사용 가능한 CPU가 부족한 상황

#### 해결 방법
```yaml
# k8s/mariadb-values.yaml
primary:
  resources:
    requests:
      cpu: 250m        # 500m에서 50% 감소
      memory: 512Mi    # 적절한 메모리 설정
```

### 2. Kafka 설치 타임아웃

#### 문제 상황
```
INSTALLATION FAILED: context deadline exceeded
```

#### 원인 분석
- **Helm 타임아웃**: 기본 300초가 부족
- **리소스 부족**: Kafka가 요구하는 리소스가 많음
- **네트워크 지연**: 이미지 다운로드 시간

#### 해결 방법
```bash
# deploy-to-jiwoo-namespace.sh에서 타임아웃 증가
helm install jiwoo-kafka bitnami/kafka \
  --values k8s/kafka-values.yaml \
  --namespace jiwoo \
  --wait \
  --timeout 600s \    # 300s에서 600s로 증가
  --debug
```

### 3. 네임스페이스 불일치 오류

#### 문제 상황
```
error: the namespace from the provided object "default" does not match the namespace "jiwoo"
```

#### 원인 분석
- **YAML 파일**: `namespace: default`로 하드코딩
- **배포 스크립트**: `-n jiwoo`로 네임스페이스 지정

#### 해결 방법
```yaml
# 모든 k8s/*.yaml 파일에서
# namespace: default  # 주석 처리
```

### 4. 이미지 풀 오류

#### 문제 상황
```
Failed to pull image "ktech4.azurecr.io/kltecho_jiwoo-backend:latest": 401 Unauthorized
```

#### 원인 분석
- **이미지 태그 불일치**: GitHub Actions는 날짜시간 태그, YAML은 latest 태그
- **인증 문제**: ACR 접근 권한

#### 해결 방법
```yaml
# k8s/jiwoo-backend-deployment.yaml
spec:
  containers:
  - name: backend
    image: ktech4.azurecr.io/kltecho_jiwoo_20250828_032716-backend  # 구체적인 태그 사용
```

### 5. 시크릿 누락 오류

#### 문제 상황
```
Error from server (NotFound): secrets "jiwoo-backend-secrets" not found
```

#### 원인 분석
- **기존 시크릿**: default 네임스페이스에 존재
- **새 네임스페이스**: jiwoo 네임스페이스에 시크릿 없음

#### 해결 방법
```bash
# cleanup-jiwoo-namespace.sh에서 기존 시크릿 삭제
kubectl delete secret backend-secrets -n default --ignore-not-found=true
kubectl delete secret jiwoo-backend-secrets -n default --ignore-not-found=true
```

## 🔧 배포 스크립트 개선사항

### 1. 상세 로깅 추가
```bash
# --debug 플래그 추가
helm install jiwoo-mariadb bitnami/mariadb \
  --values k8s/mariadb-values.yaml \
  --namespace jiwoo \
  --wait \
  --timeout 300s \
  --debug

# -v=1 플래그 추가
kubectl apply -f k8s/jiwoo-backend-secret.yaml -n jiwoo -v=1
```

### 2. 타임아웃 조정
```bash
# 600s → 300s로 조정 (사용자 요청)
--timeout 300s
```

### 3. 네임스페이스 관리
```bash
# 네임스페이스 생성 확인
kubectl create namespace jiwoo --dry-run=client -o yaml | kubectl apply -f - -v=1
```

## 📊 리소스 모니터링

### 클러스터 현황 확인
```bash
# 노드별 리소스 사용량
kubectl top nodes

# 네임스페이스별 CPU 요구량
kubectl get pods --all-namespaces -o custom-columns="NAMESPACE:.metadata.namespace,CPU-REQ:.spec.containers[*].resources.requests.cpu" | grep -v "<none>" | awk '{print $1, $2}' | awk '{split($2,arr,","); for(i in arr) print $1, arr[i]}' | sort | awk '{sum[$1]+=$2} END {for(i in sum) print i, sum[i]"m"}' | sort -k2 -nr
```

### 파드 상태 확인
```bash
# 파드 상태 확인
kubectl get pods -n jiwoo

# 파드 상세 정보
kubectl describe pod <pod-name> -n jiwoo

# 파드 로그 확인
kubectl logs <pod-name> -n jiwoo
```

## 🎯 예방 방법

### 1. 사전 리소스 확인
```bash
# 배포 전 클러스터 여유 리소스 확인
kubectl top nodes
kubectl get pods --all-namespaces | grep Pending
```

### 2. 점진적 배포
```bash
# 한 번에 하나씩 배포
helm install jiwoo-redis bitnami/redis --values k8s/redis-values.yaml --namespace jiwoo --wait
helm install jiwoo-mariadb bitnami/mariadb --values k8s/mariadb-values.yaml --namespace jiwoo --wait
helm install jiwoo-kafka bitnami/kafka --values k8s/kafka-values.yaml --namespace jiwoo --wait
```

### 3. 롤백 준비
```bash
# 배포 실패 시 롤백
helm rollback jiwoo-mariadb -n jiwoo
kubectl delete namespace jiwoo --ignore-not-found=true
```

## 📋 체크리스트

### 배포 전 확인사항
- [ ] 클러스터 리소스 여유 확인
- [ ] 이미지 태그 일치 확인
- [ ] 네임스페이스 정리 완료
- [ ] values 파일 리소스 설정 확인

### 배포 중 확인사항
- [ ] 파드 스케줄링 상태 확인
- [ ] 이미지 풀 상태 확인
- [ ] 서비스 시작 상태 확인
- [ ] 로그 오류 확인

### 배포 후 확인사항
- [ ] 모든 파드 Running 상태 확인
- [ ] 서비스 연결 확인
- [ ] 애플리케이션 동작 확인
- [ ] 리소스 사용량 모니터링
