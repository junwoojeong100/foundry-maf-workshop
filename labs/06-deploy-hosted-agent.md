# Lab 06. Foundry에 배포 — hosted agent

> ⏱️ 예상 시간: 30분

Lab 03~05에서 만든 에이전트·워크플로우는 모두 `local`/`serve`로 내 컴퓨터에서 실행했습니다. 이 랩에서는 같은 소스코드를 Microsoft Foundry의 **hosted agent**로 배포하고 원격 호출합니다.

이것으로 워크샵이 한 바퀴 완성됩니다: **모델 배포 → MAF로 에이전트·워크플로우 빌드 → Foundry에 hosted agent로 배포.**

---

## 🎯 목표

- 로컬 `serve` 코드와 hosted agent 코드가 같다는 점을 이해한다.
- 현재 권장 형식인 통합 `azure.yaml`과 **code deployment**를 사용한다.
- 배포된 hosted agent를 CLI와 `FoundryAgent`로 호출한다.
- 기존 Foundry 프로젝트를 보존하면서 hosted agent만 안전하게 삭제한다.

---

## 배포의 큰 그림

세 예제 모두 배포할 수 있습니다.

| 예제 | 만든 랩 | hosted agent 이름 |
|------|:------:|-------------------|
| `maf_basic/` | Lab 03 | `maf-basic-agent` |
| `maf_tools/` | Lab 04 | `maf-tools-agent` |
| `maf_workflow/` | Lab 05 | `maf-workflow-agent` |

저장소에는 에이전트 소스와 의존성만 둡니다. 배포 작업 디렉토리에서 `azd ai agent init`을 실행하면 현재 형식의 파일이 생성됩니다.

| 파일 | 생성 시점 | 역할 |
|------|-----------|------|
| `main.py` | 저장소에 포함 | 에이전트 정의 + Responses 서버 진입점 |
| `requirements.txt` | 저장소에 포함 | 로컬/원격 빌드 의존성 |
| `azure.yaml` | `azd ai agent init` | azd 프로젝트와 hosted agent의 통합 설정 |
| `.agentignore` | `azd ai agent init` | 배포 ZIP에서 `.env`, 가상환경 등을 제외 |

> `agent.manifest.yaml`과 standalone `agent.yaml`은 폐기 예정입니다. 이 가이드는 Python 소스를 ZIP으로 업로드하고 Foundry가 원격 빌드하는 **code deployment**를 사용하므로 Docker/ACR이 필요하지 않습니다.

---

## 사전 준비: Azure Developer CLI와 Foundry 확장

`azd`는 Azure CLI(`az`)와 별개 도구입니다. 현재 Foundry 확장이 요구하는 **azd 1.27.0 이상**을 사용하세요.

```bash
# azd 설치 확인 (없으면 https://aka.ms/azd-install)
azd version

# Foundry 확장 묶음 설치/업데이트
azd ext install microsoft.foundry
azd ext upgrade microsoft.foundry
azd ai agent version

# az login과 별개의 인증 컨텍스트
azd auth login
```

> `microsoft.foundry`는 `azure.ai.agents`를 포함한 Foundry 확장 묶음입니다. 특정 확장만 설치하는 환경이나 이전 azd에서는 `azd ext install azure.ai.agents`도 유효합니다. [공식 quickstart](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent)와 `azd ext list`를 함께 확인하세요.

기존 프로젝트에 hosted agent를 배포하려면 사용자에게 최소한 다음 Foundry 데이터 플레인 권한이 필요합니다.

- Foundry 리소스: **Foundry User**
- 대상 프로젝트: **Foundry Project Manager**

Lab 01의 CLI 절차를 완료했다면 두 역할이 이미 부여되어 있습니다.

---

## Step A. 배포 전 로컬 확인

먼저 `maf_basic`이 로컬에서 정상 동작하는지 확인합니다.

```bash
cd code/maf_basic
source ../.venv/bin/activate
cp .env.example .env      # 실제 엔드포인트와 모델 배포 이름으로 수정
python main.py serve

# 다른 터미널에서
curl -sS -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "안녕!", "stream": false}'
```

응답이 오면 서버를 종료합니다. 이 `main.py`를 변경 없이 배포합니다.

---

## Step B. 기존 Foundry 프로젝트 ID 확인

