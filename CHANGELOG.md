# CHANGELOG - 0827_hw 프로젝트

## 📋 프로젝트 개요
- **목표**: Full-stack 웹 애플리케이션을 로컬 Rancher Desktop Kubernetes에 배포 후 Azure로 CI/CD
- **기술 스택**: Python Flask (Backend) + Vue.js (Frontend) + MariaDB + Redis + Kafka
- **현재 상태**: 로컬 K8s에서 완전히 동작 중

## 🚀 주요 변경사항 (원본 대비)

### 1. Helm Charts 설정 (Bitnami)

#### Redis 설정 (`k8s/redis-values.yaml`)
```yaml
auth:
  enabled: true
  password: "New1234!"
architecture: standalone
service:
  type: ClusterIP
persistence:
  enabled: true
  size: 1Gi
```

#### Kafka 설정 (`k8s/kafka-values.yaml`)
```yaml
controller:
  replicaCount: 3  # 처음 1개 → 3개로 변경
zookeeper:
  enabled: true
  replicaCount: 3
persistence:
  enabled: true
  size: 1Gi
service:
  type: ClusterIP
auth:
  enabled: false  # SASL 인증 비활성화
```

#### MariaDB 설정 (`k8s/mariadb-values.yaml`)
```yaml
auth:
  enabled: true
  username: "jiwoo"
  password: "jiwoo1234!"
  database: "jiwoo_db"
primary:
  persistence:
    enabled: true
    size: 1Gi
service:
  type: ClusterIP
```

### 2. 데이터베이스 스키마 변경 (`db/init.sql`)

**완전히 재작성:**
```sql
-- 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS jiwoo_db;
USE jiwoo_db;

-- 사용자 테이블 생성
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 메시지 테이블 생성
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT NOT NULL,
    user_id VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);

-- 샘플 데이터 삽입
INSERT IGNORE INTO users (username, password) VALUES 
('admin', 'admin123'),
('testuser', 'test123');
```

### 3. Kubernetes 배포 파일 생성

#### 백엔드 배포 (`k8s/jiwoo-backend-deployment.yaml`)
- **이름 변경**: `backend` → `jiwoo-backend`
- **이미지**: `npr04191/0827_hw_local:backend`
- **환경변수 추가**: `MYSQL_DATABASE: "jiwoo_db"`
- **서비스 이름**: `jiwoo-backend-service`

#### 프론트엔드 배포 (`k8s/jiwoo-frontend-deployment.yaml`)
- **이름 변경**: `frontend` → `jiwoo-frontend`
- **이미지**: `npr04191/0827_hw_local:frontend`
- **서비스 이름**: `jiwoo-frontend-service`

#### Secret 설정 (`k8s/jiwoo-backend-secret.yaml`)
```yaml
FLASK_SECRET_KEY: "andpamRlZmluaXRlbHlzZWN1cmVrZXlmb3JqaXdvbyI="  # jiwoo flask secret key
MYSQL_PASSWORD: "aml3b28xMjM0IQ=="  # jiwoo1234!를 base64로 인코딩
REDIS_PASSWORD: "TmV3MTIzNCE="  # New1234!를 base64로 인코딩
KAFKA_PASSWORD: ""  # Kafka는 인증 없이 설정
```

### 4. 백엔드 코드 수정 (`backend/app.py`)

#### 데이터베이스 연결 수정
```python
# [변경사항] database를 환경변수로 변경하여 jiwoo_db 사용
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'my-mariadb'),
        user=os.getenv('MYSQL_USER', 'testuser'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE', 'jiwoo_db'),  # [변경] testdb → jiwoo_db
        connect_timeout=30
    )
```

#### Kafka 연결 수정
```python
# [변경사항] SASL 인증 제거하여 단순 연결로 변경
def get_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=os.getenv('KAFKA_SERVERS', 'my-kafka:9092'),
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
        # [변경] SASL 인증 설정 제거 (security_protocol, sasl_mechanism 등)
    )
```

#### 메시지 저장 시 user_id 추가 (최근 수정)
```python
# [변경사항] user_id도 함께 저장하도록 SQL 쿼리 수정
sql = "INSERT INTO messages (message, user_id, created_at) VALUES (%s, %s, %s)"
cursor.execute(sql, (data['message'], user_id, datetime.now()))
```

### 5. 프론트엔드 설정 수정 (`frontend/nginx.conf`)

