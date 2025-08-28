# GitHub Actions 설정 가이드

## 🚀 GitHub Actions 워크플로우

### 워크플로우 파일: `.github/workflows/build-and-push.yml`

#### 주요 기능
- **자동 빌드**: main/master/develop 브랜치 푸시 시 자동 실행
- **Docker 이미지 빌드**: Backend와 Frontend 각각 빌드
- **ACR 푸시**: Azure Container Registry에 이미지 업로드
- **KST 기반 태깅**: 한국 시간 기준 날짜시간 태그 생성

#### 워크플로우 구조
```yaml
name: Build and Push Docker Images

on:
  push:
    branches: [ main, master, develop ]

jobs:
  build-backend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./backend
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Log in to Azure Container Registry (ACR)
        uses: azure/docker-login@v1
        with:
          login-server: ${{ secrets.ACR_LOGIN_SERVER }}
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}
      
      - name: Get current date and time (KST)
        id: datetime
        run: echo "datetime=$(TZ='Asia/Seoul' date +'%Y%m%d_%H%M%S')" >> $GITHUB_OUTPUT
      
      - name: Build and push Docker image to ACR
        run: |
          docker build -t ${{ secrets.ACR_LOGIN_SERVER }}/kltecho_jiwoo_${{ steps.datetime.outputs.datetime }}-backend \
            -t ${{ secrets.ACR_LOGIN_SERVER }}/kltecho_jiwoo-backend:latest .
          docker push ${{ secrets.ACR_LOGIN_SERVER }}/kltecho_jiwoo_${{ steps.datetime.outputs.datetime }}-backend
          docker push ${{ secrets.ACR_LOGIN_SERVER }}/kltecho_jiwoo-backend:latest

  build-frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./frontend
    steps:
      # Frontend 빌드 단계 (Backend와 유사)
```

## 🔐 GitHub Secrets 설정

### 필요한 Secrets
| Secret 이름 | 설명 | 예시 값 |
|-------------|------|---------|
| `ACR_LOGIN_SERVER` | Azure Container Registry 로그인 서버 | `ktech4.azurecr.io` |
| `ACR_USERNAME` | ACR 사용자명 | `ktech4` |
| `ACR_PASSWORD` | ACR 비밀번호 | `[ACR에서 생성한 비밀번호]` |

### Secrets 설정 방법
1. **GitHub 저장소** → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** 클릭
3. 위의 3개 Secrets 추가

## 🐳 Docker 이미지 태깅 전략

### 태그 형식
- **날짜시간 태그**: `kltecho_jiwoo_20250127_143052-backend`
- **Latest 태그**: `kltecho_jiwoo-backend:latest`

### 태그 생성 로직
```bash
# 한국 시간 기준 날짜시간 생성
TZ='Asia/Seoul' date +'%Y%m%d_%H%M%S'
# 결과: 20250127_143052
```

### 이미지 이름 규칙
- **Backend**: `ktech4.azurecr.io/kltecho_jiwoo_날짜시간-backend`
- **Frontend**: `ktech4.azurecr.io/kltecho_jiwoo_날짜시간-frontend`

## 📦 Azure Container Registry (ACR) 설정

### ACR 생성 (Azure CLI)
```bash
# 리소스 그룹 생성
az group create --name myResourceGroup --location eastus

# ACR 생성
az acr create --resource-group myResourceGroup \
  --name ktech4 --sku Basic

# ACR 로그인 서버 확인
az acr show --name ktech4 --query loginServer --output tsv

# ACR 자격 증명 생성
az acr credential show --name ktech4
```

### ACR 인증 정보
```bash
# 사용자명과 비밀번호 확인
az acr credential show --name ktech4 --query "username" --output tsv
az acr credential show --name ktech4 --query "passwords[0].value" --output tsv
```

## 🔄 배포 프로세스

### 1. 코드 푸시
```bash
git add .
git commit -m "Update application code"
git push origin main
```

### 2. 자동 빌드 및 푸시
- GitHub Actions가 자동으로 실행
- Docker 이미지 빌드 및 ACR 푸시
- 날짜시간 태그와 latest 태그 생성

### 3. 수동 배포
```bash
# 배포 스크립트 실행
./deploy-to-jiwoo-namespace.sh
```

## 📊 워크플로우 모니터링

### GitHub Actions 대시보드
- **저장소** → **Actions** 탭에서 워크플로우 실행 상태 확인
- 실시간 로그 확인 가능
- 실패 시 상세 오류 메시지 확인

### 로그 확인 방법
```bash
# 워크플로우 실행 로그
# GitHub 웹 인터페이스에서 확인

# ACR 이미지 확인
az acr repository list --name ktech4 --output table
az acr repository show-tags --name ktech4 --repository kltecho_jiwoo-backend --output table
```

## 🛠️ 문제 해결

### 일반적인 문제들

#### 1. ACR 인증 실패
```
Error: unauthorized: authentication required
```
**해결**: GitHub Secrets의 ACR 인증 정보 확인

#### 2. 이미지 빌드 실패
```
Error: failed to build image
```
**해결**: Dockerfile 문법 오류 확인, 빌드 컨텍스트 확인

#### 3. 푸시 실패
```
Error: failed to push image
```
**해결**: ACR 저장소 권한 확인, 네트워크 연결 확인

### 디버깅 명령어
```bash
# ACR 연결 테스트
az acr login --name ktech4

# 이미지 목록 확인
az acr repository list --name ktech4

# 태그 확인
az acr repository show-tags --name ktech4 --repository kltecho_jiwoo-backend
```

## 🔄 향후 개선 계획

### 1. 자동 배포 추가
- GitHub Actions에서 AKS 자동 배포
- 배포 승인 워크플로우
- 롤백 자동화

### 2. 보안 강화
- 이미지 스캔 추가
- 취약점 검사
- 시크릿 로테이션

### 3. 모니터링 통합
- 배포 상태 알림
- 성능 메트릭 수집
- 로그 집계

## 📋 체크리스트

### 초기 설정
- [ ] Azure Container Registry 생성
- [ ] GitHub Secrets 설정
- [ ] 워크플로우 파일 생성
- [ ] 첫 번째 빌드 테스트

### 정기 점검
- [ ] ACR 저장소 정리 (오래된 이미지 삭제)
- [ ] GitHub Secrets 유효성 확인
- [ ] 워크플로우 성능 모니터링
- [ ] 보안 업데이트 적용
