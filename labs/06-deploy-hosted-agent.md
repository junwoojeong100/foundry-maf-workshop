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

hosted agent는 **컨테이너로 패키징된 MAF 앱**입니다. Lab 03~05에서 만든 **세 예제 모두** 배포 대상이며, 각 폴더에는 이미 배포에 필요한 파일이 똑같은 구성으로 들어 있습니다.

| 예제 | 만든 랩 | hosted agent 이름 |
|------|:------:|-------------------|
| `maf_basic/` | Lab 03 | `maf-basic-agent` |
| `maf_tools/` | Lab 04 | `maf-tools-agent` |
| `maf_workflow/` | Lab 05 | `maf-workflow-agent` |

아래에서는 `maf_basic`을 예로 전체 절차를 따라간 뒤, **나머지 둘도 완전히 같은 방법**으로 배포합니다. 각 폴더에 들어 있는 배포 파일은 다음과 같습니다.

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

hosted agent 배포는 **Azure Developer CLI(`azd`)** 로 합니다. `azd`는 인프라 프로비저닝과 코드(컨테이너) 배포를 **한 번에** 처리하는 개발자용 CLI로, `az`(Azure CLI)와는 **별개 도구**입니다.

이 워크샵은 `azd`의 **`ai agent` 확장**(preview)을 쓰는데, 이 확장이 Foundry와 하는 일은 다음과 같습니다.

1. **`azd ai agent init`** — 예제 매니페스트(`agent.manifest.yaml`)를 읽어 `azure.yaml`·`infra/`·소스 복사본을 갖춘 **azd 프로젝트**를 생성하고, Lab 01에서 만든 **기존 Foundry 프로젝트**(`--project-id`)와 **모델 배포**(`--model-deployment`)에 연결합니다.
2. **`azd up`**(= `provision` + `deploy`) — 컨테이너를 **원격 빌드**해 컨테이너 레지스트리에 올린 뒤, 이를 **Foundry 프로젝트 안의 hosted agent로 등록**합니다. 배포 상태는 `.azure/` 폴더(azd 환경)에 저장됩니다.
3. 이후 **Foundry가 그 컨테이너를 호스팅**하고, 실행 시 `FOUNDRY_PROJECT_ENDPOINT`·`AZURE_AI_MODEL_DEPLOYMENT_NAME`을 **자동 주입**합니다.

즉 `azd ai agent`는 "내 MAF 컨테이너"를 **기존 Foundry 프로젝트에 얹는 다리** 역할입니다. Foundry 프로젝트·모델 자체는 새로 만들지 않고 재사용합니다.

```bash
# 설치 확인 (없으면 https://aka.ms/azd-install 참고)
azd version

# 로그인 (az login 과는 별개의 인증 컨텍스트입니다 — 둘 다 필요)
azd auth login
```

