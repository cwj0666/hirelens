from collections import Counter
from typing import Any, Dict, Literal

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from .models import (
    DEFAULT_MAX_ROUNDS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_WEIGHTS,
    EVALUATOR_ROLES,
    EVAL_STATE_KEYS,
    EvaluatorOutput,
    InterviewQuestions,
    NegotiationState,
)
from .prompts import (
    DEPT_HEAD_EVAL_TEMPLATE,
    HR_EVAL_TEMPLATE,
    INTERVIEW_QUESTION_TEMPLATE,
    NEGOTIATION_TEMPLATE,
    TALENT_DEV_EVAL_TEMPLATE,
)

_llm_config: dict[str, Any] = {
    "model_name": DEFAULT_MODEL,
    "temperature": DEFAULT_TEMPERATURE,
    "weights": None,
}


def configure_llm(
    model_name: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    weights: dict[str, float] | None = None,
) -> None:
    _llm_config["model_name"] = model_name
    _llm_config["temperature"] = temperature
    _llm_config["weights"] = weights


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=_llm_config["model_name"],
        temperature=_llm_config["temperature"],
    )


def _get_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=EvaluatorOutput)


def get_role_weights(normalize: bool = False) -> tuple[dict[str, float], float]:
    custom_weights = _llm_config.get("weights")
    role_weights = dict(custom_weights) if custom_weights else dict(DEFAULT_WEIGHTS)
    total_weight = sum(role_weights.values())

    if normalize and total_weight > 0:
        role_weights = {
            role: weight / total_weight
            for role, weight in role_weights.items()
        }

    return role_weights, total_weight


def _get_latest_eval(state: NegotiationState, role_key: str) -> EvaluatorOutput:
    evals = getattr(state, EVAL_STATE_KEYS[role_key])
    return evals[-1]


def _format_other_evals(state: NegotiationState, exclude_role: str) -> str:
    lines = []
    for role_key, role_name in EVALUATOR_ROLES.items():
        if role_key == exclude_role:
            continue
        ev = _get_latest_eval(state, role_key)
        lines.append(
            f"### {role_name}\n"
            f"- 판정: {ev.decision}, 점수: {ev.score}\n"
            f"- 근거: {ev.reasoning}\n"
            f"- 강점: {', '.join(ev.key_strengths)}\n"
            f"- 약점: {', '.join(ev.key_weaknesses)}",
        )
    return "\n\n".join(lines)


def _evaluate(
    state: NegotiationState,
    role_key: str,
    template: str,
) -> Dict[str, Any]:
    examples_text = ""
    if state.use_rag and state.reference_examples:
        examples_text = state.reference_examples

    job_posting_text = state.job_posting or "모집공고 정보 없음"

    parser = _get_parser()
    prompt = PromptTemplate(
        template=template,
        input_variables=[
            "cover_letter", "job_posting", "reference_examples",
            "career_level", "company_news",
        ],
        partial_variables={"format_instruction": parser.get_format_instructions()},
    )
    eval_chain = prompt | _get_llm() | parser
    result = eval_chain.invoke({
        "cover_letter": state.cover_letter,
        "job_posting": job_posting_text,
        "reference_examples": examples_text,
        "career_level": state.career_level or "자동",
        "company_news": state.company_news or "뉴스 정보 없음",
    })
    state_key = EVAL_STATE_KEYS[role_key]
    return {state_key: [result]}


def evaluate_hr(state: NegotiationState) -> Dict[str, Any]:
    return _evaluate(state, "hr", HR_EVAL_TEMPLATE)


def evaluate_dept_head(state: NegotiationState) -> Dict[str, Any]:
    return _evaluate(state, "dept_head", DEPT_HEAD_EVAL_TEMPLATE)


def evaluate_talent_dev(state: NegotiationState) -> Dict[str, Any]:
    return _evaluate(state, "talent_dev", TALENT_DEV_EVAL_TEMPLATE)


def check_consensus(state: NegotiationState) -> Dict[str, Any]:
    decisions = [
        _get_latest_eval(state, role).decision
        for role in EVALUATOR_ROLES
    ]
    is_consensus = len(set(decisions)) == 1
    current_round = max(len(state.hr_evals) - 1, 0)
    return {
        "is_consensus": is_consensus,
        "current_round": current_round,
    }


