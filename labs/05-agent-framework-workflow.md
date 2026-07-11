# Lab 05. 워크플로우

> ⏱️ 예상 시간: 20분

**워크플로우(workflow)**는 여러 단계를 연결해, 각 단계가 데이터를 처리하고 다음 단계로 넘겨주는 구조입니다. 이 랩에서는 **여러 에이전트를 순차로 연결한** 워크플로우를 만들고, 그것을 **하나의 에이전트로 노출**해 로컬 실행·serve까지 진행합니다.

이 "워크플로우를 하나의 에이전트로 감싸는" 패턴이 [Lab 06](06-deploy-hosted-agent.md)에서 **워크플로우를 hosted agent로 배포**하는 열쇠입니다.

---

## 🎯 목표

- 워크플로우의 핵심 개념(executor, edge)을 이해한다.
- 여러 에이전트를 순차로 연결하고, `.as_agent()`로 단일 에이전트로 노출한다.
- `local`로 실행하고 `serve`로 띄운다.

---

## 개념: Executor와 Edge

| 용어 | 의미 |
|------|------|
| **Executor** | 워크플로우의 한 단계(처리 단위). 여기서는 각 에이전트를 `AgentExecutor`로 감쌈 |
| **Edge** | executor를 연결하는 방향. `add_edge(A, B)`는 A의 출력을 B의 입력으로 전달 |
| **`.as_agent()`** | 완성된 워크플로우를 **하나의 에이전트**처럼 호출 가능하게 노출 |

이번 예제의 흐름:

```
입력: "친환경 텀블러 브랜드의 슬로건을 만들어줘"
   │
   ▼  [writer]          슬로건 초안 작성
   │
   ▼  [legal_reviewer]  법적으로 문제없게 수정
   │
   ▼  [formatter]       레트로 스타일로 다듬어 최종 출력
```

> 💡 `context_mode="last_agent"`: 각 단계가 전체 대화가 아니라 **직전 단계의 출력만** 보도록 제한합니다.

---

## 코드

📄 `code/maf_workflow/main.py` (핵심 부분)

```python
import os
from azure.identity import DefaultAzureCredential
from agent_framework import Agent, AgentExecutor, WorkflowBuilder
from agent_framework.foundry import FoundryChatClient

def build_workflow_agent() -> Agent:
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )
    # 각 단계는 직전 단계의 출력만 입력으로 받습니다. "받은 텍스트를 처리 대상으로
    # 삼아 결과만 출력하고 되묻지 말라"고 명확히 지시해야 안정적으로 동작합니다.
    writer    = Agent(client=client, name="writer",
                      instructions="입력 주제로 슬로건 하나를 만들어 그 슬로건만 출력하세요. 질문하지 마세요.")
    reviewer  = Agent(client=client, name="legal_reviewer",
                      instructions="입력 슬로건을 법적으로 문제없게 고쳐 최종 한 줄만 출력하세요. 되묻지 마세요.")
    formatter = Agent(client=client, name="formatter",
                      instructions="입력 슬로건을 레트로 스타일로 다듬어 최종 결과만 출력하세요. 추가 정보를 요청하지 마세요.")

    writer_exec    = AgentExecutor(writer,    context_mode="last_agent")
    reviewer_exec  = AgentExecutor(reviewer,  context_mode="last_agent")
    formatter_exec = AgentExecutor(formatter, context_mode="last_agent")

    return (
        WorkflowBuilder(
            start_executor=writer_exec,
            output_from=[formatter_exec],   # 최종 출력은 formatter 결과만
        )
        .add_edge(writer_exec, reviewer_exec)
        .add_edge(reviewer_exec, formatter_exec)
        .build()
        .as_agent()                          # ← 워크플로우를 하나의 에이전트로 노출
    )
```

`local` / `serve` / `call` 진입점은 Lab 03·04와 동일하게, 이 `build_workflow_agent()`를 공유합니다.

---

## 실행

```bash
cd code/maf_workflow
cp .env.example .env      # 값 채우기

# 1) 로컬 실행
python main.py local

# 2) 서버로 띄우고(터미널 A) HTTP 호출(터미널 B)
python main.py serve
curl -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "친환경 텀블러 브랜드의 슬로건을 만들어줘", "stream": false}'
```

**확인**: writer → reviewer → formatter 세 단계를 거친 최종 슬로건이 나오면 성공입니다. 외부에서는 이 파이프라인이 **하나의 에이전트**처럼 보입니다.

---

## 🧩 핵심 개념

| 요소 | 설명 |
|------|------|
| `AgentExecutor(agent, context_mode=...)` | 에이전트를 워크플로우의 한 단계로 감쌈 |
| `WorkflowBuilder(start_executor=..., output_from=[...])` | 시작 단계와 최종 출력 단계를 지정 |
| `.add_edge(A, B)` | A의 출력을 B로 전달 |
| `.build().as_agent()` | 워크플로우를 단일 에이전트로 노출 → 호스팅 가능 |

---

## ⚠️ import 경로 안내

`agent-framework`의 워크플로우 API는 버전에 따라 경로가 다를 수 있습니다. 오류가 나면 [공식 샘플](https://github.com/microsoft/agent-framework/tree/main/python/samples/04-hosting/foundry-hosted-agents/responses/05_workflows)에서 최신 형태를 확인하세요.

> 이 워크플로우는 이전 에이전트의 assistant 메시지를 다음 에이전트가 이어서 처리하므로, 공식 샘플과 동일하게 `gpt-5.4`로 검증했습니다.

---

## ✅ 체크포인트

- [ ] `python main.py local` → 3단계를 거친 최종 출력
- [ ] `python main.py serve` + curl → 동일 확인
- [ ] `.as_agent()`가 왜 배포에 중요한지 설명할 수 있다

---

## 다음 단계

지금까지 만든 세 에이전트(기본·도구·워크플로우)는 모두 **내 컴퓨터에서** `local`/`serve`로 돌았습니다. 다음 랩에서는 이것을 **그대로 Foundry에 hosted agent로 배포**합니다.

완료했다면 👉 **[Lab 06. Foundry에 배포 (hosted agent)](06-deploy-hosted-agent.md)** 로 이동하세요.