`.env`의 프로젝트 엔드포인트가 아니라 Azure **리소스 ID**가 필요합니다.

```bash
# Lab 01에서 사용한 값을 넣으세요.
PROJECT_ID=$(az cognitiveservices account project show \
  --name <리소스이름> \
  --resource-group <리소스그룹> \
  --project-name <프로젝트이름> \
  --query id -o tsv)

printf '%s\n' "$PROJECT_ID"
```

형식:

```text
/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<account>/projects/<project>
```

포털에서는 프로젝트의 **Operate → Admin → Resource ID**에서도 복사할 수 있습니다.

---

## Step C. code deployment로 초기화하고 배포

`azd ai agent init`은 같은 폴더에서 반복 실행할 때 서비스 이름에 `-2`가 붙을 수 있습니다. 각 에이전트마다 새 작업 디렉토리를 사용하세요.

### C-1. 기본 에이전트 소스 복사

```bash
# 저장소의 절대경로로 바꾸세요.
WORKSHOP_ROOT="/절대경로/foundry-maf-workshop"
test -f "$WORKSHOP_ROOT/code/maf_basic/main.py" || { echo "WORKSHOP_ROOT 경로를 확인하세요."; exit 1; }

DEPLOY_DIR=~/maf-deploy/maf-basic-agent
mkdir -p "$DEPLOY_DIR"
test -z "$(ls -A "$DEPLOY_DIR")" || { echo "작업 디렉토리가 비어 있지 않습니다. 새 디렉토리를 사용하세요."; exit 1; }
cp "$WORKSHOP_ROOT/code/maf_basic/main.py" \
   "$WORKSHOP_ROOT/code/maf_basic/requirements.txt" \
   "$DEPLOY_DIR/"
cd "$DEPLOY_DIR"
```

`.env`는 복사하지 않습니다. 로컬 비밀값이 배포 패키지에 들어가지 않게 하기 위함입니다.

### C-2. 통합 `azure.yaml` 생성

```bash
test -n "$PROJECT_ID" || { echo "Step B에서 PROJECT_ID를 다시 설정하세요."; exit 1; }

azd ai agent init --no-prompt \
  --src . \
  --agent-name maf-basic-agent \
  --project-id "$PROJECT_ID" \
  --model-deployment gpt-5.4 \
  --deploy-mode code \
  --runtime python_3_13 \
  --entry-point main.py
```

생성 결과를 확인합니다.

```bash
# azure.yaml에 hosted agent와 codeConfiguration이 있어야 합니다.
grep -E "host: azure.ai.agent|codeConfiguration|python_3_13|entryPoint" azure.yaml

# .env, 가상환경, 캐시가 배포에서 제외되는지 확인합니다.
grep -E "^\\.env|\\.venv|__pycache__" .agentignore

# 기존 프로젝트와 모델 배포가 올바르게 연결되었는지 확인합니다.
azd env get-values
```

> `FOUNDRY_PROJECT_ENDPOINT`는 Foundry가 hosted agent에 자동 주입합니다. `AZURE_AI_MODEL_DEPLOYMENT_NAME`은 azd 환경에서 `azure.yaml`로 전달됩니다. `FOUNDRY_PROJECT_ENDPOINT`를 `azure.yaml`에 직접 선언하지 마세요.

### C-3. 프로비저닝 + 배포

```bash
azd up
```

`azd up`은 패키징·프로비저닝·배포를 한 흐름으로 실행합니다. 이 가이드의 **기존 프로젝트 + code deployment** 경로에서는 소스를 ZIP으로 업로드하고 Foundry가 원격 빌드합니다. Docker나 Azure Container Registry를 만들지 않습니다.

배포 후 확인:

```bash
azd ai agent show
azd ai agent invoke "프랑스의 수도는 어디인가요?"
```

`Status`가 `active`이고 응답이 오면 성공입니다. 포털의 프로젝트 **Build → Agents**에서도 `maf-basic-agent`와 버전을 확인할 수 있습니다.

### C-4. 나머지 두 예제 배포

각각 새 디렉토리에서 같은 절차를 반복합니다.

