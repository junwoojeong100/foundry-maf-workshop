# Lab 06. Foundry에 배포 — hosted agent

> ⏱️ 예상 시간: 30분

Lab 03~05에서 만든 에이전트·워크플로우는 모두 `local`/`serve`로 **내 컴퓨터에서** 돌았습니다.
이 랩에서는 그 코드를 **그대로 Microsoft Foundry에 hosted agent로 배포**해, 서버가 호스팅하고
이름으로 어디서든 호출할 수 있게 만듭니다.

이것으로 워크샵이 한 바퀴 완성됩니다: **모델 배포 → MAF로 에이전트·워크플로우 빌드 → Foundry에 hosted agent로 배포.**

---

## 🎯 목표

- "로컬 serve"와 "Foundry hosted agent"가 **같은 코드**임을 이해한다.
- MAF 에이전트/워크플로우를 `azd`로 Foundry에 배포한다.
- 배포된 hosted agent를 `call` 모드로 원격 호출한다.

---

## 배포의 큰 그림

hosted agent는 **컨테이너로 패키징된 MAF 앱**입니다. 각 예제 폴더(`maf_basic/` 등)에는 이미 배포에 필요한 파일이 들어 있습니다.

| 파일 | 역할 |
|------|------|
| `main.py` | 에이전트 정의 + `ResponsesHostServer(...).run()` (serve 진입점) |
| `agent.yaml` | 컨테이너 에이전트 설정(프로토콜·리소스·환경변수) |
| `agent.manifest.yaml` | 배포 매니페스트(이름·모델 리소스 등) |
| `Dockerfile` | 컨테이너 이미지 (`python main.py`, 포트 8088) |
| `requirements.txt` | 컨테이너용 최소 의존성 |

```
로컬 serve (python main.py serve)  ─────  똑같은 코드  ─────▶  Foundry hosted agent (azd deploy)
        http://localhost:8088                                    서버가 호스팅, 이름으로 호출
```

> 💡 로컬에서 `serve`로 검증한 바로 그 `main.py`가 컨테이너 안에서 실행됩니다. 새로 짜는 코드가 없습니다.

---

## 사전 준비: Azure Developer CLI

hosted agent 배포는 **Azure Developer CLI(`azd`)** 로 합니다.

```bash
# 설치 확인 (없으면 https://aka.ms/azd-install 참고)
azd version

# 로그인
azd auth login
```

