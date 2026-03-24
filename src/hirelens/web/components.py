from html import escape

import streamlit as st
from hirelens.evaluation.models import EVAL_STATE_KEYS, EVALUATOR_ROLES, EvaluatorOutput
from hirelens.web import APP_NAME, APP_TITLE

RESULT_SECTION_OPTIONS = ("요약", "평가 기록", "수정안", "면접 질문", "출처")
DECISION_DISPLAY = {
    "통과": "합격",
    "보류": "보완",
    "불통과": "불합격",
}


def render_hero() -> None:
    st.html(
        f"""
        <div class="hero-panel">
            <div class="hero-eyebrow">{APP_NAME}</div>
            <h1 class="hero-title">{APP_TITLE}</h1>
            <div class="hero-copy">회사 맥락과 뉴스 흐름까지 반영해 자소서를 평가합니다.</div>
        </div>
        """
    )


def render_section_header(title: str, copy: str) -> None:
    st.html(
        f"""
        <div class="section-title">{title}</div>
        <div class="section-copy">{copy}</div>
        """
    )


def render_status_banner(label: str, tone: str) -> None:
    st.html(
        f'<div class="status-banner status-banner-{tone}">{escape(label)}</div>',
    )


def render_info_grid(items: list[tuple[str, str]]) -> None:
    cells = []
    for label, value in items:
        if not value:
            continue
        cells.append(
            f"""
            <div class="info-grid-item">
                <div class="info-grid-label">{escape(label)}</div>
                <div class="info-grid-value">{escape(value)}</div>
            </div>
            """,
        )
    if not cells:
        return
    st.html(f'<div class="info-grid">{"".join(cells)}</div>')


def _list_html(items: list[str], empty_text: str) -> str:
    if not items:
        return f'<div class="surface-empty">{escape(empty_text)}</div>'
    rows = "".join(f"<li>{escape(_format_display_item(item))}</li>" for item in items)
    return f'<ul class="surface-list">{rows}</ul>'


def _normalize_text_items(items: object) -> list[str]:
    if not items:
        return []
    if isinstance(items, str):
        return [items]
    normalized: list[str] = []
    if isinstance(items, list):
        for item in items:
            if isinstance(item, str):
                text = item.strip()
            elif isinstance(item, dict):
                text = " ".join(str(value).strip() for value in item.values() if value)
            else:
                text = str(item).strip()
            if text:
                normalized.append(text)
    return normalized


def _clean_text(text: object) -> str:
    if text is None:
        return ""
    return " ".join(str(text).split()).strip()


def _format_display_item(text: object) -> str:
    cleaned = _clean_text(text).rstrip(",;")
    if not cleaned:
        return ""

    replacements = [
        ("드러나지 않음", "드러나지 않습니다"),
        ("부족함", "부족합니다"),
        ("미흡함", "미흡합니다"),
        ("약함", "약합니다"),
        ("모호함", "모호합니다"),
        ("불분명함", "불분명합니다"),
        ("필요함", "필요합니다"),
        ("필요", "필요합니다"),
        ("적음", "적습니다"),
        ("낮음", "낮습니다"),
        ("보임", "보입니다"),
        ("없음", "없습니다"),
        ("않음", "않습니다"),
        ("어려움", "어렵습니다"),
    ]
    for old, new in replacements:
        if cleaned.endswith(old):
            cleaned = f"{cleaned[:-len(old)]}{new}"
            break
    return cleaned


def _strip_sentence_end(text: object) -> str:
    return _clean_text(text).rstrip(" .!?")


def _ensure_sentence(text: object) -> str:
    cleaned = _clean_text(text)
    if not cleaned:
        return ""
    if cleaned[-1] in ".!?":
        return cleaned
    return f"{cleaned}."


def _rich_paragraph_html(text: object) -> str:
    cleaned = _clean_text(text)
    if not cleaned:
        return ""
    return f'<p class="surface-copy">{escape(cleaned)}</p>'


def _rich_paragraphs_html(items: list[object]) -> str:
    return "".join(_rich_paragraph_html(text) for text in items)


