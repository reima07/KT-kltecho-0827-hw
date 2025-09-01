#!/bin/bash

# jiwoo 네임스페이스 배포 스크립트
# 이 스크립트는 jiwoo 네임스페이스에 모든 리소스를 배포합니다

echo "🚀 jiwoo 네임스페이스 배포 시작"
echo "=================================="

# 1단계: jiwoo 네임스페이스 생성
echo "📁 1단계: jiwoo 네임스페이스 생성"
kubectl create namespace jiwoo --dry-run=client -o yaml | kubectl apply -f - -v=1
echo "✅ 네임스페이스 생성 완료"

# 2단계: Helm 저장소 추가
echo "📦 2단계: Helm 저장소 추가"
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
echo "✅ Helm 저장소 추가 완료"

# 3단계: Helm 차트 설치 (인프라)
echo "🏗️ 3단계: Helm 차트 설치 (인프라)"

echo "   - Redis 설치 중..."
helm install jiwoo-redis bitnami/redis \
  --values k8s/redis-values.yaml \
  --namespace jiwoo \
  --wait \
  --timeout 300s \
  --debug
echo "   ✅ Redis 설치 완료"

echo "   - Kafka 설치 중..."
helm install jiwoo-kafka bitnami/kafka \
  --values k8s/kafka-values.yaml \
  --namespace jiwoo \
  --wait \
  --timeout 300s \
  --debug
echo "   ✅ Kafka 설치 완료"

echo "   - MariaDB 설치 중..."
helm install jiwoo-mariadb bitnami/mariadb \
  --values k8s/mariadb-values.yaml \
  --namespace jiwoo \
  --wait \
  --timeout 300s \
  --debug
echo "   ✅ MariaDB 설치 완료"

echo "   - Promtail 설치 중..."
helm install promtail grafana/promtail \
  --namespace jiwoo \
  --set "config.lokiAddress=http://collector.lgtm.20.249.154.255.nip.io/loki" \
  --wait \
  --timeout 300s \
  --debug
echo "   ✅ Promtail 설치 완료"

# 4단계: 초기화 Job 실행
echo "🔧 4단계: 초기화 Job 실행"

echo "   - MariaDB 초기화 Job 실행 중..."
kubectl apply -f k8s/jiwoo-mariadb-init-job.yaml -n jiwoo -v=1
kubectl wait --for=condition=complete job/jiwoo-mariadb-init --timeout=120s -n jiwoo
echo "   ✅ MariaDB 초기화 완료"

echo "   - Redis 초기화 Job 실행 중..."
kubectl apply -f k8s/jiwoo-redis-init-job.yaml -n jiwoo -v=1
kubectl wait --for=condition=complete job/jiwoo-redis-init --timeout=120s -n jiwoo
echo "   ✅ Redis 초기화 완료"

# 5단계: 애플리케이션 배포
echo "🚀 5단계: 애플리케이션 배포"

echo "   - Secret 적용 중..."
kubectl apply -f k8s/jiwoo-backend-secret.yaml -n jiwoo -v=1
kubectl apply -f k8s/jiwoo-acr-secret.yaml -n jiwoo -v=1
echo "   ✅ Secret 적용 완료"

echo "   - 백엔드 배포 중..."
kubectl apply -f k8s/jiwoo-backend-deployment.yaml -n jiwoo -v=1
kubectl rollout status deployment/jiwoo-backend --timeout=300s -n jiwoo
echo "   ✅ 백엔드 배포 완료"

echo "   - 프론트엔드 배포 중..."
kubectl apply -f k8s/jiwoo-frontend-deployment.yaml -n jiwoo -v=1
kubectl rollout status deployment/jiwoo-frontend --timeout=300s -n jiwoo
echo "   ✅ 프론트엔드 배포 완료"

echo "   - FastAPI 배포 중..."
kubectl apply -f k8s/jiwoo-fastapi-deployment.yaml -n jiwoo -v=1
kubectl rollout status deployment/jiwoo-fastapi --timeout=300s -n jiwoo
echo "   ✅ FastAPI 배포 완료"

# 6단계: 배포 상태 확인
echo "🔍 6단계: 배포 상태 확인"
echo ""

echo "=== Pod 상태 ==="
kubectl get pods -n jiwoo

echo ""
echo "=== 서비스 상태 ==="
kubectl get services -n jiwoo

echo ""
echo "=== 배포 상태 ==="
kubectl get deployments -n jiwoo

echo ""
echo "🎉 배포가 성공적으로 완료되었습니다!"
echo "📊 접속 정보:"
echo "   - 프론트엔드: LoadBalancer IP 확인 필요"
echo "   - 백엔드 API: ClusterIP (내부 접속)"
echo "   - Grafana Loki: http://grafana.20.249.154.255.nip.io"
echo ""
echo "🔍 LoadBalancer IP 확인:"
echo "   kubectl get service jiwoo-frontend-service -n jiwoo"
echo ""
echo "🔧 유용한 명령어:"
echo "   - 전체 상태 확인: kubectl get all -n jiwoo"
echo "   - Pod 로그 확인: kubectl logs <pod-name> -n jiwoo"
echo "   - Pod 상세 정보: kubectl describe pod <pod-name> -n jiwoo"
echo "   - Promtail 상태: kubectl get pods -n jiwoo | grep promtail"
