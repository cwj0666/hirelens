import sys
from pathlib import Path

# src/를 import 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastmcp import FastMCP

from hirelens.evaluation.models import (
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    EVALUATOR_ROLES,
    RAG_APPROVED_RESULT,
)
from hirelens.evaluation.storage import (
    format_retrieved_examples,
    get_retriever,
    init_db,
)
from hirelens.evaluation.workflow import build_graph, configure_llm

mcp = FastMCP(
    "hirelens",
    instructions="자기소개서 평가와 합격 사례 검색을 제공하는 MCP 서버",
)


@mcp.tool()
def evaluate_cover_letter(
    cover_letter: str,
    job_posting: str = "",
    industry: str = "",
    job_role: str = "",
    career_level: str = "자동",
    company_news: str = "",
    use_rag: bool = False,
    model_name: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
) -> dict:
    """
    자기소개서를 3인 평가자(HR, 현업 부서장, 인재개발팀)가 협상하여 평가한다.
    모집공고가 있으면 함께 전달하여 공고 요구사항 대비 평가를 수행한다.
    use_rag=True이면 합격 사례를 검색하여 평가에 참고한다.
    최종 판정(통과/보류/불통과), 점수, 근거 및 각 평가자별 상세 결과를 반환한다.
    """
    configure_llm(model_name=model_name, temperature=temperature)

    reference_examples = ""
    if use_rag:
        init_db()
        retriever = get_retriever(
            industry=industry or None,
            job_role=job_role or None,
            result=RAG_APPROVED_RESULT,
            k=3,
        )
        docs = retriever.invoke(cover_letter[:500])
        reference_examples = format_retrieved_examples(docs)

    graph = build_graph()
    result = graph.invoke({
        "cover_letter": cover_letter,
        "job_posting": job_posting,
        "career_level": career_level,
        "company_news": company_news,
        "use_rag": use_rag,
        "reference_examples": reference_examples,
    })

    evaluator_details = {}
    for role_key, role_name in EVALUATOR_ROLES.items():
        evals_key = f"{role_key}_evals"
        evals = result.get(evals_key, [])
        if evals:
            latest = evals[-1]
            evaluator_details[role_name] = {
                "판정": latest.decision,
                "점수": latest.score,
                "근거": latest.reasoning,
                "강점": latest.key_strengths,
                "약점": latest.key_weaknesses,
                "라운드수": len(evals),
            }

    return {
        "final_decision": result.get("final_decision", ""),
        "final_score": result.get("final_score", 0.0),
        "final_reasoning": result.get("final_reasoning", ""),
        "evaluator_details": evaluator_details,
        "rounds": result.get("current_round", 0),
        "interview_questions": result.get("interview_questions", {}),
    }


@mcp.tool()
def search_examples(
    industry: str = "",
    job_role: str = "",
    k: int = 3,
) -> str:
    """
    합격 사례 DB에서 유사한 자소서를 검색한다.
    업종(industry)과 직무(job_role)로 필터링하여 상위 k개를 반환한다.
    """
    init_db()

    retriever = get_retriever(
        industry=industry or None,
        job_role=job_role or None,
        result=RAG_APPROVED_RESULT,
        k=k,
    )

    # 빈 쿼리로 검색하여 전체 사례를 가져옴
    docs = retriever.invoke("자기소개서")
    if not docs:
        return "검색된 합격 사례가 없습니다."

    return format_retrieved_examples(docs)


if __name__ == "__main__":
    mcp.run()