def render_surface_card(title: str, body_html: str, extra_class: str = "") -> None:
    class_attr = f"surface-card {extra_class}".strip()
    st.html(
        f"""
        <div class="{class_attr}">
            <div class="surface-card-title">{escape(title)}</div>
            <div class="surface-card-body">{body_html}</div>
        </div>
        """
    )


def render_sidebar_intro(has_openai: bool, has_google: bool) -> None:
    pills = []
    if has_openai:
        pills.append('<span class="sidebar-pill sidebar-pill-ready">OpenAI 연결됨</span>')
    else:
        pills.append('<span class="sidebar-pill sidebar-pill-warn">OpenAI 키 필요</span>')
    if has_google:
        pills.append('<span class="sidebar-pill sidebar-pill-ready">Google 연결됨</span>')

    st.sidebar.html(
        f"""
        <div class="sidebar-panel">
            <div class="sidebar-pill-row">
                {''.join(pills)}
            </div>
        </div>
        """
    )


def render_sidebar_section_copy(copy: str) -> None:
    st.html(
        f'<div class="sidebar-section-copy">{copy}</div>',
    )


def render_model_note(model_name: str) -> None:
    notes = {
        "gpt-4.1": "추천: 정확도를 우선할 때 가장 무난한 선택입니다.",
        "gpt-4o": "속도와 품질 균형이 좋아 일반적인 평가에 적합합니다.",
        "gpt-4.1-mini": "비용을 줄이면서도 비교적 안정적인 응답을 기대할 수 있습니다.",
        "gpt-4o-mini": "가벼운 검토나 빠른 반복 확인에 적합합니다.",
        "o3-mini": "추론 성향이 강해 논리 검토에 유리할 수 있습니다.",
    }
    note = notes.get(model_name, "직접 지정한 모델을 사용합니다.")
    st.html(
        f'<div class="sidebar-model-note">{note}</div>',
    )


def get_decision_class(decision: str) -> str:
    if decision == "통과":
        return "decision-pass"
    if decision == "보류":
        return "decision-hold"
    return "decision-fail"


def format_decision(decision: str) -> str:
    return DECISION_DISPLAY.get(decision, decision)


def render_eval_card(role_key: str, ev: EvaluatorOutput) -> None:
    role_name = EVALUATOR_ROLES[role_key]
    decision_class = get_decision_class(ev.decision)
    display_decision = format_decision(ev.decision)
    body_html = f"""
    <div class="surface-meta-line">
        <span class="decision-chip {decision_class}">{escape(display_decision)}</span>
        <span class="score-text">{ev.score:.1f}점</span>
    </div>
    <div class="surface-copy">{escape(ev.reasoning)}</div>
    <div class="surface-split">
        <div>
            <div class="surface-subtitle">강점</div>
            {_list_html(ev.key_strengths, "강점이 없습니다.")}
        </div>
        <div>
            <div class="surface-subtitle">보완 포인트</div>
            {_list_html(ev.key_weaknesses, "보완 포인트가 없습니다.")}
        </div>
    </div>
    """
    render_surface_card(role_name, body_html)


def render_negotiation_round(state: dict, round_idx: int) -> None:
    st.markdown(f"#### 협상 라운드 {round_idx + 1}")
    cols = st.columns(3)

    for i, (role_key, role_name) in enumerate(EVALUATOR_ROLES.items()):
        evals = state[EVAL_STATE_KEYS[role_key]]
        if len(evals) <= round_idx + 1:
            continue

        prev_ev = evals[round_idx]
        curr_ev = evals[round_idx + 1]
        changed = prev_ev.decision != curr_ev.decision
        decision_class = get_decision_class(curr_ev.decision)
        current_label = format_decision(curr_ev.decision)

        with cols[i]:
            score_text = f"{prev_ev.score:.1f}점 -> {curr_ev.score:.1f}점" if changed else f"{curr_ev.score:.1f}점"
            decision_text = current_label if changed else f"{current_label} 유지"
            body_html = f"""
            <div class="surface-meta-line">
                <span class="decision-chip {decision_class}">{escape(decision_text)}</span>
                <span class="score-text">{score_text}</span>
            </div>
            <div class="surface-copy">{escape(curr_ev.reasoning)}</div>
            """
            render_surface_card(role_name, body_html)