> ⚠️ `azd ai agent`와 `agent-framework-foundry-hosting`은 **preview**입니다. 명령·패키지 이름이 바뀔 수 있으니, 문제가 생기면 [공식 hosted-agents 샘플](https://github.com/microsoft/agent-framework/tree/main/python/samples/04-hosting/foundry-hosted-agents)의 README에서 최신 절차를 확인하세요.

---

## Step A. 배포 전 — 로컬에서 다시 확인

배포할 예제 하나를 골라(여기서는 `maf_basic`) 로컬에서 정상 동작을 확인합니다.

```bash
cd code/maf_basic
cp .env.example .env      # FOUNDRY_PROJECT_ENDPOINT, AZURE_AI_MODEL_DEPLOYMENT_NAME 채우기
python main.py serve

# 다른 터미널에서
curl -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" -d '{"input": "안녕!"}'
```

응답이 오면 배포 준비 완료입니다.

---

## Step B. Foundry에 배포하기

> ⚠️ **디렉토리 주의**: `azd ai agent init`은 매니페스트가 있는 폴더 안에 새 `src/` 트리를 만들려고 하므로, **예제 폴더(`maf_basic/`) 안에서 직접 실행하면 경로가 중첩되어 실패**합니다. 아래처럼 **빈 작업 디렉토리**를 따로 만들고, 매니페스트는 **절대경로**로 가리킵니다.

```bash
# 0. 배포용 작업 디렉토리 (예제 폴더 밖)
mkdir -p ~/maf-deploy && cd ~/maf-deploy

# 1. 매니페스트로 배포 프로젝트 초기화
#    - 매니페스트는 예제 폴더의 절대경로로 지정
#    - Lab 01에서 만든 기존 Foundry 프로젝트를 재사용 (--project-id, --model-deployment)
azd ai agent init \
  -m /절대경로/code/maf_basic/agent.manifest.yaml \
  --project-id "<Lab 01에서 만든 프로젝트 리소스 ID>" \
  --model-deployment gpt-5.4

# 2. 프로비저닝 + 배포를 한 번에 (ACR·App Insights 자동 생성)
azd up
```

> 💡 프로젝트 리소스 ID는 다음으로 확인합니다.
> ```bash
> az cognitiveservices account project show \
>   --name <리소스이름> -g <리소스그룹> --project-name <프로젝트이름> --query id -o tsv
> ```
> `azd up` 대신 `azd provision`(리소스) → `azd deploy`(코드)로 나눠 실행해도 됩니다.

배포가 끝나면 Foundry 호스팅 인프라가 컨테이너에 다음 환경변수를 **자동 주입**합니다.

- `FOUNDRY_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- `APPLICATIONINSIGHTS_CONNECTION_STRING`

**확인**: [포털](https://ai.azure.com) → 프로젝트 → **Agents** 목록에 `maf-basic-agent`가 보이면 성공입니다. CLI로는 `azd ai agent show maf-basic-agent`의 `Status`가 **active**이면 됩니다.

> 워크플로우 예제(`maf_workflow/`)도 **똑같은 절차**로 배포합니다. 워크플로우가 `.as_agent()`로 단일 에이전트가 되어 있으므로, hosting 입장에서는 일반 에이전트와 동일합니다.

---

## Step C. 배포된 hosted agent 호출하기

이제 `call` 모드로 **배포된** 에이전트를 이름으로 원격 호출합니다. 내부적으로 `FoundryAgent`를 씁니다.

📄 `main.py`의 `call` 진입점:

```python
from agent_framework.foundry import FoundryAgent

agent = FoundryAgent(
    project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    agent_name=os.environ.get("FOUNDRY_AGENT_NAME", "maf-basic-agent"),
    credential=DefaultAzureCredential(),
    allow_preview=True,   # hosted agent(service-side session)용 preview surface
)
result = await agent.run("프랑스의 수도는 어디인가요?")
```

실행:

```bash
# .env 의 FOUNDRY_AGENT_NAME 이 배포한 이름과 같은지 확인
python main.py call
```

**확인**: 로컬이 아니라 **Foundry에 배포된** 에이전트가 답을 돌려주면 성공입니다.

> 🔎 `FoundryChatClient` vs `FoundryAgent`
> - `Agent(client=FoundryChatClient(...))` (serve/local) — 정의를 **내 코드가 소유**.
> - `FoundryAgent(agent_name=...)` (call) — 정의가 **Foundry에 배포**되어 있고, 이름으로 참조.

---

## 🧩 핵심 개념 정리

| 개념 | 설명 |
|------|------|
| `ResponsesHostServer(agent).run()` | 에이전트를 Responses 서버로 노출 (serve = 컨테이너 진입점) |
| `agent.yaml` / `agent.manifest.yaml` | 컨테이너 에이전트 설정과 배포 매니페스트 |
| `azd ai agent init` → `provision` → `deploy` | hosted agent 배포 절차 |
| 워크플로우 `.as_agent()` | 워크플로우를 단일 에이전트로 만들어 그대로 배포 |
| `FoundryAgent(..., allow_preview=True)` | 배포된 hosted agent를 이름으로 원격 호출 |

---

## ⚠️ 트러블슈팅

| 증상 | 해결 |
|------|------|
| `azd: command not found` | Azure Developer CLI 설치 (https://aka.ms/azd-install) |
| `azd ai agent` 서브커맨드 없음 | preview 확장 — 공식 hosted-agents 샘플 README에서 최신 절차 확인 |
| `init` 시 `target ... is inside the manifest directory` | `azd ai agent init`을 **예제 폴더 안**에서 실행하면 발생. 빈 작업 디렉토리를 따로 만들고 매니페스트를 **절대경로**로 지정 (Step B 참고) |
| `ModuleNotFoundError: agent_framework_foundry_hosting` | `pip install agent-framework-foundry-hosting` |
| 배포한 에이전트가 포털에 안 보임 | 배포에 쓴 프로젝트와 `.env`의 `FOUNDRY_PROJECT_ENDPOINT`가 같은지 확인 |
| `call` 실행 시 not found | `.env`의 `FOUNDRY_AGENT_NAME`이 배포한 이름과 같은지 확인 |
| `call` 실행 시 403 / PermissionDenied | 프로젝트(또는 리소스)에 데이터플레인 역할 필요: **Cognitive Services OpenAI User** + **Cognitive Services User**. 부여 후 전파에 1~2분 소요 |

---

## ✅ 체크포인트

- [ ] `maf_basic`을 `serve`로 확인 → `azd`로 배포 → 포털 Agents에 표시
- [ ] `python main.py call` → 배포된 에이전트 원격 호출 성공
- [ ] `maf_workflow`도 동일 절차로 배포(도전)

완료했다면 👉 **[부록. GitHub Copilot CLI](appendix-copilot-cli.md)** *(Optional)* 로 이어가세요.