> ⚠️ `azd ai agent`와 `agent-framework-foundry-hosting`은 **preview**입니다. 명령·패키지 이름이 바뀔 수 있으니, 문제가 생기면 [공식 hosted-agents 샘플](https://github.com/microsoft/agent-framework/tree/main/python/samples/04-hosting/foundry-hosted-agents)의 README에서 최신 절차를 확인하세요.

---

## Step A. 배포 전 — 로컬에서 다시 확인

**배포 대상은 Lab 03~05에서 만든 세 예제의 소스코드**입니다. 여기서는 **Lab 03의 `code/maf_basic/`** 를 예로 전체 절차를 따라가고, Step B 끝에서 나머지 둘(`maf_tools`, `maf_workflow`)도 같은 방법으로 배포합니다.

먼저 배포할 `maf_basic`이 로컬에서 정상 동작하는지 확인합니다.

```bash
cd code/maf_basic
cp .env.example .env      # FOUNDRY_PROJECT_ENDPOINT, AZURE_AI_MODEL_DEPLOYMENT_NAME 채우기
python main.py serve

# 다른 터미널에서
curl -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" -d '{"input": "안녕!"}'
```

응답이 오면 배포 준비 완료입니다. **이 `main.py`가 그대로 컨테이너로 패키징되어 배포됩니다.**

---

## Step B. Foundry에 배포하기

> 🧭 **헷갈리지 마세요 — 무엇을 배포하나?**
> - **배포 대상(코드)** = Lab 03~05에서 만든 예제(`maf_basic` / `maf_tools` / `maf_workflow`)의 `main.py`. 여기서는 `maf_basic`이 예시입니다.
> - **배포될 곳(인프라)** = Lab 01에서 미리 만들어 둔 **기존 Foundry 프로젝트**. 새로 만들지 않고 그대로 재사용합니다.
>
> 즉 "Lab 01 프로젝트"는 배포하는 물건이 아니라, 코드가 **올라갈 자리**입니다.

기존 Foundry 프로젝트를 재사용하기 위해 `azd ai agent init`의 `--project-id`(`-p`)·`--model-deployment`(`-d`) 플래그를 씁니다.

### B-1. 기존 Foundry 프로젝트의 리소스 ID 확인

지금까지 프로젝트 *엔드포인트*와 *모델 배포 이름*은 `.env`에 있지만, 배포에는 프로젝트의 **리소스 ID**가 추가로 필요합니다. 아래로 얻습니다.

```bash
# <리소스이름>·<리소스그룹>·<프로젝트이름>은 프로젝트를 만들 때 정한 값
az cognitiveservices account project show \
  --name <리소스이름> -g <리소스그룹> --project-name <프로젝트이름> \
  --query id -o tsv
# 출력 예:
# /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<리소스이름>/projects/<프로젝트이름>
```

> 💡 `.env`의 엔드포인트 `https://<리소스이름>.services.ai.azure.com/api/projects/<프로젝트이름>`에서 `<리소스이름>`과 `<프로젝트이름>`을 그대로 읽을 수 있습니다. 리소스 그룹은 `az cognitiveservices account list -o table`로 확인하세요.

### B-2. 초기화 → 배포

> ⚠️ **디렉토리 주의**: `azd ai agent init`은 현재 폴더 **안에 `<agent-name>/` 서브폴더**를 만들고, 거기에 `azure.yaml`·`infra/`·`src/<agent-name>/`(예제 소스 복사본)를 생성합니다. 예제 폴더(`maf_basic/`) 안에서 실행하면 파일이 섞이므로, 아래처럼 **빈 작업 디렉토리**에서 진행합니다.

```bash
# 0. 배포용 작업 디렉토리 (예제 폴더 밖의 빈 폴더)
mkdir -p ~/maf-deploy && cd ~/maf-deploy

# 1. 매니페스트로 초기화 — 배포할 코드(-m)를 기존 프로젝트(-p)에 연결
#    -m           : 배포할 예제(Lab 03~05)의 매니페스트 (절대경로. GitHub URL도 가능)
#    -p / --project-id      : B-1에서 얻은 기존 프로젝트 리소스 ID
#    -d / --model-deployment: 배포한 모델 이름 (예: gpt-5.4)
azd ai agent init \
  -m /절대경로/code/maf_basic/agent.manifest.yaml \
  --project-id "<B-1에서 얻은 프로젝트 리소스 ID>" \
  --model-deployment gpt-5.4
# init 도중 Application Insights를 붙일지 묻는 프롬프트가 나옵니다(선택 사항).
# 관측(로그·추적)이 필요 없으면 건너뛰어도 배포에는 지장이 없습니다.

# 2. 프로비저닝 + 배포를 한 번에 (컨테이너 remote build → hosted agent 생성)
#    → ~/maf-deploy/maf-basic-agent/ 안에서 실행
cd maf-basic-agent
azd up
```

> 💡 **첫 `azd up`**은 배포용 **환경 이름(environment)**, **구독**, **리전(location)**을 물어봅니다(선택 값은 `.azure/` 폴더에 저장됨). 여기서 고르는 리전은 **새로 만들 리소스**(컨테이너 레지스트리 등)의 위치이며, Lab 01에서 만든 프로젝트·모델은 위치와 무관하게 그대로 재사용됩니다.

> 💡 `azd up` 대신 `azd provision`(리소스) → `azd deploy`(코드)로 나눠 실행해도 됩니다. 기존 프로젝트를 재사용하므로 프로비저닝 단계에서는 **컨테이너 레지스트리 연결**과 (선택 시) **Application Insights** 정도만 추가되고, 프로젝트·모델은 기존 것을 그대로 씁니다.
>
> `azd ai agent`는 **preview**입니다. 플래그가 바뀔 수 있으니 `azd ai agent init --help`로 최신 목록을 확인하세요.

배포가 끝나면 Foundry 호스팅 인프라가 컨테이너에 다음 환경변수를 **자동 주입**합니다.

- `FOUNDRY_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- `APPLICATIONINSIGHTS_CONNECTION_STRING` *(Application Insights를 붙였을 때만)*

**확인**: CLI로 `azd ai agent show maf-basic-agent`의 `Status`가 **active**이면 성공입니다. [포털](https://ai.azure.com) → 프로젝트 → **Agents** 목록에도 `maf-basic-agent`가 보입니다. 성공 시 `azd up` 출력 끝에 **Agent endpoint(responses)** URL이 표시됩니다.

> **나머지 두 예제도 똑같은 절차로 배포합니다.** `-m` 매니페스트 경로만 바꾸면 됩니다(`-p`·`-d`는 동일한 프로젝트 값을 재사용).
> - `maf_tools/agent.manifest.yaml` → **Lab 04**의 도구 에이전트(`maf-tools-agent`). 함수 도구가 컨테이너 안에서 함께 실행됩니다.
> - `maf_workflow/agent.manifest.yaml` → **Lab 05**의 워크플로우(`maf-workflow-agent`). `.as_agent()`로 단일 에이전트가 되어 있으므로, hosting 입장에서는 일반 에이전트와 동일합니다.
>
> 각 예제는 **별도의 빈 작업 디렉토리**에서 `init`하는 것을 권장합니다(예: `~/maf-deploy-tools`, `~/maf-deploy-workflow`). 배포가 끝나면 포털 **Agents** 목록에 세 에이전트가 모두 보입니다.

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
# 각 예제 폴더에서, .env 값을 배포한 대상과 맞춘 뒤
python main.py call
```

> ⚠️ **엔드포인트 확인**: `call`은 `.env`의 `FOUNDRY_PROJECT_ENDPOINT`가 가리키는 프로젝트에서 에이전트를 찾습니다. Step B에서 **기존 프로젝트를 재사용**했다면 이 값은 지금까지 쓰던 그대로면 됩니다(바꿀 필요 없음). 다른 프로젝트에 배포했다면 그 프로젝트 엔드포인트로 맞추세요. `FOUNDRY_AGENT_NAME`도 배포한 이름과 같은지 확인합니다.

각 예제의 `call` 모드는 자기 폴더의 기본 이름·질문을 사용합니다.

| 예제 폴더 | `FOUNDRY_AGENT_NAME` | call 시 보내는 질문 |
|-----------|----------------------|---------------------|
| `maf_basic` | `maf-basic-agent` | "프랑스의 수도는 어디인가요?" |
| `maf_tools` | `maf-tools-agent` | "암스테르담 날씨 어때요?" |
| `maf_workflow` | `maf-workflow-agent` | "친환경 텀블러 브랜드의 슬로건을 만들어줘" |

**확인**: 로컬이 아니라 **Foundry에 배포된** 에이전트가 답을 돌려주면 성공입니다.

> 🔎 `FoundryChatClient` vs `FoundryAgent`
> - `Agent(client=FoundryChatClient(...))` (serve/local) — 정의를 **내 코드가 소유**.
> - `FoundryAgent(agent_name=...)` (call) — 정의가 **Foundry에 배포**되어 있고, 이름으로 참조.

> 🔧 **배포 후 유용한 `azd ai agent` 명령** — 각 배포 작업 디렉토리 안에서 실행합니다(에이전트 이름은 `azure.yaml`에서 자동 해석).
> - `azd ai agent show` — 상태 확인(`active` 이면 정상)
> - `azd ai agent invoke '<질문>'` — 빠른 원격 호출 테스트(인자 2개면 `<이름> '<질문>'`)
> - `azd ai agent monitor --follow` — 컨테이너 실행 로그 실시간 스트리밍(문제 진단)
> - `azd ai agent run` — 배포 없이 로컬에서 실행(개발용, `python main.py serve` 와 유사)

---

## Step D. 정리 — 리소스 삭제 *(실습 후 권장)*

배포한 hosted agent와 그 과정에서 만든 Azure 리소스는 **계속 과금**됩니다. 실습을 마쳤다면 삭제하세요.

**배포에 사용한 각 작업 디렉토리**(예: `~/maf-deploy/maf-basic-agent`)에서 실행합니다.

```bash
cd ~/maf-deploy/maf-basic-agent
azd down --purge      # 확인 프롬프트에 y. --purge 는 소프트 삭제 리소스까지 완전 삭제
```

- `azd down`은 **azd가 프로비저닝한 리소스만** 지웁니다: 컨테이너 레지스트리, hosted agent 컨테이너, (붙였다면) Application Insights.
- **Lab 01에서 만든 Foundry 프로젝트·모델 배포는 삭제되지 않습니다**(azd가 만든 게 아니므로 그대로 유지 → 다음 실습에 재사용 가능).
- 세 예제를 각각 배포했다면 **작업 디렉토리마다 한 번씩** `azd down`을 실행하세요.
- 포털 **Agents** 목록에 에이전트가 남아 있으면 프로젝트 → **Agents** 에서 직접 삭제합니다.
- Foundry 프로젝트까지 **완전히** 없애려면 [포털](https://ai.azure.com)이나 `az group delete --name <리소스그룹>`으로 리소스 그룹 전체를 삭제하세요.

---

## 🧩 핵심 개념 정리

| 개념 | 설명 |
|------|------|
| `ResponsesHostServer(agent).run()` | 에이전트를 Responses 서버로 노출 (serve = 컨테이너 진입점) |
| `agent.yaml` / `agent.manifest.yaml` | 컨테이너 에이전트 설정과 배포 매니페스트 |
| `azd ai agent init` → `provision` → `deploy` | hosted agent 배포 절차 |
| 워크플로우 `.as_agent()` | 워크플로우를 단일 에이전트로 만들어 그대로 배포 |
| `FoundryAgent(..., allow_preview=True)` | 배포된 hosted agent를 이름으로 원격 호출 |
| `azd 환경(.azure/)` | 배포 대상 구독·리전·프로젝트 등 상태를 저장하는 azd 작업 단위 |
| `azd down` | 실습으로 만든 Azure 리소스 삭제(정리) — 기존 Foundry 프로젝트·모델은 유지 |

---

## ⚠️ 트러블슈팅

| 증상 | 해결 |
|------|------|
| `azd: command not found` | Azure Developer CLI 설치 (https://aka.ms/azd-install) |
| `azd ai agent` 서브커맨드 없음 | preview 확장 — 공식 hosted-agents 샘플 README에서 최신 절차 확인 |
| `init` 시 파일이 섞임 / 매니페스트 관련 오류 | `azd ai agent init`을 **예제 폴더 안**에서 실행하면 발생. 빈 작업 디렉토리에서 실행하고 매니페스트를 **절대경로**로 지정 (Step B 참고) |
| `--project-id`/`--model-deployment` 플래그 없음 | `azd ai agent` 확장 버전이 낮음. `azd ai agent version`으로 확인하고 최신 preview로 갱신 |
| `ModuleNotFoundError: agent_framework_foundry_hosting` | `pip install agent-framework-foundry-hosting` |
| 배포한 에이전트가 포털에 안 보임 | 배포에 쓴 프로젝트와 `.env`의 `FOUNDRY_PROJECT_ENDPOINT`가 같은지 확인 |
| `call` 실행 시 not found | `.env`의 `FOUNDRY_AGENT_NAME`이 배포한 이름과 같은지 확인. `azd ai agent invoke <이름> '<질문>'`으로도 직접 호출해 볼 수 있음 |
| `call` 실행 시 403 / PermissionDenied | 프로젝트(또는 리소스)에 데이터플레인 역할 필요: **Cognitive Services OpenAI User** + **Cognitive Services User**. 부여 후 전파에 1~2분 소요 |
| 배포 리소스를 정리하고 싶음 | 각 배포 작업 디렉토리에서 `azd down --purge` (Step D 참고). 기존 Foundry 프로젝트·모델은 삭제되지 않음 |

---

## ✅ 체크포인트

- [ ] `maf_basic`을 `serve`로 확인 → `azd`로 배포 → 포털 Agents에 표시
- [ ] `python main.py call` → 배포된 에이전트 원격 호출 성공
- [ ] `maf_tools`, `maf_workflow`도 동일 절차로 배포 → 포털 Agents에 세 에이전트 모두 표시
- [ ] *(실습 후)* 각 작업 디렉토리에서 `azd down`으로 리소스 정리

완료했다면 👉 **[부록. GitHub Copilot CLI](appendix-copilot-cli.md)** *(Optional)* 로 이어가세요.
