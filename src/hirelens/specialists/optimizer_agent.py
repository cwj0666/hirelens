import os

from google.adk.agents import Agent
from google.adk.agents.readonly_context import ReadonlyContext

from ..evaluation.models import DEFAULT_ADK_MODEL

def optimizer_instruction(ctx: ReadonlyContext) -> str:
    company = ctx.state.get("company_info", "회사 정보 없음")
    evaluation = ctx.state.get("evaluation_result", "평가 결과 없음")
    job_posting = ctx.state.get("job_posting", "")

    base = (
        "당신은 자소서 최적화 전문가입니다.\n\n"
        f"## 회사 정보\n{company}\n\n"
        f"## 평가 결과\n{evaluation}\n\n"
    )

    if job_posting:
        base += f"## 모집공고\n{job_posting}\n\n"

    base += (
        "## 지시사항\n"
        "위 정보를 종합하여 자소서 수정안을 제시하라. 수정안에는 반드시 다음을 포함한다:\n"
        "1. 평가에서 지적된 약점을 보완하는 구체적 방안\n"
        "2. 회사의 업종, 사업내용, 전망을 반영한 지원동기 강화 방안\n"
        "3. 모집공고의 자격요건/우대사항에 맞춘 경험 서술 개선\n"
        "4. 각 항목별 수정 전/후 문장 예시\n"
        "5. 전체적인 구조와 흐름에 대한 개선 제안\n\n"
        "한국어로 상세하게 답변한다."
    )
    return base


optimizer_agent = Agent(
    name='optimizer_agent',
    model=os.getenv("ADK_MODEL", DEFAULT_ADK_MODEL),
    description='회사 정보와 평가 결과를 종합하여 자소서 수정안을 제시하는 에이전트',
    instruction=optimizer_instruction,
)
