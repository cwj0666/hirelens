import os
from pathlib import Path
import sys

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters

from ..evaluation.models import DEFAULT_ADK_MODEL

MCP_SERVER_PATH = str(
    Path(__file__).resolve().parent.parent / "mcp" / "server.py"
)

hirelens_mcp = MCPToolset(
    connection_params=StdioConnectionParams(
        timeout=15.0,
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[MCP_SERVER_PATH],
        ),
    ),
)

evaluation_agent = Agent(
    name='evaluation_agent',
    model=os.getenv("ADK_MODEL", DEFAULT_ADK_MODEL),
    description='자소서를 3인 평가자(HR, 현업 부서장, 인재개발팀)가 협상하여 평가하는 에이전트',
    instruction=(
        '사용자의 자기소개서를 evaluate_cover_letter tool로 평가한다. '
        '모집공고가 있으면 job_posting 인자로 함께 전달한다. '
        '평가 결과(최종 판정, 점수, 각 평가자별 상세 결과)를 정리하여 전달한다.'
    ),
    output_key='evaluation_result',
    tools=[hirelens_mcp],
)