```nginx
location /api/ {
    rewrite ^/api/(.*) /$1 break;
    # [변경사항] 백엔드 서비스 이름을 jiwoo- 접두사로 변경
    proxy_pass http://jiwoo-backend-service:5000;  # [변경] backend-service → jiwoo-backend-service
}
```

### 6. 자동화 스크립트 생성

#### 배포 스크립트 (`build-and-deploy.sh`)
```bash
#!/bin/bash
# Docker 이미지 빌드
docker build -t jiwoo-backend:latest ./backend
docker build -t jiwoo-frontend:latest ./frontend

# Helm으로 인프라 설치
helm install jiwoo-redis bitnami/redis -f k8s/redis-values.yaml
helm install jiwoo-kafka bitnami/kafka -f k8s/kafka-values.yaml
helm install jiwoo-mariadb bitnami/mariadb -f k8s/mariadb-values.yaml

# 서비스 준비 대기 (타임아웃 최적화)
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=redis --timeout=120s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=kafka --timeout=120s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=mariadb --timeout=120s

# 초기화 Job 실행
kubectl apply -f k8s/jiwoo-mariadb-init-job.yaml
kubectl apply -f k8s/jiwoo-redis-init-job.yaml

# Job 완료 대기 (타임아웃 최적화)
kubectl wait --for=condition=complete job/jiwoo-mariadb-init --timeout=60s
kubectl wait --for=condition=complete job/jiwoo-redis-init --timeout=60s

# 애플리케이션 배포
kubectl apply -f k8s/jiwoo-backend-secret.yaml
kubectl apply -f k8s/jiwoo-backend-deployment.yaml
kubectl apply -f k8s/jiwoo-frontend-deployment.yaml
```

#### 정리 스크립트 (`cleanup.sh`)
```bash
#!/bin/bash
# 애플리케이션 삭제
kubectl delete -f k8s/jiwoo-frontend-deployment.yaml
kubectl delete -f k8s/jiwoo-backend-deployment.yaml
kubectl delete -f k8s/jiwoo-backend-secret.yaml

# 초기화 Job 삭제
kubectl delete -f k8s/jiwoo-mariadb-init-job.yaml
kubectl delete -f k8s/jiwoo-redis-init-job.yaml

# Helm 릴리스 삭제
helm uninstall jiwoo-mariadb
helm uninstall jiwoo-kafka
helm uninstall jiwoo-redis

# Docker 이미지 삭제
docker rmi jiwoo-backend:latest
docker rmi jiwoo-frontend:latest
```

### 7. 자동화 Job 생성

#### MariaDB 초기화 Job (`k8s/jiwoo-mariadb-init-job.yaml`)
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: jiwoo-mariadb-init
spec:
  template:
    spec:
      containers:
      - name: mariadb-init
        image: docker.io/bitnami/mariadb:12.0.2-debian-12-r0
        command:
        - /bin/bash
        - -c
        - |
          # MariaDB 준비 대기
          until mysql -h jiwoo-mariadb -u jiwoo -pjiwoo1234! -e "SELECT 1"; do
            sleep 5
          done
          
          # 데이터베이스 및 테이블 생성
          mysql -h jiwoo-mariadb -u jiwoo -pjiwoo1234! << 'EOF'
          CREATE DATABASE IF NOT EXISTS jiwoo_db;
          USE jiwoo_db;
          
          CREATE TABLE IF NOT EXISTS users (
              id INT AUTO_INCREMENT PRIMARY KEY,
              username VARCHAR(255) UNIQUE NOT NULL,
              password VARCHAR(255) NOT NULL,
              created_at DATETIME DEFAULT CURRENT_TIMESTAMP
          );
          
          CREATE TABLE IF NOT EXISTS messages (
              id INT AUTO_INCREMENT PRIMARY KEY,
              message TEXT NOT NULL,
              user_id VARCHAR(255),
              created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
              INDEX idx_user_id (user_id),
              INDEX idx_created_at (created_at)
          );
          
          INSERT IGNORE INTO users (username, password) VALUES 
          ('admin', 'admin123'),
          ('testuser', 'test123');
          EOF
      restartPolicy: OnFailure
