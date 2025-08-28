# K8s 마이크로서비스 데모 - Jiwoo 버전

이 프로젝트는 Kubernetes 환경에서 Redis, MariaDB, Kafka를 활용하는 마이크로서비스 데모입니다.

## 🚀 주요 변경사항 (원본 대비)

### 1. 리소스 이름 변경
- 모든 Kubernetes 리소스에 `jiwoo-` 접두사 추가
- 예: `backend` → `jiwoo-backend`, `frontend` → `jiwoo-frontend`

### 2. 데이터베이스 설정 변경
- 데이터베이스 이름: `testdb` → `jiwoo_db`
- 사용자: `testuser` → `jiwoo`
- 비밀번호: `testpassword` → `jiwoo1234!`

### 3. Redis 설정 변경
- 비밀번호: `undIJzFiRi` → `New1234!`

### 4. Kafka 설정 변경
- 컨트롤러 수: 1개 → 3개 (프로덕션 권장)
- 인증 방식: SASL → 인증 비활성화 (개발 환경)

### 5. 이미지 저장소 변경
- Docker Hub 계정: `giglepeople` → `npr04191`
- 이미지 이름: `0827_hw_local`

## 📋 주요 기능

### 1. 사용자 관리
- 회원가입: 새로운 사용자 등록
- 로그인/로그아웃: 세션 기반 인증
- Redis를 활용한 세션 관리

### 2. 메시지 관리 (MariaDB)
- 메시지 저장: 사용자가 입력한 메시지를 DB에 저장
- 메시지 조회: 저장된 메시지 목록 표시
- 샘플 데이터 생성: 테스트용 샘플 메시지 생성
- 페이지네이션: 대량의 데이터 효율적 처리

### 3. 검색 기능
- 메시지 검색: 특정 키워드로 메시지 검색
- 전체 메시지 조회: 모든 저장된 메시지 표시
- Redis 캐시를 활용한 검색 성능 최적화

### 4. 로깅 시스템
- Redis 로깅: API 호출 로그 저장 및 조회
- Kafka 로깅: API 통계 데이터 수집 (비동기)

## 🗄️ 데이터베이스 구조

### MariaDB (jiwoo_db)
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT NOT NULL,
    user_id VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);
```

### Redis 데이터 구조
- 세션 저장: `session:{username}`
- API 로그: `api_logs` (List 타입)
- 검색 캐시: `search:{query}`

## 🔧 API 엔드포인트

### 사용자 관리
- POST /register: 회원가입
- POST /login: 로그인
- POST /logout: 로그아웃

### 메시지 관리
- POST /db/message: 메시지 저장
- GET /db/messages: 전체 메시지 조회
- GET /db/messages/search: 메시지 검색

### 로그 관리
- GET /logs/redis: Redis 로그 조회
- GET /logs/kafka: Kafka 로그 조회

## ⚙️ 환경 변수 설정
```yaml
- MYSQL_HOST: jiwoo-mariadb
- MYSQL_USER: jiwoo
- MYSQL_PASSWORD: jiwoo1234!
- MYSQL_DATABASE: jiwoo_db
- REDIS_HOST: jiwoo-redis-master
- REDIS_PASSWORD: New1234!
- KAFKA_SERVERS: jiwoo-kafka:9092
- FLASK_SECRET_KEY: Flask 세션 암호화 키
```

## 🛠️ 배포 방법

### 1. 로컬 빌드 및 배포
```bash
# 전체 배포 스크립트 실행
./build-and-deploy.sh
```

### 2. 수동 배포
```bash
# 1. Docker 이미지 빌드
docker build -t npr04191/0827_hw_local:backend ./backend
docker build -t npr04191/0827_hw_local:frontend ./frontend

# 2. 이미지 푸시
docker push npr04191/0827_hw_local:backend
docker push npr04191/0827_hw_local:frontend

# 3. Helm으로 인프라 설치
helm install jiwoo-redis bitnami/redis -f k8s/redis-values.yaml
helm install jiwoo-kafka bitnami/kafka -f k8s/kafka-values.yaml
helm install jiwoo-mariadb bitnami/mariadb -f k8s/mariadb-values.yaml

# 4. 애플리케이션 배포
kubectl apply -f k8s/jiwoo-backend-secret.yaml
kubectl apply -f k8s/jiwoo-backend-deployment.yaml
kubectl apply -f k8s/jiwoo-frontend-deployment.yaml
```

### 3. 정리
```bash
# 전체 리소스 정리
./cleanup.sh
```

## 🌐 접속 정보

- **프론트엔드**: http://localhost:30080
- **백엔드 API**: http://localhost:5000

## 🔒 보안 기능
- 비밀번호 해시화 저장
- 세션 기반 인증
- Redis를 통한 세션 관리
- API 접근 제어

## ⚡ 성능 최적화
- Redis 캐시를 통한 검색 성능 향상
- 비동기 로깅으로 API 응답 시간 개선
- 페이지네이션을 통한 대용량 데이터 처리

## 📊 모니터링
- API 호출 로그 저장 및 조회
- 사용자 행동 추적
- 시스템 성능 모니터링

## 🗂️ 프로젝트 구조
```
0827_hw_local/
├── backend/                 # Flask 백엔드
│   ├── app.py              # [변경] DB 연결, Kafka 설정 수정
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # Vue.js 프론트엔드
│   ├── nginx.conf          # [변경] 백엔드 서비스 이름 수정
│   ├── Dockerfile
│   └── src/
├── k8s/                    # Kubernetes 배포 파일
│   ├── jiwoo-*.yaml        # [신규] jiwoo 접두사 배포 파일
│   ├── *-values.yaml       # [신규] Helm values 파일
│   ├── *-init-job.yaml     # [신규] 자동화 초기화 Job
│   └── *.yaml              # [기존] 원본 배포 파일
├── db/
│   └── init.sql            # [변경] DB 구조 완전 재작성
├── build-and-deploy.sh     # [신규] 배포 스크립트
├── cleanup.sh              # [신규] 정리 스크립트
└── README.md               # [변경] 프로젝트 문서 업데이트
```

## ⚠️ 주의사항

### 1. 자동화된 초기화
다음 항목들은 Kubernetes Job으로 자동화되었습니다:
- ✅ MariaDB 테이블 생성 (jiwoo-mariadb-init-job)
- ✅ Redis 테스트 데이터 (jiwoo-redis-init-job)

### 2. 수동 초기화 (필요시)
자동화가 실패한 경우에만 수동으로 실행:
```bash
# DB 초기화
kubectl exec -i jiwoo-mariadb-0 -- mysql -u jiwoo -pjiwoo1234! jiwoo_db < db/init.sql

# Redis 테스트 데이터
kubectl exec -it jiwoo-redis-master-0 -- redis-cli -a New1234! lpush api_logs '{"timestamp":"2025-08-28T00:30:00","action":"test","details":"Redis 연결 테스트"}'
``` 