from datetime import datetime
from html import escape

from hirelens.evaluation.models import EVAL_STATE_KEYS, EVALUATOR_ROLES
from hirelens.web import APP_NAME, APP_TITLE
from hirelens.web.components import build_result_summary, build_revision_suggestions


def build_result_archive_html(result: dict) -> str:
    exported_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_decision = result.get("final_decision", "")
    final_score = result.get("final_score", 0.0)
    is_consensus = result.get("is_consensus", False)
    cover_letter = escape(result.get("_cover_letter", ""))
    reference_text = escape(result.get("_reference_text", ""))
    news_report = result.get("_company_news_report", {}) or {}
    summary = build_result_summary(result)
    revision = build_revision_suggestions(result)

    role_cards = []
    for role_key, role_name in EVALUATOR_ROLES.items():
        evals = result.get(EVAL_STATE_KEYS[role_key], [])
        if not evals:
            continue
        ev = evals[0]
        strengths_html = "".join(f"<li>{escape(item)}</li>" for item in ev.key_strengths)
        weaknesses_html = "".join(f"<li>{escape(item)}</li>" for item in ev.key_weaknesses)
        role_cards.append(
            f"""
            <section class="card">
                <h3>{escape(role_name)}</h3>
                <p><strong>판정</strong> {escape(ev.decision)} / <strong>점수</strong> {ev.score:.1f}</p>
                <p>{escape(ev.reasoning)}</p>
                <div class="grid">
                    <div><h4>강점</h4><ul>{strengths_html}</ul></div>
                    <div><h4>보완 포인트</h4><ul>{weaknesses_html}</ul></div>
                </div>
            </section>
            """,
        )

    round_sections = []
    hr_eval_count = len(result.get("hr_evals", []))
    if hr_eval_count > 1:
        for round_idx in range(hr_eval_count - 1):
            round_rows = []
            for role_key, role_name in EVALUATOR_ROLES.items():
                evals = result.get(EVAL_STATE_KEYS[role_key], [])
                if len(evals) <= round_idx + 1:
                    continue
                prev_ev = evals[round_idx]
                curr_ev = evals[round_idx + 1]
                round_rows.append(
                    f"""
                    <div class="subcard">
                        <h4>{escape(role_name)}</h4>
                        <p><strong>{escape(prev_ev.decision)}</strong> ({prev_ev.score:.1f})
                           -> <strong>{escape(curr_ev.decision)}</strong> ({curr_ev.score:.1f})</p>
                        <p>{escape(curr_ev.reasoning)}</p>
                    </div>
                    """,
                )
            round_sections.append(
                f"""
                <section class="card">
                    <h3>협상 라운드 {round_idx + 1}</h3>
                    <div class="grid">{''.join(round_rows)}</div>
                </section>
                """,
            )

    interview_questions = result.get("interview_questions", {})
    interview_section = ""
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
            items_html = "".join(f"<li>{escape(q)}</li>" for q in items) or "<li>생성된 질문 없음</li>"
            category_cards.append(
                f'<div class="subcard"><h4>{label}</h4><ul>{items_html}</ul></div>',
            )
        interview_section = f"""
        <section class="card">
            <h2>예상 면접 질문</h2>
            <div class="grid">{''.join(category_cards)}</div>
        </section>
        """

    reference_section = ""
    if reference_text:
        reference_section = f"""
        <section class="card">
            <h3>참고한 합격 사례</h3>
            <pre>{reference_text}</pre>
        </section>
        """

    news_section = ""
    if news_report:
        recurring_topics_html = "".join(
            f"<li>{escape(item)}</li>" for item in news_report.get("recurring_topics", [])
        ) or "<li>반복 이슈 없음</li>"
        key_points_html = "".join(
            f"<li>{escape(item)}</li>" for item in news_report.get("key_points", [])
        ) or "<li>정리된 핵심 이슈 없음</li>"
        watch_points_html = "".join(
            f"<li>{escape(item)}</li>" for item in news_report.get("watch_points", [])
        ) or "<li>정리된 체크 포인트 없음</li>"
        application_tips_html = "".join(
            f"<li>{escape(item)}</li>" for item in news_report.get("application_tips", [])
        ) or "<li>정리된 반영 포인트 없음</li>"
        source_lines = escape(news_report.get("source_lines", ""))
        news_section = f"""
        <section class="card">
            <h2>회사 뉴스 브리프</h2>
            <div class="subcard">
                <h3>핵심 요약</h3>
                <p>{escape(news_report.get("summary", ""))}</p>
                <p>수집 기사 {int(news_report.get("article_count", 0))}건 / 선별 기사 {int(news_report.get("relevant_article_count", 0))}건 / 브리프 반영 {int(news_report.get("used_article_count", 0))}건</p>
            </div>
            <div class="grid" style="margin-top: 0.8rem;">
              <div class="subcard">
                <h3>향후 전망</h3>
                <p>{escape(news_report.get("outlook", ""))}</p>
              </div>
              <div class="subcard">
                <h3>반복 이슈</h3>
                <ul>{recurring_topics_html}</ul>
              </div>
              <div class="subcard">
                <h3>핵심 이슈</h3>
                <ul>{key_points_html}</ul>
              </div>
              <div class="subcard">
                <h3>체크 포인트</h3>
                <ul>{watch_points_html}</ul>
              </div>
              <div class="subcard">
                <h3>자소서/면접 반영 포인트</h3>
                <ul>{application_tips_html}</ul>
              </div>
            </div>
            <div class="subcard" style="margin-top: 0.8rem;">
              <h3>기사 출처</h3>
              <pre>{source_lines}</pre>
            </div>
        </section>
        """

    strengths_html = "".join(
        f"<li>{escape(item)}</li>" for item in summary["strengths"]
    ) or "<li>공통 강점이 명확히 겹치지 않았습니다.</li>"
    weaknesses_html = "".join(
        f"<li>{escape(item)}</li>" for item in summary["weaknesses"]
    ) or "<li>공통 보완 포인트가 명확히 겹치지 않았습니다.</li>"

    revision_weaknesses_html = "".join(
        f"<li>{escape(w)}</li>" for w in revision["weaknesses"]
    ) or "<li>공통 약점 없음</li>"
    revision_strengths_html = "".join(
        f"<li>{escape(s)}</li>" for s in revision["strengths"]
    ) or "<li>공통 강점 없음</li>"

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{APP_NAME} 결과 아카이브</title>
  <style>
    body {{
      margin: 0; padding: 2.4rem;
      font-family: "Noto Sans KR", "Apple SD Gothic Neo", sans-serif;
      color: #0f172a; background: #f8fafc; line-height: 1.65;
    }}
    h1, h2, h3, h4, p {{ margin-top: 0; }}
    .hero {{
      padding: 1.6rem 1.8rem; border-radius: 24px;
      background: linear-gradient(135deg, #0f172a, #334155);
      color: #f8fafc; margin-bottom: 1.2rem;
    }}
    .meta {{ display: flex; gap: 0.7rem; flex-wrap: wrap; margin-top: 1rem; }}
    .pill {{
      background: rgba(255,255,255,0.12);
      border: 1px solid rgba(255,255,255,0.18);
      border-radius: 999px; padding: 0.35rem 0.7rem; font-size: 0.9rem;
    }}
    .card {{
      background: #ffffff; border: 1px solid #dbe4f0;
      border-radius: 22px; padding: 1.25rem 1.35rem;
      margin-bottom: 1rem; box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
    }}
    .subcard {{
      background: #f8fafc; border: 1px solid #e2e8f0;
      border-radius: 16px; padding: 1rem;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 0.8rem;
    }}
    pre {{
      white-space: pre-wrap; word-break: break-word;
      background: #f8fafc; border: 1px solid #e2e8f0;
      border-radius: 16px; padding: 1rem; overflow-x: auto;
    }}
    ul {{ padding-left: 1.2rem; }}
  </style>
</head>
<body>
  <section class="hero">
    <h1>{APP_NAME} 결과 아카이브</h1>
    <p>{APP_TITLE}</p>
    <div class="meta">
      <span class="pill">내보낸 시각: {exported_at}</span>
      <span class="pill">최종 판정: {escape(final_decision)}</span>
      <span class="pill">가중 점수: {final_score:.1f}</span>
      <span class="pill">결정 방식: {"합의" if is_consensus else "과반수"}</span>
    </div>
  </section>
  <section class="card">
    <h2>1차 평가 결과</h2>
    <div class="grid">{''.join(role_cards)}</div>
  </section>
  {''.join(round_sections)}
  <section class="card">
    <h2>최종 판정 요약</h2>
    <p>{escape(summary["judgment"])}</p>
    <div class="grid">
      <div class="subcard"><h3>공통 강점</h3><ul>{strengths_html}</ul></div>
      <div class="subcard"><h3>보완 포인트</h3><ul>{weaknesses_html}</ul></div>
    </div>
  </section>
  <section class="card">
    <h2>자소서 수정안</h2>
    <div class="grid">
      <div class="subcard">
        <h3>개선이 필요한 부분</h3>
        <ul>{revision_weaknesses_html}</ul>
      </div>
      <div class="subcard">
        <h3>유지할 강점</h3>
        <ul>{revision_strengths_html}</ul>
      </div>
    </div>
  </section>
  {interview_section}
  {news_section}
  {reference_section}
  <section class="card">
    <h2>원본 자기소개서</h2>
    <pre>{cover_letter}</pre>
  </section>
</body>
</html>"""


def make_archive_filename() -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"cover-letter-review-{timestamp}.html"


def build_news_archive_html(report: dict) -> str:
    exported_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    company_name = escape(report.get("company_name", "회사"))
    summary = escape(report.get("summary", ""))
    outlook = escape(report.get("outlook", ""))
    recurring_topics_html = "".join(
        f"<li>{escape(item)}</li>" for item in report.get("recurring_topics", [])
    ) or "<li>반복 이슈 없음</li>"
    key_points_html = "".join(
        f"<li>{escape(item)}</li>" for item in report.get("key_points", [])
    ) or "<li>정리된 핵심 이슈 없음</li>"
    watch_points_html = "".join(
        f"<li>{escape(item)}</li>" for item in report.get("watch_points", [])
    ) or "<li>정리된 체크 포인트 없음</li>"
    application_tips_html = "".join(
        f"<li>{escape(item)}</li>" for item in report.get("application_tips", [])
    ) or "<li>정리된 반영 포인트 없음</li>"
    source_lines = escape(report.get("source_lines", ""))

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{company_name} 뉴스 브리프</title>
  <style>
    body {{
      margin: 0; padding: 2.4rem;
      font-family: "Noto Sans KR", "Apple SD Gothic Neo", sans-serif;
      color: #0f172a; background: #f8fafc; line-height: 1.65;
    }}
    .hero, .card, .subcard {{
      border-radius: 22px;
      border: 1px solid #dbe4f0;
    }}
    .hero {{
      background: linear-gradient(135deg, #0f172a, #334155);
      color: #f8fafc; padding: 1.6rem 1.8rem; margin-bottom: 1rem;
    }}
    .card {{
      background: #ffffff; padding: 1.25rem 1.35rem; margin-bottom: 1rem;
      box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
    }}
    .subcard {{
      background: #f8fafc; padding: 1rem; margin-top: 0.8rem;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 0.8rem;
    }}
    pre {{
      white-space: pre-wrap; word-break: break-word;
      background: #f8fafc; border: 1px solid #e2e8f0;
      border-radius: 16px; padding: 1rem; overflow-x: auto;
    }}
  </style>
</head>
<body>
  <section class="hero">
    <h1>{company_name} 뉴스 브리프</h1>
    <p>최근 수집된 뉴스를 요약한 회사 브리핑</p>
    <p>내보낸 시각: {exported_at}</p>
  </section>
  <section class="card">
    <h2>핵심 요약</h2>
    <p>{summary}</p>
    <p>수집 기사 {int(report.get("article_count", 0))}건 / 선별 기사 {int(report.get("relevant_article_count", 0))}건 / 브리프 반영 {int(report.get("used_article_count", 0))}건</p>
    <div class="grid">
      <div class="subcard">
        <h3>향후 전망</h3>
        <p>{outlook}</p>
      </div>
      <div class="subcard">
        <h3>반복 이슈</h3>
        <ul>{recurring_topics_html}</ul>
      </div>
      <div class="subcard">
        <h3>핵심 이슈</h3>
        <ul>{key_points_html}</ul>
      </div>
      <div class="subcard">
        <h3>체크 포인트</h3>
        <ul>{watch_points_html}</ul>
      </div>
      <div class="subcard">
        <h3>자소서/면접 반영 포인트</h3>
        <ul>{application_tips_html}</ul>
      </div>
    </div>
  </section>
  <section class="card">
    <h2>기사 출처</h2>
    <pre>{source_lines}</pre>
  </section>
</body>
</html>"""


def make_news_archive_filename() -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"company-news-brief-{timestamp}.html"
