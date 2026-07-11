"""
MAF 워크플로우 → hosted agent — 로컬 실행 & Foundry 배포

여러 에이전트를 순차 워크플로우로 연결한 뒤, `.as_agent()` 로 **하나의 에이전트로 감싸**
Foundry hosted agent로 배포합니다. (Foundry Agent Service는 단일 에이전트를 호스팅하므로,
워크플로우를 에이전트로 노출하는 것이 핵심입니다.)

  writer → legal_reviewer → formatter   를 하나의 에이전트처럼 호출

모드:
  python main.py local    # 콘솔에서 워크플로우 직접 실행
  python main.py serve     # Responses 서버 (http://localhost:8088) ← hosted runtime 진입점
  python main.py call      # 배포된 hosted agent(워크플로우) 원격 호출

환경변수:
  FOUNDRY_PROJECT_ENDPOINT, AZURE_AI_MODEL_DEPLOYMENT_NAME, FOUNDRY_AGENT_NAME
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential

from agent_framework import Agent, AgentExecutor, WorkflowBuilder
from agent_framework.foundry import FoundryChatClient

load_dotenv()

AGENT_NAME = os.environ.get("FOUNDRY_AGENT_NAME", "maf-workflow-agent")


def build_workflow_agent() -> Agent:
    """세 에이전트를 순차 워크플로우로 연결하고, 하나의 에이전트로 노출."""
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )

    # 각 단계는 '직전 단계의 출력'을 입력으로 받습니다(context_mode="last_agent").
    # 되묻지 말고, 받은 텍스트 자체를 처리 대상으로 삼아 결과만 출력하도록 명확히 지시합니다.
    writer = Agent(
        client=client,
        name="writer",
        instructions=(
            "당신은 뛰어난 슬로건 작가입니다. 입력으로 받은 주제에 대해 "
            "슬로건 하나를 새로 만들어 그 슬로건만 출력하세요. 질문하지 마세요."
        ),
    )
    reviewer = Agent(
        client=client,
        name="legal_reviewer",
        instructions=(
            "당신은 법률 검토자입니다. 입력으로 받은 슬로건을 법적으로 문제없도록 "
            "필요하면 고쳐서, 최종 슬로건 한 줄만 출력하세요. 되묻거나 설명하지 마세요."
        ),
    )
    formatter = Agent(
        client=client,
        name="formatter",
        instructions=(
            "당신은 콘텐츠 포매터입니다. 입력으로 받은 슬로건을 멋진 레트로 스타일로 "
            "다듬어 최종 결과만 출력하세요. 추가 정보를 요청하지 말고, 받은 슬로건을 그대로 다듬으세요."
        ),
    )

    # context_mode="last_agent": 각 단계가 전체 대화가 아니라 직전 단계의 출력만 보도록 제한
    writer_exec = AgentExecutor(writer, context_mode="last_agent")
    reviewer_exec = AgentExecutor(reviewer, context_mode="last_agent")
    formatter_exec = AgentExecutor(formatter, context_mode="last_agent")

    # 워크플로우 조립 → build() → as_agent() 로 단일 에이전트화
    return (
        WorkflowBuilder(
            start_executor=writer_exec,
            output_from=[formatter_exec],  # 최종 출력은 formatter 결과만
        )
        .add_edge(writer_exec, reviewer_exec)
        .add_edge(reviewer_exec, formatter_exec)
        .build()
        .as_agent()
    )


async def run_local() -> None:
    agent = build_workflow_agent()
    result = await agent.run("친환경 텀블러 브랜드의 슬로건을 만들어줘")
    print("워크플로우 결과:", result)


def run_serve() -> None:
    # 로컬에서 Azure VM 메타데이터를 조회하는 Statsbeat만 비활성화합니다.
    if not os.environ.get("FOUNDRY_HOSTING_ENVIRONMENT"):
        os.environ.setdefault("APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL", "true")

    from agent_framework_foundry_hosting import ResponsesHostServer

    server = ResponsesHostServer(build_workflow_agent())
    server.run()


async def run_call() -> None:
    from agent_framework.foundry import FoundryAgent

    agent = FoundryAgent(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        agent_name=AGENT_NAME,
        credential=DefaultAzureCredential(),
        allow_preview=True,
    )
    result = await agent.run("친환경 텀블러 브랜드의 슬로건을 만들어줘")
    print("배포된 워크플로우 에이전트:", result)


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