| 원본 파일 | 작업 디렉토리 예 | `--agent-name` |
|-----------|------------------|----------------|
| `code/maf_tools/main.py`, `requirements.txt` | `~/maf-deploy/maf-tools-agent` | `maf-tools-agent` |
| `code/maf_workflow/main.py`, `requirements.txt` | `~/maf-deploy/maf-workflow-agent` | `maf-workflow-agent` |

`--project-id`, `--model-deployment`, `--deploy-mode`, `--runtime`, `--entry-point` 값은 동일합니다. 워크플로우 예제는 `gpt-5.4`로 검증했습니다.

> 새 터미널에서 반복한다면 `WORKSHOP_ROOT`를 다시 설정하고 Step B를 다시 실행해 `PROJECT_ID`를 채우세요. 각 작업 디렉토리는 반드시 비어 있어야 합니다.

---

## Step D. Python `call` 모드로 원격 호출

각 원본 예제 폴더의 `.env`에서 프로젝트 엔드포인트와 에이전트 이름을 배포 결과에 맞춥니다.

```bash
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5.4
FOUNDRY_AGENT_NAME=maf-basic-agent
```

`main.py`의 원격 호출 부분:

```python
from agent_framework.foundry import FoundryAgent

agent = FoundryAgent(
    project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    agent_name=os.environ.get("FOUNDRY_AGENT_NAME", "maf-basic-agent"),
    credential=DefaultAzureCredential(),
    allow_preview=True,
)
result = await agent.run("프랑스의 수도는 어디인가요?")
```

실행:

```bash
# 새 터미널이라면 저장소 절대경로를 다시 설정하세요.
WORKSHOP_ROOT="/절대경로/foundry-maf-workshop"
source "$WORKSHOP_ROOT/code/.venv/bin/activate"
cd "$WORKSHOP_ROOT/code/maf_basic"
python main.py call
```

각 예제의 기본 이름과 질문:

| 예제 폴더 | `FOUNDRY_AGENT_NAME` | 질문 |
|-----------|----------------------|------|
| `maf_basic` | `maf-basic-agent` | 프랑스의 수도는 어디인가요? |
| `maf_tools` | `maf-tools-agent` | 암스테르담 날씨 어때요? |
| `maf_workflow` | `maf-workflow-agent` | 친환경 텀블러 브랜드의 슬로건을 만들어줘 |

---

## Step E. 유용한 `azd ai agent` 명령

배포 작업 디렉토리에서 실행합니다.

| 명령 | 용도 |
|------|------|
| `azd ai agent show` | 상태·버전·엔드포인트 확인 |
| `azd ai agent invoke "<질문>"` | 원격 호출 |
| `azd ai agent monitor --follow` | 최근 호출 세션의 로그 스트리밍 |
| `azd ai agent run` | 배포 전 로컬 서버 실행 |
| `azd ai agent doctor` | 로컬·원격 설정 진단 |

> 현재 `azure.ai.agents` 1.0.0-beta.5에서 code deployment 프로젝트에 `azd ai agent doctor`를 실행하면, 더 이상 사용하지 않는 `agent.yaml`이 없다는 항목을 실패로 표시할 수 있습니다. `azure.yaml`에 `host: azure.ai.agent`와 `codeConfiguration`이 정상 생성됐다면 이 항목 때문에 legacy 파일을 새로 만들지 말고, 나머지 진단 결과만 확인하세요.

---

## Step F. 안전하게 정리

이 워크샵은 기존 Foundry 프로젝트와 모델을 재사용합니다. 따라서 `azd down` 대신 hosted agent만 삭제합니다.

```bash
cd ~/maf-deploy/maf-basic-agent
azd ai agent delete

# 활성 세션 때문에 거부될 때만:
azd ai agent delete --force
```

세 예제를 배포했다면 각 작업 디렉토리에서 한 번씩 실행합니다. 삭제 후 로컬 작업 디렉토리는 파일 탐색기나 안전한 경로 확인 후 직접 지울 수 있습니다.

> ⚠️ 이 흐름에서 `azd down`을 실행하지 마세요. `azd down`은 해당 azd 환경이 관리하는 Azure 리소스를 모두 삭제하며, 구성에 따라 리소스 그룹의 Foundry 프로젝트·모델까지 삭제할 수 있습니다.

Lab 01에서 이 워크샵 전용 리소스 그룹을 새로 만들었고 그 안에 공유 리소스가 없음을 확인했다면, 모든 Foundry 리소스까지 정리할 수 있습니다.