def summarize_repeated_points(items: list[str], limit: int = 3) -> list[str]:
    counts: dict[str, int] = {}
    ordered: list[str] = []

    for item in items:
        cleaned = _format_display_item(item)
        if not cleaned:
            continue
        if cleaned not in counts:
            ordered.append(cleaned)
        counts[cleaned] = counts.get(cleaned, 0) + 1

    repeated = [item for item in ordered if counts[item] >= 2]
    selected = repeated if repeated else ordered
    return selected[:limit]


def get_latest_evaluations(result: dict) -> list[tuple[str, EvaluatorOutput]]:
    latest = []
    for role_key, role_name in EVALUATOR_ROLES.items():
        evals = result.get(EVAL_STATE_KEYS[role_key], [])
        if evals:
            latest.append((role_name, evals[-1]))
    return latest


def build_result_summary(result: dict) -> dict[str, object]:
    latest_evals = get_latest_evaluations(result)
    strengths = summarize_repeated_points([
        item
        for _, ev in latest_evals
        for item in ev.key_strengths
    ])
    weaknesses = summarize_repeated_points([
        item
        for _, ev in latest_evals
        for item in ev.key_weaknesses
    ])

    final_decision = result.get("final_decision", "")
    final_score = result.get("final_score", 0.0)
    is_consensus = result.get("is_consensus", False)
    total_rounds = result.get("current_round", 1)

    process_sentence = (
        "이번 결과는 평가자 간 합의를 거쳐 정리되었습니다."
        if is_consensus
        else f"이번 결과는 협상 {total_rounds}라운드 후 과반 판단으로 정리되었습니다."
    )
    display = format_decision(final_decision)
    base = f"최종 판정은 {display}이며, 가중 점수는 {final_score:.1f}점입니다. {process_sentence}"
    judgment_parts = [base]
    if strengths:
        judgment_parts.append(
            "여러 평가자가 공통적으로 높게 본 강점이 분명했고, 이 지점들이 지원자의 직무 적합성과 설득력을 뒷받침하는 핵심 근거로 작용했습니다.",
        )
    if weaknesses:
        judgment_parts.append(
            "반대로 추가 보완이 필요하다고 본 포인트도 분명했습니다. 이 항목들이 판정을 다소 보수적으로 만든 주요 이유였으며, 세부 내용은 아래 보완 포인트에서 확인하실 수 있습니다.",
        )
    if not strengths and not weaknesses:
        judgment_parts.append("다만 평가자 간에 반복해서 지적된 공통 포인트가 뚜렷하지 않아, 세부 의견까지 함께 확인하시는 편이 좋습니다.")

    return {
        "judgment": " ".join(judgment_parts),
        "strengths": strengths,
        "weaknesses": weaknesses,
    }


def build_revision_suggestions(result: dict) -> dict[str, list[str]]:
    all_weaknesses = []
    all_strengths = []
    for role_key in EVALUATOR_ROLES:
        evals = result.get(EVAL_STATE_KEYS[role_key], [])
        if evals:
            latest = evals[-1]
            all_weaknesses.extend(latest.key_weaknesses)
            all_strengths.extend(latest.key_strengths)

    return {
        "weaknesses": summarize_repeated_points(all_weaknesses, limit=5),
        "strengths": summarize_repeated_points(all_strengths, limit=5),
    }


