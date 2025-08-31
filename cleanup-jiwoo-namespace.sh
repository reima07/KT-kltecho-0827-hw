#!/bin/bash

# jiwoo 네임스페이스 정리 스크립트
# 이 스크립트는 jiwoo 네임스페이스의 모든 리소스를 삭제합니다

echo "🧹 jiwoo 네임스페이스 정리 시작"
echo "=================================="

# 확인 메시지
read -p "정말로 jiwoo 네임스페이스의 모든 리소스를 삭제하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 정리가 취소되었습니다."
    exit 1
fi

# 1단계: 기존 Helm 릴리스 및 Secret 정리 (default 네임스페이스)
echo "🗑️ 1단계: 기존 Helm 릴리스 및 Secret 정리"

echo "   - 기존 Helm 릴리스 삭제 중..."
helm uninstall jiwoo-redis --ignore-not-found=true
helm uninstall jiwoo-kafka --ignore-not-found=true
helm uninstall jiwoo-mariadb --ignore-not-found=true
echo "   ✅ 기존 Helm 릴리스 삭제 완료"

echo "   - 기존 Secret 삭제 중..."
kubectl delete secret backend-secrets --ignore-not-found=true
kubectl delete secret jiwoo-backend-secrets --ignore-not-found=true
echo "   ✅ 기존 Secret 삭제 완료"

# 2단계: 애플리케이션 삭제
echo "🗑️ 2단계: 애플리케이션 삭제"

echo "   - 프론트엔드 삭제 중..."
kubectl delete -f k8s/jiwoo-frontend-deployment.yaml -n jiwoo --ignore-not-found=true
echo "   ✅ 프론트엔드 삭제 완료"

echo "   - 백엔드 삭제 중..."
kubectl delete -f k8s/jiwoo-backend-deployment.yaml -n jiwoo --ignore-not-found=true
echo "   ✅ 백엔드 삭제 완료"

echo "   - Secret 삭제 중..."
kubectl delete -f k8s/jiwoo-backend-secret.yaml -n jiwoo --ignore-not-found=true
echo "   ✅ Secret 삭제 완료"

# 3단계: 초기화 Job 삭제
echo "🗑️ 3단계: 초기화 Job 삭제"

echo "   - MariaDB 초기화 Job 삭제 중..."
kubectl delete -f k8s/jiwoo-mariadb-init-job.yaml -n jiwoo --ignore-not-found=true
echo "   ✅ MariaDB 초기화 Job 삭제 완료"

echo "   - Redis 초기화 Job 삭제 중..."
kubectl delete -f k8s/jiwoo-redis-init-job.yaml -n jiwoo --ignore-not-found=true
echo "   ✅ Redis 초기화 Job 삭제 완료"

# 4단계: Helm 릴리스 삭제
echo "🗑️ 4단계: Helm 릴리스 삭제"

echo "   - MariaDB 삭제 중..."
helm uninstall jiwoo-mariadb -n jiwoo --ignore-not-found=true
echo "   ✅ MariaDB 삭제 완료"

echo "   - Kafka 삭제 중..."
helm uninstall jiwoo-kafka -n jiwoo --ignore-not-found=true
echo "   ✅ Kafka 삭제 완료"

echo "   - Redis 삭제 중..."
helm uninstall jiwoo-redis -n jiwoo --ignore-not-found=true
echo "   ✅ Redis 삭제 완료"

echo "   - Promtail 삭제 중..."
helm uninstall promtail -n jiwoo --ignore-not-found=true
echo "   ✅ Promtail 삭제 완료"

# 5단계: 네임스페이스 삭제
echo "🗑️ 5단계: 네임스페이스 삭제"

echo "   - jiwoo 네임스페이스 삭제 중..."
kubectl delete namespace jiwoo --ignore-not-found=true
echo "   ✅ jiwoo 네임스페이스 삭제 완료"

# 6단계: 정리 완료 확인
echo "🔍 6단계: 정리 완료 확인"

echo "   - 네임스페이스 목록 확인 중..."
kubectl get namespaces | grep jiwoo || echo "   ✅ jiwoo 네임스페이스가 성공적으로 삭제되었습니다."

echo ""
echo "🎉 jiwoo 네임스페이스 정리가 성공적으로 완료되었습니다!"
echo "📝 모든 리소스가 삭제되었습니다:"
echo "   - 기존 Helm 릴리스 (default 네임스페이스)"
echo "   - 기존 Secret (default 네임스페이스)"
echo "   - 애플리케이션 (Frontend, Backend)"
echo "   - Secret"
echo "   - 초기화 Job"
echo "   - Helm 릴리스 (MariaDB, Kafka, Redis, Promtail)"
echo "   - 네임스페이스"
