# 🚀 0827_hw 프로젝트 - Full-Stack Kubernetes 애플리케이션

## 📋 프로젝트 개요

### 🎯 목표
- **1단계**: 로컬 Rancher Desktop Kubernetes에 Full-Stack 웹 애플리케이션 배포
- **2단계**: Azure Cloud로 CI/CD 파이프라인 구축하여 프로덕션 배포

### 🏗️ 기술 스택
```
Frontend: Vue.js + Nginx
Backend: Python Flask
Database: MariaDB
Cache: Redis
Message Queue: Apache Kafka
Container: Docker
Orchestration: Kubernetes
Package Manager: Helm (Bitnami)
Cloud: Azure (예정)
CI/CD: GitHub Actions (예정)
```

## 🏛️ 아키텍처

### 전체 구조
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Infrastructure│
│   (Vue.js)      │◄──►│   (Flask)       │◄──►│   (K8s + Helm)  │
│   Port: 30080   │    │   Port: 5000    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   MariaDB       │    │   Redis         │
│   (Proxy)       │    │   (Database)    │    │   (Cache/Log)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   Kafka         │
                                              │   (Event Log)   │
                                              └─────────────────┘
```

### 데이터 플로우
1. **사용자 요청** → Frontend (Vue.js)
2. **API 호출** → Nginx → Backend (Flask)
3. **데이터 처리** → MariaDB (저장) / Redis (캐시)
4. **이벤트 로깅** → Kafka (비동기)
5. **응답 반환** → Frontend

## 📊 현재 진행 상황

### ✅ 완료된 작업

#### 1. 로컬 Kubernetes 배포
- [x] **Helm Charts 설정** (Redis, Kafka, MariaDB)
- [x] **Kubernetes 배포 파일 생성** (jiwoo- 접두사)
- [x] **Docker 이미지 빌드 및 푸시** (Docker Hub → Azure Container Registry)
- [x] **자동화 스크립트 생성** (deploy-to-jiwoo-namespace.sh, cleanup-jiwoo-namespace.sh)
- [x] **초기화 Job 생성** (DB/Redis 자동 설정)
- [x] **jiwoo 네임스페이스 설정** (리소스 격리)

#### 2. 애플리케이션 기능
- [x] **로그인/회원가입 시스템**
- [x] **메시지 저장 및 검색**
- [x] **Redis 로그 조회**
- [x] **Kafka API 통계 로깅**
- [x] **사용자별 메시지 관리**

#### 3. 문제 해결
- [x] **이미지 Pull 문제** → Docker Hub 사용
- [x] **데이터베이스 연결 문제** → 환경변수 설정
- [x] **테이블 없음 문제** → 자동화 Job 생성
- [x] **Kafka CrashLoopBackOff** → 설정 최적화
- [x] **사용자 정보 미저장** → SQL 쿼리 수정
- [x] **배포 시간 최적화** → 타임아웃 조정
- [x] **CI/CD 파이프라인 구축** → GitHub Actions + 수동 배포

#### 4. CI/CD 파이프라인
- [x] **GitHub Actions 워크플로우 생성** (Docker 빌드 + ACR 푸시)
- [x] **수동 배포 스크립트 생성** (jiwoo 네임스페이스)
- [x] **이미지 태깅 시스템** (날짜시간 기반)
- [x] **Azure Container Registry 연동** 준비

### 🔄 진행 중인 작업
- [ ] **Git 저장소 설정**
- [ ] **GitHub Actions Secrets 설정**
- [ ] **Azure Container Registry 설정**

### 📋 예정된 작업

#### 1. Azure 클라우드 배포
- [ ] **Azure Container Registry 생성**
- [ ] **Azure Kubernetes Service 클러스터 생성**
- [ ] **GitHub Actions Secrets 설정**
- [ ] **클라우드 환경 배포 테스트**

#### 2. 추가 기능 (선택사항)
- [ ] **Event Hub 연동** (API 통계 저장)
- [ ] **세션 관리 개선** (Redis 활용)
- [ ] **모니터링 시스템** (Prometheus/Grafana)
- [ ] **로드 밸런싱** (HAProxy/Nginx)

## 🛠️ 배포 정보

### 현재 접속 정보
- **프론트엔드**: http://localhost:30080
- **백엔드 API**: http://localhost:5000

### 서비스 상태
```
✅ Frontend: Running (Vue.js + Nginx)
✅ Backend: Running (Flask)
✅ MariaDB: Running (Database)
✅ Redis: Running (Cache/Log)
✅ Kafka: Running (3개 컨트롤러)
✅ 초기화 Job: Completed
```

### 주요 기능
- ✅ **사용자 인증**: 로그인/회원가입
- ✅ **메시지 관리**: 저장, 검색, 사용자별 분류
- ✅ **로그 시스템**: Redis 기반 실시간 로그
- ✅ **API 모니터링**: Kafka 기반 통계 수집

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
├── deploy-to-jiwoo-namespace.sh    # 배포 스크립트
├── cleanup-jiwoo-namespace.sh      # 정리 스크립트
├── CHANGELOG.md             # 변경사항 기록
├── PROJECT_OVERVIEW.md      # 프로젝트 개요
└── README.md               # 기본 문서
```

