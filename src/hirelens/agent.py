import json
import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from google.genai import types
from mcp import StdioServerParameters

from .tools.company_tools import get_code, get_company_info
from .tools.news_tools import get_company_news_report, search_company_news
from .evaluation.models import DEFAULT_ADK_MODEL
from .tools.session_tools import (
    extract_session_id,
    list_recent_sessions,
    load_evaluation_session,
    load_session_into_state,
)
MCP_SERVER_PATH = str(Path(__file__).resolve().parent / "mcp" / "server.py")

hirelens_mcp = MCPToolset(
    connection_params=StdioConnectionParams(
        timeout=15.0,
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[MCP_SERVER_PATH],
        ),
    ),
)

load_dotenv()


def _extract_user_text(user_content) -> str:
    if user_content is None:
        return ""
    if isinstance(user_content, str):
        return user_content

    parts = getattr(user_content, "parts", None) or []
    texts = []
    for part in parts:
        text = getattr(part, "text", None)
        if text:
            texts.append(text)
    return "\n".join(texts).strip()


def _make_text_response(text: str) -> types.Content:
    return types.Content(role="model", parts=[types.Part(text=text)])


def auto_load_session_callback(callback_context: CallbackContext):
    user_text = _extract_user_text(callback_context.user_content)
    session_id = extract_session_id(user_text)
    if not session_id:
        return None

    loaded, message = load_session_into_state(session_id, callback_context.state)
    if not loaded:
        return _make_text_response(message)

    if user_text.strip().upper() == session_id:
        return _make_text_response(
            message
            + "\n\n평가 세션을 불러왔습니다. 이제 이 결과를 기준으로 자소서 코칭이나 수정본 재평가를 이어갈 수 있습니다.",
        )

    return None


def _build_session_context(session_data: dict) -> str:
    session_snapshot = {
        "session_id": session_data.get("_session_id", ""),
        "company_info": session_data.get("_company_info", {}),
        "career_level": session_data.get("career_level", "자동"),
        "job_posting": session_data.get("_job_posting", ""),
        "company_news": session_data.get("_company_news", ""),
        "company_news_report": session_data.get("_company_news_report", {}),
        "final_decision": session_data.get("final_decision", ""),
        "final_score": session_data.get("final_score", 0.0),
        "final_reasoning": session_data.get("final_reasoning", ""),
        "hr_evals": session_data.get("hr_evals", []),
        "dept_head_evals": session_data.get("dept_head_evals", []),
        "talent_dev_evals": session_data.get("talent_dev_evals", []),
        "interview_questions": session_data.get("interview_questions", {}),
        "cover_letter": session_data.get("_cover_letter", ""),
    }
    return json.dumps(session_snapshot, ensure_ascii=False, indent=2)


def coaching_instruction(ctx: ReadonlyContext) -> str:
    session_data = ctx.state.get("session_data")

    instruction = (
        "당신은 자소서 코칭 전용 에이전트다.\n"
        "기본 역할:\n"
        "1. 저장된 평가 결과를 바탕으로 사용자 질문에 답한다.\n"
        "2. 자소서 문단별 수정 방향과 문장 예시를 제안한다.\n"
        "3. 면접 질문 답변 코칭을 제공한다.\n"
        "4. 사용자가 수정본을 주면 evaluate_cover_letter 도구로 재평가하고, 기존 세션과 차이를 비교한다.\n\n"
        "작업 원칙:\n"
        "- 세션이 아직 없으면 먼저 load_evaluation_session 또는 list_recent_sessions 사용을 우선 제안한다.\n"
        "- 세션이 로드된 뒤에는 기존 평가의 강점, 약점, 판정 근거를 근거로 답한다.\n"
        "- 수정본 재평가 시 가능하면 기존 세션의 모집공고와 경력 수준을 그대로 재사용한다.\n"
        "- 회사 관련 보강이 필요하면 get_code, get_company_info, get_company_news_report, search_company_news를 활용한다.\n"
        "- 재평가 결과를 설명할 때는 기존 결과 대비 점수, 판정, 약점 변화 중심으로 비교한다.\n"
        "- 모든 답변은 한국어로 작성한다.\n"
    )

    if not session_data:
        return (
            instruction
            + "\n현재 로드된 평가 세션이 없다. 세션 ID를 받으면 load_evaluation_session을 호출하라."
        )

    return (
        instruction
        + "\n현재 로드된 평가 세션 정보:\n"
        + _build_session_context(dict(session_data))
    )


_adk_model = os.getenv("ADK_MODEL", DEFAULT_ADK_MODEL)

root_agent = Agent(
    name="hirelens",
    model=_adk_model,
    description="저장된 평가 결과를 불러와 자소서 코칭과 수정본 재평가를 수행하는 에이전트",
    instruction=coaching_instruction,
    before_agent_callback=auto_load_session_callback,
    tools=[
        load_evaluation_session,
        list_recent_sessions,
        hirelens_mcp,
        get_code,
        get_company_info,
        get_company_news_report,
        search_company_news,
    ],
)
