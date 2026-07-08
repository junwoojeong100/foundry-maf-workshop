# Lab 04. 도구(함수) 추가

> ⏱️ 예상 시간: 20분

에이전트에 **도구(tool)**를 붙이면, 모델이 스스로 할 수 없는 일(외부 데이터 조회, API 호출 등)을 함수로 위임할 수 있습니다. 에이전트는 질문을 보고 **필요할 때 스스로 도구를 호출**합니다.

Lab 03과 똑같이 `local` / `serve` / `call` 세 모드를 지원합니다. 여기서는 도구가 붙은 에이전트를 배포해도 **함수 도구가 에이전트 프로세스 안에서 실행**된다는 점을 확인합니다.

---

## 🎯 목표

- 일반 파이썬 함수를 `@tool`로 에이전트 도구로 만든다.
- 도구가 붙은 에이전트를 `local`로 실행하고 `serve`로 띄운다.

---

## 도구란?

에이전트는 텍스트만 생성할 수 있을 뿐, "지금 암스테르담 날씨"처럼 실시간·외부 정보는 알 수 없습니다. 도구는 그 간극을 메웁니다.

```
사용자: "암스테르담 날씨 어때?"
  → 에이전트: get_weather 도구가 필요하겠군  (모델의 판단)
  → get_weather("암스테르담") 실행               (프레임워크가 호출)
  → 결과를 받아 자연어로 답변                     (모델이 정리)
```

---

## 코드

📄 `code/maf_tools/main.py` (핵심 부분)

```python
import os
from typing import Annotated
from random import randint
from pydantic import Field
from azure.identity import DefaultAzureCredential
from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient

# docstring과 Field 설명이 모델에게 전달되어, 언제 이 도구를 쓸지 판단하는 근거가 됩니다.
# approval_mode="never_require" 는 실습 편의용. 운영에서는 "always_require" 권장.
@tool(approval_mode="never_require")
def get_weather(
    location: Annotated[str, Field(description="날씨를 조회할 지역 이름")],
) -> str:
    """주어진 지역의 현재 날씨를 반환합니다."""
    conditions = ["맑음", "흐림", "비", "폭풍"]
    return f"{location}의 날씨는 {conditions[randint(0, 3)]}, 최고 기온 {randint(10, 30)}°C입니다."

def build_agent() -> Agent:
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )
    return Agent(
        client=client,
        name="WeatherAgent",
        instructions="당신은 날씨 도우미입니다. 날씨 질문에는 get_weather 도구를 사용해 답하세요.",
        tools=[get_weather],
        default_options={"store": False},
    )
```

`serve` / `call` 진입점은 Lab 03과 동일합니다.

---

## 실행

```bash
cd code/maf_tools
cp .env.example .env      # 값 채우기

# 1) 로컬 호출
python main.py local

# 2) 서버로 띄우고(터미널 A) HTTP 호출(터미널 B)
python main.py serve
curl -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "암스테르담 날씨 어때요?"}'
```

**확인**: 에이전트가 `get_weather`를 자동 호출해, 날씨 함수의 결과를 반영한 답변을 내놓으면 성공입니다.

---

## 🧩 핵심 개념

| 요소 | 설명 |
|------|------|
| `@tool` | 일반 함수를 에이전트 도구로 등록하는 데코레이터 |
| docstring | 도구의 용도 설명 → 모델이 언제 쓸지 판단하는 근거 |
| `Annotated[..., Field(description=...)]` | 파라미터 설명 → 모델이 인자를 채우는 근거 |
| `tools=[...]` | 에이전트에 도구 목록 전달 |
| `approval_mode` | `"always_require"`면 실행 전 사용자 승인 요구 (운영 권장) |

> 💡 함수 도구는 **`FoundryChatClient` 기반 에이전트가 소유**하므로, 로컬이든 hosted든 **에이전트 프로세스 안에서** 실행됩니다. (반면 Foundry의 hosted 도구 — web search, code interpreter 등 — 는 서버 정의에 붙입니다.)

---

## 🔬 더 해보기 (시간이 남으면)

- 도구를 하나 더 추가해 보세요. 예: `get_time(timezone)` — 특정 시간대의 현재 시각 반환.
- `instructions`를 바꿔 에이전트의 말투를 조정해 보세요.

---

## ⚠️ 트러블슈팅

| 증상 | 해결 |
|------|------|
| 에이전트가 도구를 호출하지 않음 | `instructions`에 도구 사용을 명시하고, docstring을 더 명확히 작성 |
| `@tool` import 오류 | import 경로를 [공식 샘플](https://github.com/microsoft/agent-framework/tree/main/python/samples)에서 확인 |
| pydantic 관련 오류 | `pip install pydantic` |

---

## ✅ 체크포인트

- [ ] `python main.py local` → 도구 호출 결과 반영된 답변
- [ ] `python main.py serve` + curl → 동일 확인

완료했다면 👉 **[Lab 05. 워크플로우](05-agent-framework-workflow.md)** 로 이동하세요.