def render_company_news_report(report: dict, show_header: bool = True) -> None:
    if not report:
        return

    if show_header:
        render_section_header(
            "회사 뉴스 브리프",
            "수집된 최근 뉴스를 한 번에 읽기 쉽게 요약한 내용입니다.",
        )

    summary = report.get("summary", "")
    outlook = report.get("outlook", "")
    recurring_topics = report.get("recurring_topics", [])
    key_points = report.get("key_points", [])
    watch_points = report.get("watch_points", [])
    application_tips = report.get("application_tips", [])
    source_lines = report.get("source_lines", "")
    article_count = report.get("article_count", 0)
    relevant_article_count = report.get("relevant_article_count", 0)
    used_article_count = report.get("used_article_count", 0)
    query_terms = report.get("query_terms", [])

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("수집 기사", article_count)
    with metric_col2:
        st.metric("선별 기사", relevant_article_count)
    with metric_col3:
        st.metric("브리프 반영", used_article_count)

    recurring_highlights = _normalize_text_items(recurring_topics[:2])
    render_surface_card(
        "핵심 요약",
        _rich_paragraphs_html([summary or "요약 정보가 없습니다."]),
    )

    col1, col2 = st.columns(2)
    with col1:
        render_surface_card(
            "향후 전망",
            _rich_paragraphs_html([outlook or "전망 정보가 없습니다."]),
        )
        render_surface_card("반복 이슈", _list_html(recurring_topics, "반복적으로 관찰된 이슈가 없습니다."))
        render_surface_card("핵심 이슈", _list_html(key_points, "정리된 핵심 이슈가 없습니다."))
    with col2:
        render_surface_card("체크 포인트", _list_html(watch_points, "추가 체크 포인트가 없습니다."))
        render_surface_card("반영 포인트", _list_html(application_tips, "반영 포인트가 없습니다."))

    if show_header:
        if source_lines:
            with st.expander("기사 출처 보기"):
                st.markdown(source_lines)
        if query_terms:
            with st.expander("사용한 검색어 보기"):
                for query in query_terms:
                    st.markdown(f"- {query}")


def render_company_info(company_info: dict, show_header: bool = True) -> None:
    if show_header:
        render_section_header("회사 정보", "")
    with st.container(border=True):
        market_cap = company_info.get("시가총액", 0)
        render_info_grid(
            [
                ("회사명", company_info.get("회사명", "-")),
                ("업종", company_info.get("업종", "-")),
                ("CEO", company_info.get("CEO", "-")),
                ("시장", company_info.get("시장", "-")),
                ("시가총액", f"{market_cap / 100_000_000:,.0f}억 원" if market_cap else "-"),
                ("상장일", company_info.get("상장일", "-")),
                ("홈페이지", company_info.get("홈페이지", "-")),
            ],
        )
        if company_info.get("회사소개"):
            st.html('<div class="input-card-title input-card-title-tight">소개</div>')
            st.markdown(company_info["회사소개"])


def render_first_eval(result: dict) -> None:
    render_section_header("1차 평가", "")
    cols = st.columns(3)
    for i, role_key in enumerate(EVALUATOR_ROLES):
        evals = result.get(EVAL_STATE_KEYS[role_key], [])
        if evals:
            with cols[i]:
                render_eval_card(role_key, evals[0])


def render_negotiation_section(result: dict) -> None:
    hr_eval_count = len(result.get("hr_evals", []))
    if hr_eval_count <= 1:
        return
    render_section_header("협상 과정", "")
    for round_idx in range(hr_eval_count - 1):
        render_negotiation_round(result, round_idx)
        if round_idx < hr_eval_count - 2:
            st.divider()


def render_final_verdict(result: dict) -> None:
    render_section_header("평가자별 최종 요약", "")
    for role_key, role_name in EVALUATOR_ROLES.items():
        evals = result.get(EVAL_STATE_KEYS[role_key], [])
        if not evals:
            continue
        role_summary = build_role_journey_summary(evals)
        role_html = f"""
        <div class="surface-copy">{escape(role_summary["initial"])}</div>
        <div class="surface-subtitle">조정 흐름</div>
        {_list_html(role_summary["changes"], "협상 과정에서도 기존 판단이 유지됐습니다.")}
        <div class="surface-subtitle">최종 정리</div>
        <div class="surface-copy">{escape(role_summary["final"])}</div>
        <div class="surface-split">
            <div>
                <div class="surface-subtitle">강점</div>
                {_list_html(role_summary["strengths"], "강점이 없습니다.")}
            </div>
            <div>
                <div class="surface-subtitle">보완 포인트</div>
                {_list_html(role_summary["weaknesses"], "보완 포인트가 없습니다.")}
            </div>
        </div>
        """
        render_surface_card(role_name, role_html)


