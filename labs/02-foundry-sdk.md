# Lab 02. Foundry SDK 기초 — 모델 호출

> ⏱️ 예상 시간: 15분

이 워크샵에서 **Foundry SDK(`azure-ai-projects`)를 직접 쓰는 예제는 이 랩 하나뿐**입니다.
"모델을 코드로 한 번 호출"하는 가장 작은 단위를 경험합니다. 이후 Lab 03~06은 모두
**Microsoft Agent Framework(MAF)** 로 에이전트·워크플로우를 만들고, 로컬 실행과
Foundry hosted agent 배포까지 진행합니다.

사용 SDK: `azure-ai-projects>=2.0.0`

---

## 🎯 목표

- Foundry SDK로 배포된 모델을 직접 호출하는 기본 코드를 이해한다.
- 엔드포인트·인증·모델 배포가 모두 정상인지 한 번에 확인한다.

---

## 사전 확인

```bash
# az login 되어 있어야 합니다
az account show

# .env 에 FOUNDRY_PROJECT_ENDPOINT, AZURE_AI_MODEL_DEPLOYMENT_NAME 이 채워져 있어야 합니다
```

> 💡 인증은 어떻게 되나요?
> 코드는 `DefaultAzureCredential`을 씁니다. `az login`으로 로그인된 자격증명을 자동으로 찾아 사용하므로, **키를 코드에 넣지 않습니다.**

---

## 모델과 직접 대화하기

📄 `code/01_chat_model.py`

```python
import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

load_dotenv()
PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
MODEL = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5.4")

# 프로젝트 클라이언트 (az login 자격증명 자동 사용)
project = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)

# OpenAI 호환 클라이언트를 가져와 Responses API 호출
openai = project.get_openai_client()
response = openai.responses.create(
    model=MODEL,
    input="프랑스의 면적은 몇 제곱 킬로미터인가요? 한 문장으로 답해주세요.",
)
print(response.output_text)
```

실행:

```bash
cd code
python 01_chat_model.py
```

**확인**: 모델이 생성한 한 문장짜리 답변이 출력되면 성공입니다. 이는 엔드포인트·인증·모델 배포가 모두 정상이라는 뜻입니다.

---

## 🧩 핵심 개념 정리

| 개념 | 설명 |
|------|------|
| `AIProjectClient` | Foundry 프로젝트에 접속하는 진입점 |
| `get_openai_client()` | 프로젝트에서 OpenAI 호환 클라이언트를 얻음 |
| Responses API (`responses.create`) | 모델에게 입력을 주고 응답을 받는 호출 |

> 💡 다음 랩부터는 이 "직접 호출" 대신, MAF의 `Agent`로 에이전트를 조립합니다. MAF가 내부적으로 이런 모델 호출을 대신 해줍니다.

---

## ⚠️ 트러블슈팅

| 증상 | 해결 |
|------|------|
| `DefaultAzureCredential` 인증 실패 | `az login`을 다시 실행하고, `az account show`로 로그인 확인 |
| `FOUNDRY_PROJECT_ENDPOINT` KeyError | `.env`가 저장소 루트에 있고 값이 채워졌는지 확인. `load_dotenv()` 호출 확인 |
| 403 / 권한 오류 | 리소스에 데이터플레인 역할이 필요합니다: **Cognitive Services OpenAI User**(모델 추론) + **Cognitive Services User**. 부여 후 전파에 1~2분 소요 |
| 모델 not found | `.env`의 `AZURE_AI_MODEL_DEPLOYMENT_NAME`이 실제 **배포 이름**과 일치하는지 확인 |
| `azure-ai-projects` 관련 오류 | 버전이 2.0.0 이상인지 확인: `pip show azure-ai-projects` |

---

## ✅ 체크포인트

- [ ] `01_chat_model.py` 실행 → 모델 응답 출력

완료했다면 👉 **[Lab 03. 첫 에이전트 (Agent Framework)](03-agent-framework-first.md)** 로 이동하세요.