def negotiate(state: NegotiationState) -> Dict[str, Any]:
    parser = _get_parser()
    llm = _get_llm()
    updates = {}

    for role_key, role_name in EVALUATOR_ROLES.items():
        my_eval = _get_latest_eval(state, role_key)
        other_text = _format_other_evals(state, exclude_role=role_key)

        examples_text = ""
        if state.use_rag and state.reference_examples:
            examples_text = state.reference_examples

        job_posting_text = state.job_posting or "모집공고 정보 없음"

        prompt = PromptTemplate(
            template=NEGOTIATION_TEMPLATE,
            input_variables=[
                "role_name", "my_decision", "my_score",
                "my_reasoning", "other_evaluations",
                "cover_letter", "job_posting", "reference_examples",
                "career_level", "company_news",
            ],
            partial_variables={
                "format_instruction": parser.get_format_instructions(),
            },
        )
        nego_chain = prompt | llm | parser
        result = nego_chain.invoke({
            "role_name": role_name,
            "my_decision": my_eval.decision,
            "my_score": my_eval.score,
            "my_reasoning": my_eval.reasoning,
            "other_evaluations": other_text,
            "cover_letter": state.cover_letter,
            "job_posting": job_posting_text,
            "reference_examples": examples_text,
            "career_level": state.career_level or "자동",
            "company_news": state.company_news or "뉴스 정보 없음",
        })

        state_key = EVAL_STATE_KEYS[role_key]
        updates[state_key] = [result]

    return updates


def finalize(state: NegotiationState) -> Dict[str, Any]:
    role_weights, _ = get_role_weights(normalize=True)

    latest = {
        role: _get_latest_eval(state, role)
        for role in EVALUATOR_ROLES
    }

    weighted_score = sum(
        role_weights[role] * ev.score
        for role, ev in latest.items()
    )

    decisions = [ev.decision for ev in latest.values()]
    counter = Counter(decisions)
    most_common = counter.most_common()

    if len(most_common) == 1 or most_common[0][1] > most_common[1][1]:
        final_decision = most_common[0][0]
    else:
        tied = [decision for decision, count in most_common if count == most_common[0][1]]
        tied_scores = {}
        for role, ev in latest.items():
            if ev.decision in tied:
                tied_scores.setdefault(ev.decision, 0.0)
                tied_scores[ev.decision] += role_weights[role] * ev.score
        final_decision = max(tied_scores, key=tied_scores.get)

    reasoning_parts = [
        f"[{EVALUATOR_ROLES[role]}] {ev.decision}({ev.score}점): {ev.reasoning}"
        for role, ev in latest.items()
    ]

    return {
        "final_decision": final_decision,
        "final_score": weighted_score,
        "final_reasoning": "\n".join(reasoning_parts),
    }


def generate_interview_questions(state: NegotiationState) -> Dict[str, Any]:
    latest = {role: _get_latest_eval(state, role) for role in EVALUATOR_ROLES}

    all_strengths: list[str] = []
    all_weaknesses: list[str] = []
    for ev in latest.values():
        all_strengths.extend(ev.key_strengths)
        all_weaknesses.extend(ev.key_weaknesses)

    strengths_text = "\n".join(f"- {s}" for s in dict.fromkeys(all_strengths))
    weaknesses_text = "\n".join(f"- {w}" for w in dict.fromkeys(all_weaknesses))

    parser = PydanticOutputParser(pydantic_object=InterviewQuestions)
    prompt = PromptTemplate(
        template=INTERVIEW_QUESTION_TEMPLATE,
        input_variables=[
            "cover_letter", "job_posting", "company_news",
            "final_reasoning", "strengths", "weaknesses",
        ],
        partial_variables={"format_instruction": parser.get_format_instructions()},
    )
    chain = prompt | _get_llm() | parser
    result = chain.invoke({
        "cover_letter": state.cover_letter,
        "job_posting": state.job_posting or "모집공고 정보 없음",
        "company_news": state.company_news or "뉴스 정보 없음",
        "final_reasoning": state.final_reasoning,
        "strengths": strengths_text,
        "weaknesses": weaknesses_text,
    })
    return {"interview_questions": result.model_dump()}


def route_after_consensus(
    state: NegotiationState,
) -> Literal["finalize", "negotiate"]:
    if state.is_consensus:
        return "finalize"
    if state.current_round >= state.max_rounds:
        return "finalize"
    return "negotiate"


def build_graph(max_rounds: int = DEFAULT_MAX_ROUNDS) -> Any:
    workflow = StateGraph(NegotiationState)

    workflow.add_node("evaluate_hr", evaluate_hr)
    workflow.add_node("evaluate_dept_head", evaluate_dept_head)
    workflow.add_node("evaluate_talent_dev", evaluate_talent_dev)
    workflow.add_node("check_consensus", check_consensus)
    workflow.add_node("negotiate", negotiate)
    workflow.add_node("finalize", finalize)
    workflow.add_node("generate_interview_questions", generate_interview_questions)

    workflow.add_edge(START, "evaluate_hr")
    workflow.add_edge(START, "evaluate_dept_head")
    workflow.add_edge(START, "evaluate_talent_dev")
    workflow.add_edge("evaluate_hr", "check_consensus")
    workflow.add_edge("evaluate_dept_head", "check_consensus")
    workflow.add_edge("evaluate_talent_dev", "check_consensus")
    workflow.add_conditional_edges("check_consensus", route_after_consensus)
    workflow.add_edge("negotiate", "check_consensus")
    workflow.add_edge("finalize", "generate_interview_questions")
    workflow.add_edge("generate_interview_questions", END)

    return workflow.compile()