## 🔧 주요 설정

### Helm Charts (Bitnami)
- **Redis**: 비밀번호 `New1234!`, standalone 모드
- **Kafka**: 3개 컨트롤러, SASL 인증 비활성화
- **MariaDB**: 사용자 `jiwoo`, 비밀번호 `jiwoo1234!`, DB `jiwoo_db`

### Docker 이미지
- **Backend**: `npr04191/0827_hw_local:backend`
- **Frontend**: `npr04191/0827_hw_local:frontend`

### Kubernetes 리소스
- **네임스페이스**: default
- **접두사**: jiwoo- (모든 리소스)
- **서비스 타입**: ClusterIP (내부), NodePort (외부)

## 🎓 학습 내용

### Kubernetes 개념
- **Job vs Deployment**: 일회성 작업 vs 지속적 서비스
- **서비스 디스커버리**: 내부 DNS를 통한 서비스 연결
- **Helm**: 패키지 매니저를 통한 인프라 관리
- **ConfigMap/Secret**: 설정 및 민감 정보 관리

### 아키텍처 패턴
- **마이크로서비스**: 독립적인 서비스 구성
- **API Gateway**: Nginx를 통한 프록시
- **이벤트 기반**: Kafka를 통한 비동기 로깅
- **CQRS**: 명령과 조회 분리

### 자동화
- **초기화 자동화**: Job을 통한 DB/Redis 초기화
- **배포 자동화**: 스크립트를 통한 일관된 배포
- **타임아웃 최적화**: 효율적인 배포 시간 관리

## 🚀 다음 단계

### 1. Git 저장소 설정
```bash
# 새 GitHub 저장소 생성
# 원격 저장소 연결
git remote add origin https://github.com/npr04191/0827_hw.git
git push -u origin main
```

### 2. CI/CD 파이프라인 구축
```yaml
# .github/workflows/deploy.yml
name: Deploy to Azure
on: [push]
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Build and push Docker images
    - name: Deploy to Azure Kubernetes Service
```

### 3. Azure 리소스 생성
```bash
# Azure Container Registry
az acr create --name jiwooacr --resource-group myResourceGroup

# Azure Kubernetes Service
az aks create --resource-group myResourceGroup --name jiwoo-aks --node-count 3
```

## 📞 연락처 및 참고사항

- **개발자**: Jiwoo
- **Docker Hub**: npr04191
- **프로젝트**: 0827_hw_local
- **목적**: Kubernetes 학습 및 Azure CI/CD 구축

---

**이 프로젝트는 Kubernetes와 Azure 클라우드 기술을 학습하기 위한 실습 프로젝트입니다.**
