"""
Lab 02: Foundry SDK 기초 — 모델과 직접 대화하기

이 워크샵에서 Foundry SDK(azure-ai-projects)를 직접 쓰는 예제는 이 하나뿐입니다.
"모델 호출"이라는 가장 기본 단위를 경험한 뒤, 이후 랩은 모두 Microsoft Agent Framework(MAF)로
에이전트·워크플로우를 만들고, 로컬 실행과 Foundry hosted agent 배포까지 진행합니다.

실행 전:
  1) az login 으로 로그인
  2) .env 파일에 FOUNDRY_PROJECT_ENDPOINT, AZURE_AI_MODEL_DEPLOYMENT_NAME 설정

실행:
  python 01_chat_model.py
"""

import os

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

load_dotenv()

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
MODEL = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5.4")

# 프로젝트 클라이언트 생성 (az login 자격증명을 자동으로 사용)
project = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)

# 프로젝트에서 OpenAI 호환 클라이언트를 가져옵니다.
openai = project.get_openai_client()

# Responses API로 모델을 한 번 호출합니다.
response = openai.responses.create(
    model=MODEL,
    input="프랑스의 면적은 몇 제곱 킬로미터인가요? 한 문장으로 답해주세요.",
)

print("모델 응답:")
print(response.output_text)