def render_revision(
    result: dict,
    company_info: dict | None,
    job_posting: str,
    company_news_report: dict | None = None,
) -> None:
    render_section_header("수정안", "")

    revision = build_revision_suggestions(result)
    weakness_sentence = (
        "가장 먼저 보완하셔야 할 부분은 아래 목록에 정리된 핵심 약점들입니다. 이 항목들은 단순히 표현을 손보는 문제가 아니라, 지원자의 기여도와 직무 적합성을 판단하는 근거가 부족하게 보였던 지점들입니다. 경험의 맥락, 본인의 역할, 그리고 결과가 어떻게 이어졌는지를 더 구체적으로 보여주시는 편이 좋습니다."
        if revision["weaknesses"]
        else "현재 평가에서 반복적으로 지적된 약점은 크지 않았습니다."
    )
    strength_sentence = (
        "반대로 계속 살리셔야 할 강점도 분명합니다. 수정 과정에서는 아래 강점 항목을 약하게 만들기보다, 구체적인 사례와 결과를 덧붙여 더 또렷하게 보여주시는 편이 좋습니다."
        if revision["strengths"]
        else "공통적으로 반복된 강점은 뚜렷하지 않았습니다."
    )
    render_surface_card(
        "핵심 수정 방향",
        f'<p class="surface-copy">{escape(weakness_sentence)}</p>'
        + _list_html(revision["weaknesses"], "공통으로 반복된 약점이 없습니다.")
        + f'<p class="surface-copy">{escape(strength_sentence)}</p>'
        + _list_html(revision["strengths"], "공통으로 반복된 강점이 없습니다."),
    )

    company_name = company_info.get("회사명", "해당 회사") if company_info else "해당 회사"
    fit_paragraphs: list[str] = []
    action_points: list[str] = []

    if company_info and "error" not in company_info:
        industry = company_info.get("업종", "")
        description = company_info.get("회사소개", "")
        if industry:
            fit_paragraphs.append(
                f"{company_name}는 {industry} 업종의 회사이므로, 지원동기와 경험 서술에서도 업종 특성과 연결되는 맥락을 분명히 보여주시는 편이 좋습니다. 단순히 회사명을 언급하는 수준보다, 이 업종이 중요하게 보는 문제를 본인이 어떤 방식으로 다뤄 왔는지를 설명해야 설득력이 생깁니다.",
            )
        if description:
            fit_paragraphs.append(
                f"회사 소개 문구를 그대로 반복하기보다, {company_name}의 사업 방향과 본인의 경험이 실제로 맞닿는 지점을 문장으로 풀어 쓰시는 편이 더 설득력 있습니다. 특히 본인이 다뤘던 문제 해결 방식이나 성과가 회사의 현재 방향과 어떻게 연결되는지까지 보여주시면 좋습니다.",
            )
        action_points.extend(_normalize_text_items(company_info.get("기업코멘트")))

    if company_news_report:
        summary = company_news_report.get("summary", "")
        outlook = company_news_report.get("outlook", "")
        recurring_topics = company_news_report.get("recurring_topics", [])
        if summary:
            fit_paragraphs.append(_ensure_sentence(summary))
            fit_paragraphs.append(
                "지원동기나 직무 이해 문단에서도 이 흐름을 알고 있다는 점이 자연스럽게 드러나야 합니다. 회사 이름을 언급하는 수준을 넘어서, 지금 회사가 중요하게 보는 방향과 본인의 경험을 어떻게 연결할 수 있는지까지 보여주시는 편이 좋습니다.",
            )
        if outlook:
            fit_paragraphs.append(_ensure_sentence(outlook))
            fit_paragraphs.append(
                "이 변화가 실제 채용 니즈와 직무 기대치로 어떻게 이어질지를 함께 읽어 두시는 편이 좋습니다. 자기소개서에서도 이 흐름 안에서 본인이 어떤 문제를 해결할 수 있고, 어떤 방식으로 기여할 수 있는지를 더 구체적으로 보여주시면 설득력이 높아집니다.",
            )
        action_points.extend(_normalize_text_items(recurring_topics[:2]))
        action_points.extend(_normalize_text_items(company_news_report.get("application_tips", [])))

    if job_posting:
        fit_paragraphs.append(
            "모집공고에 적힌 필수 요건, 우대사항, 핵심 역량은 별도 문단으로 흩어 쓰기보다 경험 사례 속에 직접 연결해 녹여 넣는 편이 좋습니다. 즉, 역량 이름을 나열하기보다 어떤 상황에서 그 역량을 발휘했고 어떤 결과를 냈는지까지 이어지게 쓰는 방식이 더 효과적입니다.",
        )
        action_points.extend(
            [
                "필수 자격요건이 빠지지 않았는지 다시 확인하기",
                "우대사항에 해당하는 경험은 수치와 결과까지 포함해 쓰기",
                "공고의 핵심 역량 표현을 자소서 문장에 직접 반영하기",
            ],
        )

    render_surface_card(
        "회사 맞춤 반영",
        _rich_paragraphs_html(fit_paragraphs) + _list_html(action_points[:6], "추가 반영 포인트가 없습니다."),
    )


