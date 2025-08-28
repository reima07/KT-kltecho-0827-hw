# 🚀 0827_hw - Kubernetes 마이크로서비스 프로젝트

Full-Stack 웹 애플리케이션을 Kubernetes 환경에서 실행하는 프로젝트입니다.

## 🎯 프로젝트 개요

- **Frontend**: Vue.js + Nginx
- **Backend**: Python Flask
- **Database**: MariaDB
- **Cache**: Redis
- **Message Queue**: Apache Kafka
- **Container**: Docker
- **Orchestration**: Kubernetes + Helm
- **CI/CD**: GitHub Actions + Azure Container Registry

## 🚀 빠른 시작

### 1. 자동 배포 (권장)
```bash
# GitHub Actions를 통한 자동 빌드 및 ACR 푸시
git push origin main

# 수동 배포 스크립트 실행
./deploy-to-jiwoo-namespace.sh
```

### 2. 정리
```bash
# 전체 리소스 정리
./cleanup-jiwoo-namespace.sh
```

## 🌐 접속 정보

- **프론트엔드**: http://localhost:30080
- **백엔드 API**: http://localhost:5000

## 📚 상세 문서

프로젝트의 상세한 가이드와 문제 해결 방법은 **[docs/](./docs/)** 폴더를 참조하세요:

- **[프로젝트 개요](./docs/PROJECT_OVERVIEW.md)** - 전체 프로젝트 이해
- **[변경사항 기록](./docs/CHANGELOG.md)** - 상세한 변경 이력
- **[Kubernetes 리소스 설정](./docs/kubernetes-resources.md)** - 리소스 최적화
- **[GitHub Actions 설정](./docs/github-actions-setup.md)** - CI/CD 파이프라인
- **[배포 문제 해결](./docs/deployment-issues.md)** - 문제 해결 방법

## 🗂️ 프로젝트 구조

```
0827_hw/
├── backend/                 # Flask 백엔드
├── frontend/               # Vue.js 프론트엔드
├── k8s/                    # Kubernetes 배포 파일
├── docs/                   # 📚 상세 문서
│   ├── PROJECT_OVERVIEW.md # 프로젝트 전체 개요
│   ├── CHANGELOG.md        # 변경사항 기록
│   ├── kubernetes-resources.md    # Kubernetes 리소스 설정
│   ├── github-actions-setup.md    # GitHub Actions 설정
│   ├── deployment-issues.md       # 배포 문제 해결
│   └── index.md            # 문서 인덱스
├── .github/workflows/      # GitHub Actions 워크플로우
├── db/                     # 데이터베이스 초기화
├── deploy-to-jiwoo-namespace.sh    # 배포 스크립트
├── cleanup-jiwoo-namespace.sh      # 정리 스크립트
└── README.md               # 기본 문서
```

## 🔗 링크

- **GitHub 저장소**: https://github.com/reima07/KT-kltecho-0827-hw
- **개발자**: Jiwoo
- **목적**: Kubernetes 학습 및 Azure CI/CD 구축

---

**이 프로젝트는 Kubernetes와 Azure 클라우드 기술을 학습하기 위한 실습 프로젝트입니다.** 