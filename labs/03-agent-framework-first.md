# Lab 03. 첫 에이전트 (Agent Framework)

> ⏱️ 예상 시간: 20분

Lab 02에서는 Foundry 모델을 직접 호출했습니다. 이제 **Microsoft Agent Framework(MAF)** 로
몇 줄의 코드만에 에이전트를 조립하고, **로컬에서 실행**한 뒤 **서버로 띄우는(serve)** 것까지 해봅니다.

이 랩부터 만드는 모든 예제는 **하나의 `main.py`** 로 세 가지 모드를 지원합니다.

| 모드 | 하는 일 |
|------|---------|
| `local` | 내 프로세스에서 에이전트를 직접 호출 (콘솔 테스트) |
| `serve` | Responses 프로토콜 서버로 띄움 (`http://localhost:8088`) — **Foundry hosted agent가 실행하는 바로 그 코드** |
| `call` | Foundry에 **배포된** hosted agent를 원격 호출 (Lab 06에서 사용) |

이렇게 하면 "로컬에서 돌던 그 에이전트"가 **그대로** Foundry에 배포됩니다.

---

## 🎯 목표

- MAF의 기본 구성요소(`FoundryChatClient`, `Agent`)를 이해한다.
- 에이전트를 `local`로 실행하고, `serve`로 띄워 HTTP로 호출해 본다.

---

## ⚠️ 패키지 & import 안내 (먼저 읽기)

Foundry 전용 클라이언트는 **`agent_framework.foundry`** 아래에 있습니다.

```python
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
```

- 설치: `python -m pip install -r requirements.txt` (루트의 `code/requirements.txt`)
- `agent-framework`는 빠르게 진화합니다. import 오류가 나면 [공식 문서](https://learn.microsoft.com/agent-framework/agents/providers/microsoft-foundry)에서 최신 경로를 확인하세요.

---

## 코드

📄 `code/maf_basic/main.py` (핵심 부분)

```python
import asyncio, os, sys
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient

load_dotenv()

def build_agent() -> Agent:
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )
    return Agent(
        client=client,
        name="HelloAgent",
        instructions="당신은 친절한 도우미입니다. 답변은 짧게 하세요.",
        default_options={"store": False},  # 히스토리는 호스팅 인프라가 관리
    )

async def run_local():
    agent = build_agent()
    print("에이전트:", await agent.run("프랑스의 수도는 어디인가요?"))

def run_serve():
    from agent_framework_foundry_hosting import ResponsesHostServer
    ResponsesHostServer(build_agent()).run()   # http://localhost:8088
```

> 💡 **핵심**: `build_agent()` 하나를 `local`과 `serve`가 공유합니다. 로컬에서 검증한 에이전트를 **똑같이** 서버로 노출하는 것이죠.

---

## 실행 1) 로컬 호출

```bash
cd code/maf_basic
cp .env.example .env      # 값 채우기 (루트 .env 를 복사해도 됩니다)
python main.py local
```

**확인**: "파리"라는 답이 콘솔에 출력됩니다.

## 실행 2) 서버로 띄우고 HTTP 호출

터미널 A:

```bash
python main.py serve
# → http://localhost:8088 에서 대기
```

터미널 B:

```bash
curl -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "프랑스의 수도는 어디인가요?", "stream": false}'
```

**확인**: HTTP 응답 본문에 에이전트의 답이 들어 있으면, **로컬에서 hosted agent와 동일한 방식으로** 에이전트를 노출한 것입니다. 이 상태를 그대로 Foundry에 올리는 것이 [Lab 06](06-deploy-hosted-agent.md)입니다.

---

## 🧩 핵심 개념

| 요소 | 설명 |
|------|------|
| `FoundryChatClient` | Foundry 프로젝트의 모델에 연결하는 채팅 클라이언트 |
| `Agent` | 이름 + 지시(instructions)로 정의하는 에이전트 |
| `agent.run(...)` | 응답을 한 번에 받는 호출 (async) |
| `ResponsesHostServer(agent)` | 에이전트를 Responses 프로토콜 HTTP 서버로 호스팅 |
| `default_options={"store": False}` | 대화 기록을 서비스에 저장하지 않음 (호스팅 인프라가 관리) |

---

## ⚠️ 트러블슈팅

| 증상 | 해결 |
|------|------|
| `ModuleNotFoundError: agent_framework.foundry` | `python -m pip install -r requirements.txt` 재실행 |
| `ModuleNotFoundError: agent_framework_foundry_hosting` | `python -m pip install -r requirements.txt` 재실행 |
| 인증 오류 | `az login` 재실행 |
| `.env` 값 없음 | MAF는 `.env`를 자동 로드하지 않습니다. 코드 상단 `load_dotenv()` 필수 |
| 포트 8088 사용 중 | 기존 serve 프로세스를 종료하거나 다른 포트로 실행 |

---

## ✅ 체크포인트

- [ ] `python main.py local` → 응답 출력
- [ ] `python main.py serve` + curl → HTTP로 응답 확인

완료했다면 👉 **[Lab 04. 도구 추가](04-agent-framework-tools.md)** 로 이동하세요.