def render_interview_questions(result: dict) -> None:
    questions = result.get("interview_questions", {})
    if not questions:
        return
    render_section_header("면접 질문", "")
    categories = [
        ("experience_questions", "경험 기반"),
        ("job_fit_questions", "직무 적합성"),
        ("company_questions", "회사 관련"),
        ("weakness_questions", "약점 보완"),
    ]
    col1, col2 = st.columns(2)
    cols = [col1, col2]
    for i, (key, label) in enumerate(categories):
        with cols[i % 2]:
            render_surface_card(label, _list_html(questions.get(key, []), "질문이 생성되지 않았습니다."))


def _build_verdict_narrative(
    display_decision: str,
    final_score: float,
    is_consensus: bool,
    total_rounds: int,
    strengths: list[str],
    weaknesses: list[str],
) -> str:
    process_clause = (
        "평가자 전원이 합의한 결과로"
        if is_consensus
        else f"협상 {total_rounds}라운드를 거쳐 과반수 판단으로"
    )
    opening = f"최종 판정은 {display_decision}이며, 가중 점수는 {final_score:.1f}점입니다. {process_clause} 도출됐습니다."

    n_str = len(strengths)
    n_weak = len(weaknesses)
    if strengths and weaknesses:
        return (
            f"{opening} 평가자들이 공통으로 인정한 강점 {n_str}가지가 직무 적합성을 뒷받침했으나, "
            f"보완이 필요한 포인트 {n_weak}가지도 함께 지적됐습니다. 세부 내용은 아래를 확인하세요."
        )
    if strengths:
        return f"{opening} 공통으로 인정된 강점 {n_str}가지가 높은 평가를 이끈 핵심 근거입니다."
    if weaknesses:
        return f"{opening} 다만 추가 보완이 필요한 포인트 {n_weak}가지가 확인됐습니다. 세부 내용은 아래를 확인하세요."
    return f"{opening} 평가자 간에 반복해서 지적된 공통 포인트가 뚜렷하지 않아, 세부 의견까지 함께 확인하시는 편이 좋습니다."