```

#### Redis 초기화 Job (`k8s/jiwoo-redis-init-job.yaml`)
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: jiwoo-redis-init
spec:
  template:
    spec:
      containers:
      - name: redis-init
        image: docker.io/bitnami/redis:8.2.1-debian-12-r0
        command:
        - /bin/bash
        - -c
        - |
          # Redis 준비 대기
          until redis-cli -h jiwoo-redis-master -a New1234! ping; do
            sleep 5
          done
          
          # 테스트 데이터 추가
          redis-cli -h jiwoo-redis-master -a New1234! lpush api_logs '{"timestamp":"2025-08-28T00:30:00","action":"init","details":"Redis 초기화 완료"}'
          redis-cli -h jiwoo-redis-master -a New1234! lpush api_logs '{"timestamp":"2025-08-28T00:30:01","action":"test","details":"Redis 연결 테스트 성공"}'
      restartPolicy: OnFailure
```

## 🔧 해결된 문제들

### 1. 이미지 Pull 문제
- **문제**: `ErrImageNeverPull` 오류
- **해결**: Docker Hub 사용자 저장소로 변경 (`npr04191/0827_hw_local`)

### 2. 데이터베이스 연결 문제
- **문제**: `Unknown database 'testdb'` 오류
- **해결**: 환경변수로 데이터베이스 이름 변경 (`jiwoo_db`)

### 3. 테이블 없음 문제
- **문제**: `Table 'jiwoo_db.users' doesn't exist`
- **해결**: 자동화된 초기화 Job 생성

### 4. Kafka CrashLoopBackOff
- **문제**: 컨트롤러 수 불일치 및 SASL 인증 문제
- **해결**: 컨트롤러 수 조정 및 SASL 인증 비활성화

### 5. 사용자 정보 미저장 문제
- **문제**: 메시지 저장 시 "사용자 없음" 표시
- **해결**: SQL 쿼리에 `user_id` 추가

### 6. 배포 시간 최적화
- **문제**: 300초 타임아웃으로 인한 긴 배포 시간
- **해결**: 120초/60초로 최적화

## 📊 현재 상태

### 접속 정보
- **프론트엔드**: http://localhost:30080
- **백엔드 API**: http://localhost:5000

### 서비스 상태
- ✅ Frontend: Running
- ✅ Backend: Running  
- ✅ MariaDB: Running
- ✅ Redis: Running
- ✅ Kafka: Running (3개 컨트롤러)
- ✅ 초기화 Job: Completed

### 주요 기능
- ✅ 로그인/회원가입
- ✅ 메시지 저장 (사용자 정보 포함)
- ✅ 메시지 검색
- ✅ Redis 로그 조회
- ✅ Kafka API 통계 로깅

### CI/CD 파이프라인
- ✅ GitHub Actions 워크플로우 생성
- ✅ Azure Container Registry 설정 준비
- ✅ Azure Kubernetes Service 배포 준비

## 🚀 다음 단계 (CI/CD)

1. **Git 저장소 설정**
2. **GitHub Actions 워크플로우 생성** ✅
3. **Azure Container Registry 설정**
4. **Azure Kubernetes Service 배포**

## 🔄 최근 변경사항 (2025-01-27)

### 8. Azure CI/CD 파이프라인 구축

#### GitHub Actions 워크플로우 생성
- **파일**: `.github/workflows/build-and-push.yml`
  - Docker 이미지 빌드 및 ACR 푸시 자동화
  - 백엔드/프론트엔드 병렬 빌드
  - 한국 시간(KST) 기반 날짜시간 태그 (YYYYMMDD_HHMMSS) 및 latest 태그 생성
  - main, master, develop 브랜치 푸시 시 트리거
  - 이미지 이름: `kltecho_jiwoo_날짜시간-backend/frontend`
  - ACR Secrets 변수화: `ACR_LOGIN_SERVER`, `ACR_USERNAME`, `ACR_PASSWORD`

#### 수동 배포 스크립트 생성
- **파일**: `deploy-to-jiwoo-namespace.sh`
  - jiwoo 네임스페이스에 모든 리소스 배포
  - Helm 차트 설치 (Redis, Kafka, MariaDB)
  - 초기화 Job 실행
  - 애플리케이션 배포
  - 배포 상태 확인

- **파일**: `cleanup-jiwoo-namespace.sh`
  - jiwoo 네임스페이스의 모든 리소스 삭제
  - 안전한 정리 (확인 메시지 포함)
  - 네임스페이스까지 완전 삭제

#### Docker 이미지 레지스트리 변경
- **이전**: Docker Hub (`npr04191/0827_hw_local`)
- **현재**: Azure Container Registry (`ktech4.azurecr.io/kltecho_jiwoo-*`)

