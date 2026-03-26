from datetime import datetime
from html import escape

from hirelens.evaluation.models import EVAL_STATE_KEYS, EVALUATOR_ROLES
from hirelens.web import APP_NAME, APP_TITLE
from hirelens.web.components import (
    _ensure_sentence,
    _normalize_text_items,
    _rich_paragraphs_html,
    build_result_summary,
    build_revision_suggestions,
    build_role_journey_summary,
    format_decision,
)


DECISION_CLASS_MAP = {
    "통과": "decision-pass",
    "보류": "decision-hold",
    "불통과": "decision-fail",
}

ARCHIVE_CSS = """
    @import url('https://cdn.jsdelivr.net/gh/sun-typeface/SUIT/fonts/variable/woff2/SUIT-Variable.css');
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/variable/pretendardvariable-dynamic-subset.css');

    :root {
        --font-body: "SUIT Variable", "Pretendard Variable", -apple-system,
            BlinkMacSystemFont, "Segoe UI", sans-serif;
        --color-text: #0f172a;
        --color-text-sub: #475569;
        --color-text-muted: #64748b;
        --color-bg: #f8fafc;
        --color-border: rgba(148, 163, 184, 0.16);
        --color-border-strong: rgba(148, 163, 184, 0.22);
        --radius-card: 22px;
        --radius-subcard: 16px;
        --radius-pill: 999px;
        --shadow-card: 0 10px 24px rgba(15, 23, 42, 0.05);
    }

    * { box-sizing: border-box; }

    body {
        margin: 0;
        padding: 2.4rem;
        font-family: var(--font-body);
        color: var(--color-text);
        line-height: 1.65;
        background:
            radial-gradient(circle at top left, rgba(224, 242, 254, 0.9), transparent 28%),
            radial-gradient(circle at top right, rgba(254, 240, 138, 0.45), transparent 24%),
            linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
        min-height: 100vh;
    }

    h1, h2, h3, h4, p { margin-top: 0; }

    .container {
        max-width: 1180px;
        margin: 0 auto;
    }

    /* ── Hero ─────────────────────────────────────────────────── */
    .hero-panel {
        padding: 2rem 2.1rem;
        border-radius: 24px;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 55%, #334155 100%);
        color: #f8fafc;
        border: 1px solid var(--color-border-strong);
        box-shadow: 0 20px 50px rgba(15, 23, 42, 0.16);
        margin-bottom: 1.35rem;
    }
    .hero-eyebrow {
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #93c5fd;
        margin-bottom: 0.6rem;
        font-weight: 700;
    }
    .hero-title {
        font-family: var(--font-body);
        font-size: 2.15rem;
        font-weight: 850;
        letter-spacing: -0.02em;
        margin: 0;
        color: #ffffff;
    }
    .hero-copy {
        margin-top: 0.65rem;
        font-size: 1rem;
        line-height: 1.65;
        color: #dbeafe;
    }
    .hero-meta {
        display: flex;
        gap: 0.55rem;
        flex-wrap: wrap;
        margin-top: 1rem;
    }
    .hero-pill {
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: var(--radius-pill);
        padding: 0.35rem 0.7rem;
        font-size: 0.88rem;
        font-weight: 700;
    }

    /* ── Section header ───────────────────────────────────────── */
    .section-title {
        font-family: var(--font-body);
        font-size: 1.26rem;
        font-weight: 850;
        letter-spacing: -0.015em;
        color: var(--color-text);
        margin-top: 0.4rem;
        margin-bottom: 0.55rem;
    }

    /* ── Result summary grid (3-col metrics) ──────────────────── */
    .result-summary-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.9rem;
        margin-bottom: 1rem;
    }
    .result-summary-card {
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-subcard);
        padding: 0.95rem 1rem;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
    }
    .result-summary-label {
        color: var(--color-text-sub);
        font-size: 0.9rem;
        font-weight: 780;
        letter-spacing: -0.01em;
        margin-bottom: 0.32rem;
    }
    .result-summary-value {
        color: var(--color-text);
        font-family: var(--font-body);
        font-size: 1.08rem;
        font-weight: 820;
        letter-spacing: -0.01em;
    }

    /* ── Surface card ─────────────────────────────────────────── */
    .surface-card {
        background: rgba(255, 255, 255, 0.86);
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: var(--radius-subcard);
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
        padding: 1rem 1.05rem;
        margin-bottom: 0.9rem;
    }
    .surface-card-title {
        font-family: var(--font-body);
        color: var(--color-text);
        font-size: 1.06rem;
        font-weight: 820;
        letter-spacing: -0.01em;
        margin-bottom: 0.55rem;
    }
    .surface-card-title:empty { display: none; }
    .surface-card-body > *:first-child { margin-top: 0; }
    .surface-card-body > *:last-child { margin-bottom: 0; }

    .surface-copy {
        color: #334155;
        font-size: 0.95rem;
        line-height: 1.78;
        margin-bottom: 0.75rem;
    }
    .surface-subtitle {
        color: var(--color-text-sub);
        font-size: 0.8rem;
        font-weight: 800;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 0.45rem;
        margin-top: 0.65rem;
    }
    .surface-subtitle:first-child { margin-top: 0; }
    .surface-list {
        margin: 0;
        padding-left: 1rem;
        color: var(--color-text);
    }
    .surface-list li {
        margin-bottom: 0.35rem;
        line-height: 1.62;
        font-size: 0.93rem;
    }
    .surface-empty {
        color: var(--color-text-muted);
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .surface-split {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.9rem;
        margin-top: 0.55rem;
    }
    .surface-meta-line {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        flex-wrap: wrap;
        margin-bottom: 0.65rem;
    }

    /* ── Decision chips ───────────────────────────────────────── */
    .decision-chip {
        display: inline-block;
        border-radius: var(--radius-pill);
        padding: 0.24rem 0.7rem;
        font-size: 0.82rem;
        font-weight: 800;
        margin-right: 0.45rem;
    }
    .decision-pass  { background: #dcfce7; color: #166534; }
    .decision-hold  { background: #ffedd5; color: #9a3412; }
    .decision-fail  { background: #fee2e2; color: #991b1b; }

    .score-text {
        color: #334155;
        font-weight: 700;
    }

    /* ── Grid ─────────────────────────────────────────────────── */
    .grid-2 {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.9rem;
    }
    .grid-3 {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.9rem;
    }

    /* ── News source card (뉴스 아카이브 전용) ────────────────── */
    .news-source-card {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: var(--radius-subcard);
        padding: 1rem 1.05rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
        overflow-wrap: anywhere;
        word-break: break-word;
    }
    .news-source-title {
        color: var(--color-text);
        font-family: var(--font-body);
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 0.35rem;
        line-height: 1.5;
    }
    .news-source-meta {
        color: var(--color-text-muted);
        font-size: 0.88rem;
        margin-bottom: 0.55rem;
    }
    .news-source-copy {
        color: #334155;
        line-height: 1.6;
        margin-bottom: 0.7rem;
    }
    .news-source-link {
        display: inline-flex;
        align-items: center;
        padding: 0.42rem 0.75rem;
        border-radius: var(--radius-pill);
        background: #e0f2fe;
        color: #075985 !important;
        font-weight: 800;
        text-decoration: none;
    }

    /* ── Pre / code ───────────────────────────────────────────── */
    pre {
        white-space: pre-wrap;
        word-break: break-word;
        background: var(--color-bg);
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: var(--radius-subcard);
        padding: 1rem;
        overflow-x: auto;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.9rem;
    }

    /* ── Divider ──────────────────────────────────────────────── */
    .divider {
        border: none;
        border-top: 1px solid rgba(148, 163, 184, 0.18);
        margin: 1.2rem 0;
    }

    /* ── Responsive ───────────────────────────────────────────── */
    @media (max-width: 900px) {
        body { padding: 1.2rem; }
        .hero-title { font-size: 1.6rem; }
        .result-summary-grid,
        .surface-split,
        .grid-2,
        .grid-3 { grid-template-columns: 1fr; }
    }
"""


