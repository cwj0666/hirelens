import operator
from typing import Annotated, Literal

from pydantic import BaseModel, Field

DEFAULT_MODEL = "gpt-4.1"
DEFAULT_ADK_MODEL = "gemini-2.5-flash"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_ROUNDS = 3
RAG_APPROVED_RESULT = "합격"
SUPPORTED_FILE_ENCODINGS = ("utf-8-sig", "utf-8", "cp949", "euc-kr")
OPENAI_MODEL_OPTIONS = [
    "gpt-4.1",
    "gpt-4o",
    "gpt-4.1-mini",
    "gpt-4o-mini",
    "o3-mini",
]

EVALUATOR_ROLES = {
    "hr": "HR 담당자",
    "dept_head": "현업 부서장",
    "talent_dev": "인재개발팀",
}

DEFAULT_WEIGHTS = {
    "hr": 0.30,
    "dept_head": 0.45,
    "talent_dev": 0.25,
}

DECISION_COLORS = {
    "통과": "green",
    "보류": "orange",
    "불통과": "red",
}

EVAL_STATE_KEYS = {
    "hr": "hr_evals",
    "dept_head": "dept_head_evals",
    "talent_dev": "talent_dev_evals",
}


class InterviewQuestions(BaseModel):
    experience_questions: list[str] = Field(
        description="자소서 경험 기반 질문 2~3개 (예: 자소서에서 언급한 ~를 구체적으로 설명해주세요)",
    )
    job_fit_questions: list[str] = Field(
        description="직무 적합성 질문 2~3개 (예: 공고에서 요구하는 ~에 대한 경험은?)",
    )
    company_questions: list[str] = Field(
        description="회사 관련 질문 2~3개 (예: 최근 ~를 발표했는데, 어떻게 생각하나요?)",
    )
    weakness_questions: list[str] = Field(
        description="약점 보완 질문 2~3개 (예: 평가에서 ~가 부족하다고 나왔는데, 보완 계획은?)",
    )


class EvaluatorOutput(BaseModel):
    decision: Literal["통과", "보류", "불통과"] = Field(
        description="최종 판정: 통과, 보류, 불통과 중 하나",
    )
    score: float = Field(
        description="종합 점수 (0.0 ~ 100.0)",
    )
    reasoning: str = Field(
        description="판정 근거를 3~5문장으로 서술",
    )
    key_strengths: list[str] = Field(
        description="핵심 강점 1~3개",
    )
    key_weaknesses: list[str] = Field(
        description="핵심 약점 1~3개",
    )


class NegotiationState(BaseModel):
    cover_letter: str = Field(default="", description="입력 자기소개서")
    job_posting: str = Field(default="", description="모집공고 텍스트")
    current_round: int = Field(default=0, description="현재 협상 라운드")
    max_rounds: int = Field(default=DEFAULT_MAX_ROUNDS, description="최대 협상 라운드")
    hr_evals: Annotated[list, operator.add] = Field(
        default_factory=list,
        description="HR 담당자 라운드별 평가",
    )
    dept_head_evals: Annotated[list, operator.add] = Field(
        default_factory=list,
        description="현업 부서장 라운드별 평가",
    )
    talent_dev_evals: Annotated[list, operator.add] = Field(
        default_factory=list,
        description="인재개발팀 라운드별 평가",
    )
    is_consensus: bool = Field(default=False, description="합의 도달 여부")
    final_decision: str = Field(default="", description="최종 판정")
    final_score: float = Field(default=0.0, description="최종 가중 점수")
    final_reasoning: str = Field(default="", description="최종 판정 근거")
    career_level: str = Field(default="자동", description="경력 수준 (신입/경력/자동)")
    interview_questions: dict = Field(default_factory=dict, description="면접 예상 질문")
    company_news: str = Field(default="", description="회사 최근 뉴스 텍스트")
    reference_examples: str = Field(default="", description="검색된 합격 사례 텍스트")
    use_rag: bool = Field(default=False, description="RAG 사용 여부")