#### Kubernetes 배포 파일 업데이트
- **백엔드**: `k8s/jiwoo-backend-deployment.yaml`
  ```yaml
  # [변경사항] Docker Hub → ACR 이미지 변경
  image: ktech4.azurecr.io/kltecho_jiwoo-backend:latest
  ```

- **프론트엔드**: `k8s/jiwoo-frontend-deployment.yaml`
  ```yaml
  # [변경사항] Docker Hub → ACR 이미지 변경
  image: ktech4.azurecr.io/kltecho_jiwoo-frontend:latest
  ```

#### GitHub Secrets 설정 가이드 생성
- **파일**: `GITHUB_SECRETS_SETUP.md`
  - ACR 인증 정보 설정 방법
  - Azure 서비스 주체 생성 가이드
  - AKS 클러스터 연결 방법
  - 보안 주의사항 및 체크리스트

### 9. 워크플로우 기능 상세

#### 빌드 및 푸시 워크플로우 (`build-and-push.yml`)
```yaml
# 주요 기능
- Azure Container Registry 로그인
- Docker Buildx 멀티 플랫폼 빌드
- 날짜 기반 이미지 태깅
- 백엔드/프론트엔드 병렬 처리
```

#### AKS 배포 워크플로우 (`deploy-to-aks.yml`)
```yaml
# 주요 기능
- Azure CLI 자동 로그인
- AKS 클러스터 자격 증명 가져오기
- Helm 차트 자동 설치 (Redis, Kafka, MariaDB)
- 초기화 Job 자동 실행
- 배포 상태 실시간 모니터링
```

### 10. 필요한 GitHub Secrets

#### Azure Container Registry (3개만)
- `ACR_LOGIN_SERVER`: ACR 서버 주소 (예: ktech4.azurecr.io)
- `ACR_USERNAME`: ACR 관리자 사용자명
- `ACR_PASSWORD`: ACR 관리자 비밀번호

#### 참고: 불필요한 Secrets
- ~~AZURE_CREDENTIALS~~ - ACR만 사용하므로 불필요
- ~~AZURE_RESOURCE_GROUP~~ - ACR만 사용하므로 불필요
- ~~AKS_CLUSTER_NAME~~ - 직접 배포하므로 불필요

### 11. 배포 프로세스

#### 1단계: 코드 푸시
```bash
git push origin main
```

#### 2단계: 자동 빌드 (GitHub Actions)
- Docker 이미지 빌드
- ACR에 이미지 푸시
- 날짜 태그 및 latest 태그 생성

#### 3단계: 자동 배포 (GitHub Actions)
- AKS 클러스터 연결
- Helm 차트 설치 (인프라)
- 초기화 Job 실행
- 애플리케이션 배포
- 배포 상태 확인

### 12. 최종 배포 구조

#### 하이브리드 배포 방식
- **빌드**: GitHub Actions 자동화 (Docker 이미지 빌드 + ACR 푸시)
- **배포**: 수동 스크립트 (학습용 kubectl 명령어)
- **네임스페이스**: jiwoo 전용 네임스페이스 사용
- **시간대**: 한국 시간(KST) 기반 이미지 태깅

#### 배포 프로세스
1. **코드 푸시** → GitHub Actions 자동 빌드 (한국 시간 태그)
2. **스크립트 실행** → `./deploy-to-jiwoo-namespace.sh`
3. **정리 필요시** → `./cleanup-jiwoo-namespace.sh`

#### 접속 정보
- **프론트엔드**: http://localhost:30080
- **백엔드 API**: http://localhost:5000
- **네임스페이스**: jiwoo

#### GitHub 저장소
- **URL**: https://github.com/reima07/KT-kltecho-0827-hw
- **상태**: 완전히 업로드됨 (21개 파일, 1,527줄 추가)

## 📝 학습 내용

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
- **타임아웃 최적화**: 효율적인 배포 시간 관리
- **CI/CD 자동화**: GitHub Actions를 통한 Azure 클라우드 배포

## 📁 프로젝트 구조 (최종)

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
│   └── build-and-push.yml   # Docker 빌드 및 ACR 푸시 (한국 시간 태깅)
├── deploy-to-jiwoo-namespace.sh    # 배포 스크립트
├── cleanup-jiwoo-namespace.sh      # 정리 스크립트
├── env.example               # 환경변수 템플릿 (참고용)
├── CHANGELOG.md             # 변경사항 기록
├── PROJECT_OVERVIEW.md      # 프로젝트 개요
└── README.md               # 기본 문서
```