def _list_html(items: list[str], empty_text: str) -> str:
    if not items:
        return f'<div class="surface-empty">{escape(empty_text)}</div>'
    rows = "".join(f"<li>{escape(item)}</li>" for item in items)
    return f'<ul class="surface-list">{rows}</ul>'


def _surface_card(title: str, body_html: str) -> str:
    title_html = f'<div class="surface-card-title">{escape(title)}</div>' if title else ""
    return f"""
    <div class="surface-card">
        {title_html}
        <div class="surface-card-body">{body_html}</div>
    </div>
    """


def _decision_chip_html(decision: str) -> str:
    css_class = DECISION_CLASS_MAP.get(decision, "decision-fail")
    display = format_decision(decision)
    return f'<span class="decision-chip {css_class}">{escape(display)}</span>'


def _build_eval_card_html(role_key: str, ev) -> str:
    role_name = EVALUATOR_ROLES[role_key]
    strengths_html = _list_html(ev.key_strengths, "강점이 없습니다.")
    weaknesses_html = _list_html(ev.key_weaknesses, "보완 포인트가 없습니다.")
    body = f"""
    <div class="surface-meta-line">
        {_decision_chip_html(ev.decision)}
        <span class="score-text">{ev.score:.1f}점</span>
    </div>
    <div class="surface-copy">{escape(ev.reasoning)}</div>
    <div class="surface-split">
        <div>
            <div class="surface-subtitle">강점</div>
            {strengths_html}
        </div>
        <div>
            <div class="surface-subtitle">보완 포인트</div>
            {weaknesses_html}
        </div>
    </div>
    """
    return _surface_card(role_name, body)


