# Kubernetes 리소스 최적화 가이드

## 📊 문제 상황 분석

### 초기 문제점
- **MariaDB 스케줄링 실패**: CPU 500m 요구로 인한 `Insufficient cpu` 오류
- **클러스터 리소스 부족**: 다른 사용자들의 서비스들이 많은 리소스 사용
- **배포 지연**: 리소스 부족으로 인한 파드 스케줄링 실패

### 클러스터 현황 (2025-01-27 기준)
- **총 노드**: 8개 (aks-agentpool 3개 + aks-userpool 5개)
- **CPU 사용률**: 높음 (다른 사용자들의 MariaDB들이 500m씩 요구)
- **메모리 사용률**: 37-59% (여유 있음)

## 🔧 리소스 최적화 설정

### MariaDB 설정 (`k8s/mariadb-values.yaml`)
```yaml
primary:
  resources:
    requests:
      cpu: 250m        # 기존 500m에서 50% 감소
      memory: 512Mi    # 적절한 데이터베이스 메모리
    limits:
      cpu: 500m        # 피크 시 사용 가능
      memory: 1Gi      # 최대 메모리 제한
```

### Redis 설정 (`k8s/redis-values.yaml`)
```yaml
master:
  resources:
    requests:
      cpu: 100m        # 캐시/세션 관리용
      memory: 128Mi    # 세션 데이터 저장
    limits:
      cpu: 200m        # 피크 시 사용
      memory: 256Mi    # 최대 메모리
```

### Kafka 설정 (`k8s/kafka-values.yaml`)
```yaml
controller:
  resources:
    requests:
      cpu: 200m        # 메시지 큐 처리
      memory: 256Mi    # 메시지 버퍼
    limits:
      cpu: 400m        # 피크 시 사용
      memory: 512Mi    # 최대 메모리

zookeeper:
  resources:
    requests:
      cpu: 100m        # 분산 조정
      memory: 128Mi    # 메타데이터 저장
    limits:
      cpu: 200m        # 피크 시 사용
      memory: 256Mi    # 최대 메모리
```

## 📈 최적화 결과

### 리소스 요구량 비교
| 서비스 | CPU (기존) | CPU (최적화) | Memory (최적화) |
|--------|------------|--------------|-----------------|
| MariaDB | 500m | 250m | 512Mi |
| Redis | - | 100m | 128Mi |
| Kafka | 200m | 200m | 256Mi |
| **총합** | **700m** | **550m** | **896Mi** |

### 개선 효과
- **CPU 요구량**: 21% 감소 (700m → 550m)
- **스케줄링 성공률**: 크게 향상 예상
- **안정성**: 적절한 리소스로 안정적 운영 가능

## 🎯 권장사항

### 개발/테스트 환경
- **MariaDB**: 250m CPU, 512Mi Memory
- **Redis**: 100m CPU, 128Mi Memory  
- **Kafka**: 200m CPU, 256Mi Memory

### 프로덕션 환경
- **MariaDB**: 500m CPU, 1Gi Memory
- **Redis**: 200m CPU, 256Mi Memory
- **Kafka**: 400m CPU, 512Mi Memory

## 📋 모니터링 명령어

### 리소스 사용량 확인
```bash
# 노드별 리소스 사용량
kubectl top nodes

# 파드별 리소스 사용량
kubectl top pods -n jiwoo

# 네임스페이스별 CPU 요구량
kubectl get pods --all-namespaces -o custom-columns="NAMESPACE:.metadata.namespace,CPU-REQ:.spec.containers[*].resources.requests.cpu" | grep -v "<none>" | awk '{print $1, $2}' | awk '{split($2,arr,","); for(i in arr) print $1, arr[i]}' | sort | awk '{sum[$1]+=$2} END {for(i in sum) print i, sum[i]"m"}' | sort -k2 -nr
```

### 로그 확인
```bash
# MariaDB 로그
kubectl logs -n jiwoo jiwoo-mariadb-0

# Redis 로그
kubectl logs -n jiwoo jiwoo-redis-master-0

# Kafka 로그
kubectl logs -n jiwoo jiwoo-kafka-controller-0
```

## 🔄 다음 단계

1. **배포 테스트**: 최적화된 설정으로 배포 실행
2. **성능 모니터링**: 실제 리소스 사용량 추적
3. **조정**: 필요시 리소스 요구량 미세 조정
4. **문서화**: 프로덕션 환경 설정 가이드 작성