```bash
az group delete --name my-foundry-rg --yes
```

> ⚠️ 리소스 그룹 삭제는 되돌릴 수 없습니다. 이름과 포함 리소스를 Azure portal에서 확인한 뒤 실행하세요.

---

## 🧩 핵심 개념

| 개념 | 설명 |
|------|------|
| `ResponsesHostServer(agent).run()` | 로컬과 hosted 환경에서 같은 Responses 서버 실행 |
| 통합 `azure.yaml` | azd 프로젝트·모델 연결·hosted agent 설정의 현재 단일 소스 |
| `codeConfiguration` | Python 소스를 ZIP으로 올려 Foundry에서 원격 빌드 |
| `azd ai agent init` | 기존 코드를 azd hosted-agent 프로젝트로 초기화 |
| `azd up` | 프로비저닝 + 배포 |
| 워크플로우 `.as_agent()` | 여러 단계를 단일 hosted agent로 노출 |
| `FoundryAgent` | 배포된 agent를 이름으로 원격 호출 |
| `azd ai agent delete` | 기존 프로젝트는 보존하고 hosted agent만 삭제 |

---

## ⚠️ 트러블슈팅

| 증상 | 해결 |
|------|------|
| `azd: command not found` | [Azure Developer CLI 설치](https://aka.ms/azd-install) |
| `azd ai agent` 명령이 없음 | `azd ext install microsoft.foundry` 후 `azd ai agent version` 확인 |
| `microsoft.foundry` 확장을 찾을 수 없음 | `azd ext install azure.ai.agents`로 hosted-agent 확장만 설치 |
| `--runtime`/`--entry-point` 플래그가 없음 | `azd ext upgrade microsoft.foundry`와 `azd ext upgrade azure.ai.agents` 실행 |
| `init`에서 403/권한 오류 | 사용자에게 Foundry 리소스의 **Foundry User**, 프로젝트의 **Foundry Project Manager** 역할이 있는지 확인 |
| `azure.yaml`에 `<agent-name>-2`가 생김 | 같은 폴더에서 `init`을 반복 실행한 결과. 새 작업 디렉토리에서 처음부터 다시 초기화 |
| `azure.yaml`에 `codeConfiguration`이 없음 | `--deploy-mode code --runtime python_3_13 --entry-point main.py`로 새 작업 디렉토리에서 다시 초기화 |
| `.env`가 배포될 것 같음 | `.env`를 작업 폴더에 복사하지 말고 `.agentignore`에서 제외 여부 확인 |
| `ModuleNotFoundError` | 해당 작업 폴더의 `requirements.txt`가 복사됐는지 확인 |
| 원격 빌드에서 `hyperlight-sandbox-backend-wasm`/`ResolutionImpossible` | `agent-framework` 메타 패키지 대신 이 저장소처럼 `agent-framework-core==1.11.0`과 필요한 Foundry 패키지만 사용 |
| `call`에서 agent not found | `.env`의 프로젝트 엔드포인트와 `FOUNDRY_AGENT_NAME`이 배포 대상과 같은지 확인 |
| `azd ai agent monitor`가 세션을 못 찾음 | 먼저 `azd ai agent invoke`를 한 번 실행하거나 `--session-id` 지정 |
| 워크플로우 품질이 낮음 | 모델 배포가 `gpt-5.4`인지 확인 |
| agent 삭제가 active session 때문에 실패 | `azd ai agent delete --force` |

---

## ✅ 체크포인트

- [ ] `maf_basic` 로컬 `serve` 확인
- [ ] Microsoft Foundry 확장 설치 및 `azd ai agent version` 확인
- [ ] 새 작업 디렉토리에서 통합 `azure.yaml` 생성
- [ ] `.agentignore`에서 `.env` 제외 확인
- [ ] `azd up` 후 `azd ai agent show` → `active`
- [ ] CLI와 `python main.py call` 원격 호출 성공
- [ ] `maf_tools`, `maf_workflow`도 각각 배포
- [ ] 실습 후 `azd ai agent delete`로 hosted agent 삭제

완료했다면 👉 **[부록. GitHub Copilot CLI](appendix-copilot-cli.md)** *(Optional)* 로 이어가세요.