def _section_divider(title: str) -> str:
    return f'<hr class="divider"><div class="section-title">{escape(title)}</div>'


def build_result_archive_html(
    result: dict,
    company_info: dict | None = None,
    job_posting: str = "",
    company_news_report: dict | None = None,
) -> str:
    exported_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_decision = result.get("final_decision", "")
    final_score = result.get("final_score", 0.0)
    is_consensus = result.get("is_consensus", False)
    total_rounds = result.get("current_round", 1)
    cover_letter = escape(result.get("_cover_letter", ""))
    reference_text = escape(result.get("_reference_text", ""))
    news_report = result.get("_company_news_report", {}) or {}
    summary = build_result_summary(result)
    revision = build_revision_suggestions(result)
    display_decision = format_decision(final_decision)

    # ── Summary metrics ──────────────────────────────────────
    summary_grid = f"""
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

    # ── Verdict narrative ────────────────────────────────────
    process_clause = (
        "평가자 전원이 합의한 결과로"
        if is_consensus
        else f"협상 {total_rounds}라운드를 거쳐 과반수 판단으로"
    )
    narrative = (
        f"최종 판정은 {display_decision}이며, "
        f"가중 점수는 {final_score:.1f}점입니다. "
        f"{process_clause} 도출됐습니다."
    )
    verdict_body = (
        f'<p class="surface-copy">{escape(narrative)}</p>'
        f'<div class="surface-split">'
        f'<div><div class="surface-subtitle">공통 강점</div>'
        f'{_list_html(summary["strengths"], "공통으로 반복된 강점은 없었습니다.")}'
        f'</div><div><div class="surface-subtitle">보완 포인트</div>'
        f'{_list_html(summary["weaknesses"], "공통으로 반복된 보완 포인트는 없었습니다.")}'
        f'</div></div>'
    )
    verdict_section = _surface_card("종합 요약", verdict_body)

    # ── 1차 평가 ─────────────────────────────────────────────
    eval_cards = []
    for role_key in EVALUATOR_ROLES:
        evals = result.get(EVAL_STATE_KEYS[role_key], [])
        if evals:
            eval_cards.append(_build_eval_card_html(role_key, evals[0]))

    first_eval_html = (
        _section_divider("1차 평가")
        + f'<div class="grid-3">{"".join(eval_cards)}</div>'
    )

    # ── 협상 라운드 ──────────────────────────────────────────
    round_sections = []
    hr_eval_count = len(result.get("hr_evals", []))
    if hr_eval_count > 1:
        for round_idx in range(hr_eval_count - 1):
            round_cards = []
            for role_key, role_name in EVALUATOR_ROLES.items():
                evals = result.get(EVAL_STATE_KEYS[role_key], [])
                if len(evals) <= round_idx + 1:
                    continue
                prev_ev = evals[round_idx]
                curr_ev = evals[round_idx + 1]
                changed = prev_ev.decision != curr_ev.decision
                current_label = format_decision(curr_ev.decision)
                score_text = (
                    f"{prev_ev.score:.1f}점 -> {curr_ev.score:.1f}점"
                    if changed
                    else f"{curr_ev.score:.1f}점"
                )
                decision_text = current_label if changed else f"{current_label} 유지"
                css_class = DECISION_CLASS_MAP.get(curr_ev.decision, "decision-fail")
                body = f"""
                <div class="surface-meta-line">
                    <span class="decision-chip {css_class}">{escape(decision_text)}</span>
                    <span class="score-text">{score_text}</span>
                </div>
                <div class="surface-copy">{escape(curr_ev.reasoning)}</div>
                """
                round_cards.append(_surface_card(role_name, body))
            round_sections.append(
                _section_divider(f"협상 라운드 {round_idx + 1}")
                + f'<div class="grid-3">{"".join(round_cards)}</div>',
            )

    negotiation_html = "".join(round_sections)

    # ── 평가자별 최종 요약 ───────────────────────────────────
    journey_cards = []
    for role_key, role_name in EVALUATOR_ROLES.items():
        evals = result.get(EVAL_STATE_KEYS[role_key], [])
        if not evals:
            continue
        role_summary = build_role_journey_summary(evals)
        body = f"""
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
        journey_cards.append(_surface_card(role_name, body))

    journey_html = ""
    if journey_cards:
        journey_html = _section_divider("평가자별 최종 요약") + "".join(journey_cards)

    # ── 수정안 ───────────────────────────────────────────────
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
    revision_body = (
        f'<p class="surface-copy">{escape(weakness_sentence)}</p>'
        + _list_html(revision["weaknesses"], "공통으로 반복된 약점이 없습니다.")
        + f'<p class="surface-copy">{escape(strength_sentence)}</p>'
        + _list_html(revision["strengths"], "공통으로 반복된 강점이 없습니다.")
    )
    revision_card = _surface_card("핵심 수정 방향", revision_body)

    # ── 회사 맞춤 반영 ────────────────────────────────────────
    _ci = company_info if company_info is not None else result.get("_company_info")
    _jp = job_posting or result.get("_job_posting", "")
    _cnr = company_news_report if company_news_report is not None else news_report

    company_name = _ci.get("회사명", "해당 회사") if _ci else "해당 회사"
    fit_paragraphs: list[str] = []
    action_points: list[str] = []

    if _ci and "error" not in _ci:
        industry = _ci.get("업종", "")
        description = _ci.get("회사소개", "")
        if industry:
            fit_paragraphs.append(
                f"{company_name}는 {industry} 업종의 회사이므로, 지원동기와 경험 서술에서도 업종 특성과 연결되는 맥락을 분명히 보여주시는 편이 좋습니다. 단순히 회사명을 언급하는 수준보다, 이 업종이 중요하게 보는 문제를 본인이 어떤 방식으로 다뤄 왔는지를 설명해야 설득력이 생깁니다.",
            )
        if description:
            fit_paragraphs.append(
                f"회사 소개 문구를 그대로 반복하기보다, {company_name}의 사업 방향과 본인의 경험이 실제로 맞닿는 지점을 문장으로 풀어 쓰시는 편이 더 설득력 있습니다. 특히 본인이 다뤘던 문제 해결 방식이나 성과가 회사의 현재 방향과 어떻게 연결되는지까지 보여주시면 좋습니다.",
            )
        action_points.extend(_normalize_text_items(_ci.get("기업코멘트")))

    if _cnr:
        cnr_summary = _cnr.get("summary", "")
        cnr_outlook = _cnr.get("outlook", "")
        cnr_recurring = _cnr.get("recurring_topics", [])
        if cnr_summary:
            fit_paragraphs.append(_ensure_sentence(cnr_summary))
            fit_paragraphs.append(
                "지원동기나 직무 이해 문단에서도 이 흐름을 알고 있다는 점이 자연스럽게 드러나야 합니다. 회사 이름을 언급하는 수준을 넘어서, 지금 회사가 중요하게 보는 방향과 본인의 경험을 어떻게 연결할 수 있는지까지 보여주시는 편이 좋습니다.",
            )
        if cnr_outlook:
            fit_paragraphs.append(_ensure_sentence(cnr_outlook))
            fit_paragraphs.append(
                "이 변화가 실제 채용 니즈와 직무 기대치로 어떻게 이어질지를 함께 읽어 두시는 편이 좋습니다. 자기소개서에서도 이 흐름 안에서 본인이 어떤 문제를 해결할 수 있고, 어떤 방식으로 기여할 수 있는지를 더 구체적으로 보여주시면 설득력이 높아집니다.",
            )
        action_points.extend(_normalize_text_items(cnr_recurring[:2]))
        action_points.extend(_normalize_text_items(_cnr.get("application_tips", [])))

    if _jp:
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

    company_fit_card = _surface_card(
        "회사 맞춤 반영",
        _rich_paragraphs_html(fit_paragraphs) + _list_html(action_points[:6], "추가 반영 포인트가 없습니다."),
    )

    revision_html = _section_divider("수정안") + revision_card + company_fit_card

    # ── 면접 질문 ────────────────────────────────────────────
    interview_questions = result.get("interview_questions", {})
    interview_html = ""
    if interview_questions:
        categories = [
            ("experience_questions", "경험 기반"),
            ("job_fit_questions", "직무 적합성"),
            ("company_questions", "회사 관련"),
            ("weakness_questions", "약점 보완"),
        ]
        category_cards = []
        for key, label in categories:
            items = interview_questions.get(key, [])
            items_html = _list_html(items, "생성된 질문 없음")
            category_cards.append(_surface_card(label, items_html))
        interview_html = (
            _section_divider("예상 면접 질문")
            + f'<div class="grid-2">{"".join(category_cards)}</div>'
        )

    # ── 참고 사례 ────────────────────────────────────────────
    reference_html = ""
    if reference_text:
        reference_html = _section_divider("참고 사례") + _surface_card("", f'<pre>{reference_text}</pre>')

    # ── 원본 자소서 ──────────────────────────────────────────
    cover_letter_html = ""
    if cover_letter:
        cover_letter_html = _section_divider("원본 자기소개서") + _surface_card("", f'<pre>{cover_letter}</pre>')

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{APP_NAME} 결과 아카이브</title>
  <style>{ARCHIVE_CSS}</style>