def render_result_overview(result: dict) -> None:
    summary = build_result_summary(result)
    final_decision = result.get("final_decision", "")
    final_score = result.get("final_score", 0.0)
    is_consensus = result.get("is_consensus", False)
    total_rounds = result.get("current_round", 1)
    display_decision = format_decision(final_decision)

    render_section_header("요약", "")
    st.html(
        f"""
        <div class="result-summary-grid">
            <div class="result-summary-card">
                <div class="result-summary-label">판정</div>
                <div class="result-summary-value">{escape(display_decision or '결과 없음')}</div>
            </div>
            <div class="result-summary-card">
                <div class="result-summary-label">점수</div>
                <div class="result-summary-value">{final_score:.1f}점</div>
            </div>
            <div class="result-summary-card">
                <div class="result-summary-label">결정</div>
                <div class="result-summary-value">{"합의" if is_consensus else "과반수"}</div>
            </div>
        </div>
        """
    )

    narrative = _build_verdict_narrative(
        display_decision, final_score, is_consensus, total_rounds,
        summary["strengths"], summary["weaknesses"],
    )
    overview_html = (
        f'<p class="surface-copy">{escape(narrative)}</p>'
        f'<div class="surface-split">'
        f'<div><div class="surface-subtitle">공통 강점</div>'
        f'{_list_html(summary["strengths"], "공통으로 반복된 강점은 없었습니다.")}'
        f'</div><div><div class="surface-subtitle">보완 포인트</div>'
        f'{_list_html(summary["weaknesses"], "공통으로 반복된 보완 포인트는 없었습니다.")}'
        f'</div></div>'
    )
    render_surface_card("종합 요약", overview_html)


def render_company_insights(company_info: dict | None, company_news_report: dict | None) -> None:
    if not company_info and not company_news_report:
        return

    render_section_header("회사 인사이트", "")
    overview_paragraphs: list[str] = []
    detail_points: list[str] = []

    if company_info:
        company_name = company_info.get("회사명", "")
        market = company_info.get("시장", "")
        industry = company_info.get("업종", "")
        ceo = company_info.get("CEO", "")
        market_cap = company_info.get("시가총액", 0)
        market_cap_text = f"{market_cap / 100_000_000:,.0f}억 원" if market_cap else ""

        overview_bits = [bit for bit in [market, industry] if bit]
        if overview_bits:
            overview_paragraphs.append(f"{company_name or '지원 회사'}는 {' · '.join(overview_bits)} 분야의 기업입니다.")
        else:
            overview_paragraphs.append(f"{company_name or '지원 회사'}에 대한 기본 정보입니다.")

        extra_bits = []
        if ceo:
            extra_bits.append(f"대표는 {ceo}입니다")
        if market_cap_text:
            extra_bits.append(f"시가총액은 {market_cap_text} 수준입니다")
        if extra_bits:
            overview_paragraphs.append(" ".join(extra_bits))

        if company_info.get("회사소개"):
            overview_paragraphs.append(_ensure_sentence(company_info["회사소개"]))

        detail_points.extend(_normalize_text_items(company_info.get("기업코멘트")))
        detail_points.extend(_normalize_text_items(company_info.get("전망")))

    if company_news_report:
        summary = company_news_report.get("summary", "")
        outlook = company_news_report.get("outlook", "")
        recurring_topics = company_news_report.get("recurring_topics", [])
        key_points = company_news_report.get("key_points", [])
        watch_points = company_news_report.get("watch_points", [])

        if summary:
            overview_paragraphs.append(_ensure_sentence(summary))
            overview_paragraphs.append(
                "최근 기사 흐름을 함께 보면, 회사가 지금 어디에 힘을 싣고 있는지와 조직이 어떤 방향으로 움직이는지를 비교적 분명하게 읽을 수 있습니다.",
            )
        if outlook:
            overview_paragraphs.append(_ensure_sentence(outlook))
            overview_paragraphs.append(
                "지원자 입장에서는 이 변화가 실제 채용 니즈나 직무 기대치와 어떻게 연결될지를 함께 읽어 두시는 편이 좋습니다. 자기소개서에서도 이 흐름에 맞는 문제 해결 관점이나 기여 방식을 보여주시면 훨씬 자연스럽습니다.",
            )

        detail_points.extend(_normalize_text_items(recurring_topics[:3]))
        detail_points.extend(_normalize_text_items(key_points[:2]))
        detail_points.extend(_normalize_text_items(watch_points[:2]))

    overview_html = _rich_paragraphs_html(overview_paragraphs)
    render_surface_card(
        "한눈에 보기",
        overview_html + _list_html(detail_points[:6], "추가로 정리할 인사이트가 없습니다."),
    )


