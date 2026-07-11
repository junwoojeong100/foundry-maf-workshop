"""
MAF 도구(함수) 에이전트 — 로컬 실행 & Foundry hosted agent 배포

에이전트에 @tool 함수를 붙여, 모델이 필요할 때 스스로 호출하게 합니다.
이 예제의 날씨 값은 외부 API가 아닌 무작위 모의 데이터입니다.
함수 도구는 호스팅되더라도 **에이전트의 프로세스 안에서** 실행됩니다.

모드:
  python main.py local    # 콘솔에서 직접 호출
  python main.py serve     # Responses 서버 (http://localhost:8088) ← hosted runtime 진입점
  python main.py call      # 배포된 hosted agent 원격 호출

환경변수:
  FOUNDRY_PROJECT_ENDPOINT, AZURE_AI_MODEL_DEPLOYMENT_NAME, FOUNDRY_AGENT_NAME
"""

import asyncio
import os
import sys
from random import randint
from typing import Annotated

from dotenv import load_dotenv
from pydantic import Field
from azure.identity import DefaultAzureCredential

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient

load_dotenv()

AGENT_NAME = os.environ.get("FOUNDRY_AGENT_NAME", "maf-tools-agent")


# ---------- 도구 정의 ----------
# docstring과 Field 설명이 모델에게 전달되어, 언제 이 도구를 쓸지 판단하는 근거가 됩니다.
# approval_mode="never_require"는 부작용 없는 모의 조회를 간단히 실습하기 위한 설정입니다.
# 운영에서는 도구의 위험도에 따라 승인 정책을 정하세요.
@tool(approval_mode="never_require")
def get_weather(
    location: Annotated[str, Field(description="날씨를 조회할 지역 이름")],
) -> str:
    """주어진 지역의 실습용 모의 날씨를 반환합니다."""
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


async def run_local() -> None:
    agent = build_agent()
    result = await agent.run("암스테르담 날씨 어때요?")
    print("에이전트:", result)


def run_serve() -> None:
    from agent_framework_foundry_hosting import ResponsesHostServer

    server = ResponsesHostServer(build_agent())
    server.run()


async def run_call() -> None:
    from agent_framework.foundry import FoundryAgent

    agent = FoundryAgent(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        agent_name=AGENT_NAME,
        credential=DefaultAzureCredential(),
        allow_preview=True,
    )
    result = await agent.run("암스테르담 날씨 어때요?")
    print("배포된 에이전트:", result)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "serve"
    if mode == "local":
        asyncio.run(run_local())
    elif mode == "serve":
        run_serve()
    elif mode == "call":
        asyncio.run(run_call())
    else:
        print(f"알 수 없는 모드: {mode} (local | serve | call)")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