</head>
<body>
  <div class="container">
    <div class="hero-panel">
      <div class="hero-eyebrow">{APP_NAME}</div>
      <h1 class="hero-title">{APP_TITLE}</h1>
      <div class="hero-copy">회사 맥락과 뉴스 흐름까지 반영해 자소서를 평가합니다.</div>
      <div class="hero-meta">
        <span class="hero-pill">내보낸 시각: {exported_at}</span>
        <span class="hero-pill">최종 판정: {escape(display_decision)}</span>
        <span class="hero-pill">가중 점수: {final_score:.1f}</span>
        <span class="hero-pill">결정 방식: {"합의" if is_consensus else "과반수"}</span>
      </div>
    </div>

    <div class="section-title">요약</div>
    {summary_grid}
    {verdict_section}
    {first_eval_html}
    {negotiation_html}
    {journey_html}
    {revision_html}
    {interview_html}
    {reference_html}
    {cover_letter_html}
  </div>
</body>
</html>"""


def make_archive_filename() -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"cover-letter-review-{timestamp}.html"


def build_news_archive_html(report: dict) -> str:
    exported_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    company_name = escape(report.get("company_name", "회사"))
    article_count = int(report.get("article_count", 0))
    relevant_count = int(report.get("relevant_article_count", 0))
    used_count = int(report.get("used_article_count", 0))

    metrics_html = f"""
    <div class="result-summary-grid">
        <div class="result-summary-card">
            <div class="result-summary-label">수집 기사</div>
            <div class="result-summary-value">{article_count}건</div>
        </div>
        <div class="result-summary-card">
            <div class="result-summary-label">선별 기사</div>
            <div class="result-summary-value">{relevant_count}건</div>
        </div>
        <div class="result-summary-card">
            <div class="result-summary-label">브리프 반영</div>
            <div class="result-summary-value">{used_count}건</div>
        </div>
    </div>
    """

    summary_card = _surface_card(
        "핵심 요약",
        f'<p class="surface-copy">{escape(report.get("summary", ""))}</p>',
    )

    section_items = [
        ("핵심 이슈", report.get("key_points", []), True),
        ("향후 전망", report.get("outlook", ""), False),
        ("반복 이슈", report.get("recurring_topics", []), True),
        ("체크 포인트", report.get("watch_points", []), True),
        ("자소서/면접 반영 포인트", report.get("application_tips", []), True),
    ]
    section_cards = []
    for label, content, is_list in section_items:
        if is_list:
            body = _list_html(content, f"정리된 {label} 없음")
        else:
            body = f'<p class="surface-copy">{escape(content or "정보 없음")}</p>'
        section_cards.append(_surface_card(label, body))

    # 뉴스 아카이브에는 출처 포함
    used_articles = report.get("used_articles") or report.get("articles") or []
    source_html = ""
    if used_articles:
        source_items = []
        for item in used_articles:
            title = escape(item.get("title", "기사"))
            source = escape(item.get("source", ""))
            date = escape(item.get("date", ""))
            topic = escape(item.get("topic", ""))
            relevance = escape(item.get("relevance", ""))
            description = escape(item.get("description", ""))
            url = item.get("url", "")
            meta = " · ".join(p for p in [source, date, topic, relevance] if p)
            link_html = ""
            if url:
                safe_url = escape(url, quote=True)
                link_html = f'<a class="news-source-link" href="{safe_url}" target="_blank" rel="noopener noreferrer">기사 열기</a>'
            source_items.append(f"""
            <div class="news-source-card">
                <div class="news-source-title">{title}</div>
                <div class="news-source-meta">{meta}</div>
                <div class="news-source-copy">{description}</div>
                {link_html}
            </div>
            """)
        source_html = _section_divider("기사 출처") + "".join(source_items)
    elif report.get("source_lines"):
        source_html = (
            _section_divider("기사 출처")
            + _surface_card("", f'<pre>{escape(report.get("source_lines", ""))}</pre>')
        )

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{company_name} 뉴스 브리프</title>
  <style>{ARCHIVE_CSS}</style>
</head>
<body>
  <div class="container">
    <div class="hero-panel">
      <div class="hero-eyebrow">{APP_NAME}</div>
      <h1 class="hero-title">{company_name} 뉴스 브리프</h1>
      <div class="hero-copy">최근 수집된 뉴스를 요약한 회사 브리핑</div>
      <div class="hero-meta">
        <span class="hero-pill">내보낸 시각: {exported_at}</span>
      </div>
    </div>

    {metrics_html}
    {summary_card}
    {''.join(section_cards)}
    {source_html}
  </div>
</body>
</html>"""


def make_news_archive_filename() -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"company-news-brief-{timestamp}.html"
