"""
MAF 기본 에이전트 — 로컬 실행 & Foundry hosted agent 배포

하나의 파일로 세 가지 모드를 지원합니다.

  python main.py local    # 내 프로세스에서 에이전트를 직접 호출 (콘솔 테스트)
  python main.py serve     # Responses 서버로 띄움 (http://localhost:8088) ← hosted runtime 진입점
  python main.py call      # Foundry에 "배포된" hosted agent를 원격 호출

인자 없이 `python main.py`로 실행하면 serve 모드입니다. (Lab 06 code deployment 진입점)

환경변수 (.env 또는 호스팅 인프라가 주입):
  FOUNDRY_PROJECT_ENDPOINT       Foundry 프로젝트 엔드포인트
  AZURE_AI_MODEL_DEPLOYMENT_NAME 배포한 모델 이름 (예: gpt-5.4)
  FOUNDRY_AGENT_NAME             call 모드에서 호출할 hosted agent 이름
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient

load_dotenv()

INSTRUCTIONS = "당신은 친절한 도우미입니다. 답변은 짧게 하세요."
# hosted agent로 배포할 때의 `--agent-name` 값과 맞추세요.
AGENT_NAME = os.environ.get("FOUNDRY_AGENT_NAME", "maf-basic-agent")


def build_agent() -> Agent:
    """로컬 실행과 서버 호스팅이 공유하는 에이전트 정의."""
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )
    return Agent(
        client=client,
        name="HelloAgent",
        instructions=INSTRUCTIONS,
        # 히스토리는 호스팅 인프라가 관리하므로 서비스 저장은 끕니다.
        default_options={"store": False},
    )


async def run_local() -> None:
    """모드 local: 내 프로세스에서 에이전트를 직접 호출."""
    agent = build_agent()
    result = await agent.run("프랑스의 수도는 어디인가요?")
    print("에이전트:", result)


def run_serve() -> None:
    """모드 serve: Responses 프로토콜 서버로 호스팅 (http://localhost:8088).

    이 진입점이 곧 Foundry hosted agent가 실행하는 코드입니다.
    """
    # 로컬에서 Azure VM 메타데이터를 조회하는 Statsbeat만 비활성화합니다.
    if not os.environ.get("FOUNDRY_HOSTING_ENVIRONMENT"):
        os.environ.setdefault("APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL", "true")

    from agent_framework_foundry_hosting import ResponsesHostServer

    server = ResponsesHostServer(build_agent())
    server.run()


async def run_call() -> None:
    """모드 call: Foundry에 배포된 hosted agent를 이름으로 원격 호출."""
    from agent_framework.foundry import FoundryAgent

    agent = FoundryAgent(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        agent_name=AGENT_NAME,
        credential=DefaultAzureCredential(),
        allow_preview=True,  # hosted agent(service-side session)용 preview surface
    )
    result = await agent.run("프랑스의 수도는 어디인가요?")
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
