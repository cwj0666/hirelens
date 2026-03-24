import re
from collections.abc import MutableMapping

from hirelens.evaluation.models import EVAL_STATE_KEYS, EVALUATOR_ROLES
from hirelens.evaluation.storage import (
    list_sessions,
    load_session,
    to_serializable_result,
)

SESSION_ID_PATTERN = re.compile(r"\b(?:HL|EV)-\d{8}-[A-Z0-9]{4}\b", re.IGNORECASE)


def _get_latest_evaluations(session_data: dict) -> list[tuple[str, dict]]:
    latest = []
    for role_key, role_name in EVALUATOR_ROLES.items():
        evals = session_data.get(EVAL_STATE_KEYS[role_key], [])
        if evals:
            latest.append((role_name, evals[-1]))
    return latest


def _format_session_summary(session_id: str, session_data: dict) -> str:
    company_info = session_data.get("_company_info") or {}
    company_name = company_info.get("회사명") or "미지정"
    final_decision = session_data.get("final_decision", "미확인")
    final_score = float(session_data.get("final_score", 0.0))
    career_level = session_data.get("career_level", "자동")

    evaluator_lines = []
    for role_name, evaluation in _get_latest_evaluations(session_data):
        evaluator_lines.append(
            f"- {role_name}: {evaluation.get('decision', '')} ({float(evaluation.get('score', 0.0)):.1f}점)",
        )

    summary_lines = [
        f"세션 ID: {session_id}",
        f"회사명: {company_name}",
        f"최종 판정: {final_decision}",
        f"최종 점수: {final_score:.1f}",
        f"경력 수준: {career_level}",
    ]
    if evaluator_lines:
        summary_lines.append("평가자별 최종 의견:")
        summary_lines.extend(evaluator_lines)

    return "\n".join(summary_lines)


def extract_session_id(text: str) -> str | None:
    match = SESSION_ID_PATTERN.search(text or "")
    return match.group(0).upper() if match else None


def load_session_into_state(
    session_id: str,
    state: MutableMapping,
) -> tuple[bool, str]:
    """세션을 읽어 state에 주입하고 성공 여부와 메시지를 반환한다."""
    normalized_id = extract_session_id(session_id) or session_id.strip().upper()
    session_data = load_session(normalized_id)
    if session_data is None:
        return False, (
            f"세션 ID '{normalized_id}'를 찾지 못했습니다.\n"
            "list_recent_sessions로 최근 세션을 먼저 확인하세요."
        )

    serializable_data = to_serializable_result(session_data)
    serializable_data["_session_id"] = normalized_id
    state["session_id"] = normalized_id
    state["session_data"] = serializable_data

    return True, _format_session_summary(normalized_id, serializable_data)


def load_evaluation_session(session_id: str, tool_context) -> str:
    """
    저장된 평가 세션을 불러와 ADK state에 저장한다.
    이후 코칭 대화와 수정본 재평가 비교의 기준 세션으로 사용한다.
    """
    _, message = load_session_into_state(session_id, tool_context.state)
    return message


def list_recent_sessions(limit: int = 10) -> str:
    """최근 저장된 평가 세션 목록을 반환한다."""
    rows = list_sessions(limit=limit)
    if not rows:
        return "저장된 평가 세션이 없습니다."

    lines = []
    for row in rows:
        company_name = row.get("company_name") or "미지정"
        final_decision = row.get("final_decision") or "미확인"
        final_score = float(row.get("final_score") or 0.0)
        created_at = row.get("created_at") or ""
        lines.append(
            f"- {row['session_id']} | {company_name} | {final_decision} | {final_score:.1f}점 | {created_at}",
        )
    return "\n".join(lines)
