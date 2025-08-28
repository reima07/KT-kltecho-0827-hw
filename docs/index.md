# 📚 0827_hw 프로젝트 문서

이 폴더는 0827_hw 프로젝트의 모든 상세한 문서들을 포함합니다.

## 📋 문서 목록

### 📖 프로젝트 개요
- **[PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)** - 프로젝트 전체 개요 및 아키텍처
- **[CHANGELOG.md](./CHANGELOG.md)** - 상세한 변경 이력

### 🔧 기술 가이드
- **[Kubernetes 리소스 설정](./kubernetes-resources.md)** - 리소스 최적화 가이드
- **[GitHub Actions 설정](./github-actions-setup.md)** - CI/CD 파이프라인 가이드
- **[배포 문제 해결](./deployment-issues.md)** - 배포 문제 해결 가이드

## 🎯 문서 사용 가이드

### 프로젝트 시작 시
1. **PROJECT_OVERVIEW.md** - 프로젝트 전체 이해
2. **CHANGELOG.md** - 주요 변경사항 확인

### 초기 설정 시
1. **github-actions-setup.md** - GitHub Actions와 ACR 설정
2. **kubernetes-resources.md** - 리소스 설정 확인

### 배포 시
1. **deployment-issues.md** - 문제 발생 시 참조
2. **kubernetes-resources.md** - 리소스 모니터링

### 문제 해결 시
1. **deployment-issues.md** - 문제별 해결 방법
2. **github-actions-setup.md** - CI/CD 관련 문제

## 🔗 관련 파일

### 프로젝트 루트
- **[README.md](../README.md)** - 기본 프로젝트 설명

### 설정 파일
- **[.github/workflows/build-and-push.yml](../.github/workflows/build-and-push.yml)** - CI/CD 워크플로우
- **[deploy-to-jiwoo-namespace.sh](../deploy-to-jiwoo-namespace.sh)** - 배포 스크립트
- **[cleanup-jiwoo-namespace.sh](../cleanup-jiwoo-namespace.sh)** - 정리 스크립트

### Kubernetes 설정
- **[k8s/mariadb-values.yaml](../k8s/mariadb-values.yaml)** - MariaDB 리소스 설정
- **[k8s/redis-values.yaml](../k8s/redis-values.yaml)** - Redis 리소스 설정
- **[k8s/kafka-values.yaml](../k8s/kafka-values.yaml)** - Kafka 리소스 설정

---

**이 문서들은 프로젝트 진행 과정에서 발생한 실제 문제들과 해결 방법을 바탕으로 작성되었습니다.**
