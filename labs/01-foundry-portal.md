# Lab 01. Foundry 포털 — 프로젝트 생성 & 모델 배포

> ⏱️ 예상 시간: 20분

이 랩에서는 [Microsoft Foundry 포털](https://ai.azure.com)에서 프로젝트를 만들고 모델을 배포합니다. 이후 모든 랩이 여기서 만든 리소스를 사용합니다.

---

## 🎯 목표

- Foundry 프로젝트를 생성한다.
- 모델을 배포한다.
- 프로젝트 엔드포인트를 복사해 `.env`에 저장한다.

> 두 가지 방법을 모두 안내합니다. **포털(GUI)** 방식이 처음 접하는 분께 직관적입니다. CLI에 익숙하다면 **Azure CLI** 방식이 더 빠릅니다.

---

## 방법 A) 포털(GUI)로 진행 — 권장

### 1. 프로젝트 생성

1. [https://ai.azure.com](https://ai.azure.com/?cid=learnDocs) 에 로그인합니다.
2. 우측 상단 **New Foundry** 토글이 켜져 있는지 확인합니다. (Foundry 신규 버전)
3. 프로젝트를 만듭니다.
   - 처음이라면 안내에 따라 **Create a new project**를 선택합니다.
   - 이미 프로젝트가 있다면 좌측 상단 프로젝트 이름 → **Create new project**.
4. 프로젝트 이름을 입력합니다. 예: `my-foundry-project`
5. **Advanced options**를 눌러 리소스 그룹과 지역을 설정합니다.
   - **Resource group**: 새로 만들거나 기존 것 선택 (새로 만들면 리소스 정리가 쉬움)
   - **Location**: 팀에서 가까운 지역 선택
6. **Create project**를 누르고, 프로젝트 개요 화면이 나올 때까지 기다립니다.

> 💡 **Tip**: 모델 배포 없이 빠르게 체험하고 싶다면, 지역을 **West US 3**로 만들고 [instant model(preview)](https://learn.microsoft.com/azure/ai-foundry/concepts/instant-models)을 쓸 수 있습니다. 이 경우 아래 코드의 모델 이름을 `gpt-5.1-mini`로 바꾸면 배포 단계를 건너뛸 수 있습니다.

### 2. 모델 배포

1. 우측 상단 **Discover** → 좌측 **Models** 선택.
2. 원하는 모델을 검색합니다. 예: `gpt-5.4` (또는 `gpt-4o`, `gpt-5.1-mini`)
3. **Deploy** → **Default settings**를 눌러 프로젝트에 추가합니다.
4. **배포 이름(deployment name)**을 메모해 둡니다. (예: `gpt-5.4`) — 코드에서 이 이름을 씁니다.

### 3. 프로젝트 엔드포인트 복사

1. 프로젝트를 선택합니다.
2. 프로젝트 **welcome 화면**에서 **project endpoint**를 찾습니다.
3. 엔드포인트 값을 복사합니다.
   - 형식: `https://<리소스이름>.services.ai.azure.com/api/projects/<프로젝트이름>`

---

## 방법 B) Azure CLI로 진행

> `az version` 2.67.0 이상, 리소스 그룹에 대한 Contributor/Owner 권한 필요.

```bash
# 1. 리소스 그룹 생성
az group create --name my-foundry-rg --location eastus

# 2. Foundry 리소스 생성 (프로젝트 관리 활성화)
#    --custom-domain 값은 전역에서 고유해야 합니다. 중복이면 다른 이름 사용.
az cognitiveservices account create \
    --name my-foundry-resource \
    --resource-group my-foundry-rg \
    --kind AIServices \
    --sku S0 \
    --location eastus \
    --custom-domain my-foundry-resource \
    --allow-project-management

# 3. 프로젝트 생성
az cognitiveservices account project create \
    --name my-foundry-resource \
    --resource-group my-foundry-rg \
    --project-name my-foundry-project \
    --location eastus

# 4. 모델 배포
az cognitiveservices account deployment create \
    --name my-foundry-resource \
    --resource-group my-foundry-rg \
    --deployment-name gpt-5.4 \
    --model-name gpt-5.4 \
    --model-version "2026-03-05" \
    --model-format OpenAI \
    --sku-capacity 10 \
    --sku-name GlobalStandard

# 5. 내 계정에 데이터플레인 역할 부여 (코드로 모델·에이전트를 호출하려면 필수)
#    이 역할이 없으면 Lab 02에서 403(PermissionDenied)이 납니다.
ACCT_ID=$(az cognitiveservices account show \
    --name my-foundry-resource -g my-foundry-rg --query id -o tsv)
OID=$(az ad signed-in-user show --query id -o tsv)
az role assignment create --assignee "$OID" --scope "$ACCT_ID" \
    --role "Cognitive Services OpenAI User"
az role assignment create --assignee "$OID" --scope "$ACCT_ID" \
    --role "Cognitive Services User"
```

> 💡 역할 부여 후 전파에 1~2분 걸릴 수 있습니다. 구독/리소스에 대한 Owner 권한만으로는 데이터플레인(모델 추론) 호출이 되지 않으므로 위 두 역할이 필요합니다.

> 프로젝트 엔드포인트는 포털의 welcome 화면에서 확인하는 것이 가장 정확합니다.

---

## `.env` 채우기

복사한 값으로 저장소 루트의 `.env` 파일을 채웁니다. (방법 A·B 어느 쪽으로 진행했든 공통 단계입니다.)

```bash
FOUNDRY_PROJECT_ENDPOINT=https://my-foundry-resource.services.ai.azure.com/api/projects/my-foundry-project
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5.4
FOUNDRY_AGENT_NAME=maf-basic-agent
```

---

## ⚠️ 트러블슈팅

| 증상 | 원인 & 해결 |
|------|------------|
| 프로젝트 생성 권한 오류 | 구독/리소스 그룹에 **Owner** 또는 **Foundry Owner** 역할이 필요합니다. |
| 모델을 배포할 수 없음 | 선택한 **지역(region)**에서 해당 모델을 지원하지 않을 수 있습니다. 다른 지역을 시도하세요. |
| `--custom-domain` 이름 충돌 | custom-domain 값은 전역 고유해야 합니다. 다른 이름을 쓰세요. |
| 할당량(quota) 부족 | `--sku-capacity`를 낮추거나 구독의 모델 할당량을 확인하세요. |

---

## ✅ 체크포인트

- [ ] Foundry 프로젝트 생성 완료
- [ ] 모델 배포 완료 (배포 이름 메모)
- [ ] 프로젝트 엔드포인트 복사 완료
- [ ] `.env`에 `FOUNDRY_PROJECT_ENDPOINT`, `AZURE_AI_MODEL_DEPLOYMENT_NAME` 채움

완료했다면 👉 **[Lab 02. Foundry SDK](02-foundry-sdk.md)** 로 이동하세요.
