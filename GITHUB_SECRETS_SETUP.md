# GitHub Secrets 설정 가이드

## 🔐 필요한 GitHub Secrets

Azure CI/CD 파이프라인을 위해 다음 Secrets를 GitHub 저장소에 설정해야 합니다.

### 1. Azure Container Registry (ACR) 인증 정보

#### ACR_USERNAME
- **설명**: Azure Container Registry 사용자명
- **값**: ACR 관리자 사용자명 (보통 ACR 이름)
- **예시**: `ktech4`

#### ACR_PASSWORD
- **설명**: Azure Container Registry 비밀번호
- **값**: ACR 관리자 비밀번호
- **확인 방법**:
```bash
az acr credential show --name ktech4 --query "passwords[0].value" -o tsv
```

### 2. Azure 인증 정보

#### AZURE_CREDENTIALS
- **설명**: Azure 서비스 주체 인증 정보 (JSON 형식)
- **생성 방법**:
```bash
# Azure CLI로 서비스 주체 생성
az ad sp create-for-rbac --name "jiwoo-aks-sp" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group} \
  --sdk-auth
```

### 3. Azure 리소스 정보

#### AZURE_RESOURCE_GROUP
- **설명**: Azure 리소스 그룹 이름
- **값**: AKS 클러스터가 있는 리소스 그룹
- **예시**: `jiwoo-rg`

#### AKS_CLUSTER_NAME
- **설명**: Azure Kubernetes Service 클러스터 이름
- **값**: AKS 클러스터 이름
- **예시**: `jiwoo-aks`

## 🛠️ 설정 방법

### 1. GitHub 저장소에서 Secrets 설정

1. GitHub 저장소로 이동
2. **Settings** 탭 클릭
3. 왼쪽 메뉴에서 **Secrets and variables** → **Actions** 클릭
4. **New repository secret** 버튼 클릭
5. 각 Secret 추가:
   - **Name**: `ACR_USERNAME`
   - **Value**: ACR 사용자명
6. 반복하여 모든 Secret 추가

### 2. Azure 리소스 생성 (필요한 경우)

#### Azure Container Registry 생성
```bash
# 리소스 그룹 생성
az group create --name jiwoo-rg --location eastus

# ACR 생성
az acr create --resource-group jiwoo-rg \
  --name ktech4 \
  --sku Basic \
  --admin-enabled true
```

#### Azure Kubernetes Service 생성
```bash
# AKS 클러스터 생성
az aks create --resource-group jiwoo-rg \
  --name jiwoo-aks \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# ACR과 AKS 연결
az aks update -n jiwoo-aks -g jiwoo-rg --attach-acr ktech4
```

### 3. 서비스 주체 생성 및 권한 부여

```bash
# 서비스 주체 생성
az ad sp create-for-rbac --name "jiwoo-aks-sp" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/jiwoo-rg \
  --sdk-auth

# 출력된 JSON을 AZURE_CREDENTIALS Secret으로 설정
```

## 🔍 Secrets 확인 방법

### ACR 인증 정보 확인
```bash
# ACR 로그인 서버 확인
az acr show --name ktech4 --query loginServer -o tsv

# ACR 사용자명 확인
az acr credential show --name ktech4 --query username -o tsv

# ACR 비밀번호 확인
az acr credential show --name ktech4 --query "passwords[0].value" -o tsv
```

### AKS 클러스터 정보 확인
```bash
# AKS 클러스터 목록
az aks list --resource-group jiwoo-rg -o table

# AKS 자격 증명 가져오기
az aks get-credentials --resource-group jiwoo-rg --name jiwoo-aks
```

## 🚨 주의사항

1. **보안**: Secrets는 절대 코드에 직접 포함하지 마세요
2. **권한**: 서비스 주체는 필요한 최소 권한만 부여하세요
3. **정기 갱신**: ACR 비밀번호는 정기적으로 갱신하세요
4. **백업**: 중요한 인증 정보는 안전한 곳에 백업하세요

## 📋 체크리스트

- [ ] ACR 생성 및 관리자 계정 활성화
- [ ] AKS 클러스터 생성
- [ ] ACR과 AKS 연결
- [ ] 서비스 주체 생성 및 권한 부여
- [ ] GitHub Secrets 설정:
  - [ ] ACR_USERNAME
  - [ ] ACR_PASSWORD
  - [ ] AZURE_CREDENTIALS
  - [ ] AZURE_RESOURCE_GROUP
  - [ ] AKS_CLUSTER_NAME
- [ ] 워크플로우 테스트 실행

## 🔗 참고 링크

- [Azure Container Registry 문서](https://docs.microsoft.com/azure/container-registry/)
- [Azure Kubernetes Service 문서](https://docs.microsoft.com/azure/aks/)
- [GitHub Actions Secrets 문서](https://docs.github.com/actions/security-guides/encrypted-secrets)