def _build_source_card_html(item: dict) -> str:
    title = escape(item.get("title", "기사"))
    source = escape(item.get("source", ""))
    date = escape(item.get("date", ""))
    topic = escape(item.get("topic", ""))
    relevance = escape(item.get("relevance", ""))
    description = escape(item.get("description", ""))
    url = item.get("url", "")
    meta = " · ".join(part for part in [source, date, topic, relevance] if part)
    link_html = ""
    if url:
        safe_url = escape(url, quote=True)
        link_html = f'<a class="news-source-link" href="{safe_url}" target="_blank" rel="noopener noreferrer">기사 열기</a>'

    return f"""
    <div class="news-source-card">
        <div class="news-source-title">{title}</div>
        <div class="news-source-meta">{meta}</div>
        <div class="news-source-copy">{description}</div>
        {link_html}
    </div>
    """


def render_result_sources(result: dict) -> None:
    render_section_header("출처", "")

    company_news_report = result.get("_company_news_report", {}) or {}
    used_articles = company_news_report.get("used_articles") or company_news_report.get("articles") or []
    query_terms = company_news_report.get("query_terms") or []
    reference_text = result.get("_reference_text", "")

    if used_articles:
        for item in used_articles:
            st.html(_build_source_card_html(item))
    else:
        with st.container(border=True):
            st.caption("저장된 뉴스 출처가 없습니다.")

    if query_terms:
        with st.expander("검색어", expanded=False):
            for query in query_terms:
                st.markdown(f"- {query}")

    if reference_text:
        render_surface_card("참고한 합격 사례", f'<div class="surface-copy">{escape(reference_text)}</div>')


def render_results(result: dict, active_section: str = RESULT_SECTION_OPTIONS[0]) -> None:
    company_info = result.get("_company_info")
    job_posting = result.get("_job_posting", "")
    if company_info and "error" in company_info:
        company_info = None
    company_news_report = result.get("_company_news_report", {})

    if active_section == "요약":
        render_result_overview(result)
        render_company_insights(company_info, company_news_report)
        return
    if active_section == "평가 기록":
        render_first_eval(result)
        if len(result.get("hr_evals", [])) > 1:
            st.divider()
            render_negotiation_section(result)
        st.divider()
        render_final_verdict(result)
        return
    if active_section == "수정안":
        render_revision(result, company_info, job_posting, company_news_report)
        return
    if active_section == "면접 질문":
        render_interview_questions(result)
        return
    render_result_sources(result)


def build_role_journey_summary(evals: list[EvaluatorOutput]) -> dict[str, object]:
    if not evals:
        return {
            "initial": "",
            "changes": [],
            "final": "",
            "strengths": [],
            "weaknesses": [],
        }

    first_ev = evals[0]
    last_ev = evals[-1]
    changes = []

    for round_idx in range(1, len(evals)):
        prev_ev = evals[round_idx - 1]
        curr_ev = evals[round_idx]
        if prev_ev.decision == curr_ev.decision and round(prev_ev.score, 1) == round(curr_ev.score, 1):
            continue
        changes.append(
            f"{round_idx + 1}차에서 판정은 {format_decision(prev_ev.decision)}에서 {format_decision(curr_ev.decision)}로, "
            f"점수는 {prev_ev.score:.1f}점에서 {curr_ev.score:.1f}점으로 조정됐습니다.",
        )

    repeated_strengths = summarize_repeated_points(
        [item for ev in evals for item in ev.key_strengths],
    )
    repeated_weaknesses = summarize_repeated_points(
        [item for ev in evals for item in ev.key_weaknesses],
    )

    return {
        "initial": f"1차 평가는 {format_decision(first_ev.decision)}({first_ev.score:.1f}점)였습니다.",
        "changes": changes,
        "final": f"최종 평가는 {format_decision(last_ev.decision)}({last_ev.score:.1f}점)였습니다. {_ensure_sentence(last_ev.reasoning)}",
        "strengths": repeated_strengths or first_ev.key_strengths,
        "weaknesses": repeated_weaknesses or first_ev.key_weaknesses,
    }
