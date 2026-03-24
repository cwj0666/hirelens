import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from urllib.parse import quote, urlparse

import httpx
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from hirelens.evaluation.models import DEFAULT_MODEL
from hirelens.evaluation.storage import load_recent_news_report, save_news_report

NAVER_NEWS_URL = "https://openapi.naver.com/v1/search/news.json"
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
DEFAULT_NEWS_WINDOW_DAYS = 180
DEFAULT_RAW_RESULT_LIMIT = 30
DEFAULT_FINAL_ARTICLE_LIMIT = 12
DEFAULT_CACHE_FRESHNESS_HOURS = 12
RAW_RESULTS_PER_QUERY = 6

COMPANY_QUERY_SUFFIXES = (
    "",
    "실적",
    "수주",
    "투자",
    "신사업",
    "전략",
    "채용",
    "조직",
)
INDUSTRY_QUERY_SUFFIXES = (
    "전망",
    "채용 동향",
    "투자 동향",
)

BLOCKED_NEWS_DOMAINS = {
    "blog.naver.com",
    "m.blog.naver.com",
    "post.naver.com",
    "cafe.naver.com",
    "brunch.co.kr",
    "tistory.com",
    "velog.io",
    "youtube.com",
    "www.youtube.com",
}
TRUSTED_NEWS_DOMAINS = {
    "yna.co.kr",
    "yonhapnewstv.co.kr",
    "newsis.com",
    "news1.kr",
    "edaily.co.kr",
    "hankyung.com",
    "mk.co.kr",
    "sedaily.com",
    "asiae.co.kr",
    "etnews.com",
    "zdnet.co.kr",
    "ddaily.co.kr",
    "bloter.net",
    "thelec.kr",
    "inews24.com",
    "fnnews.com",
    "joongang.co.kr",
    "chosun.com",
    "donga.com",
    "khan.co.kr",
    "hani.co.kr",
    "mt.co.kr",
    "mtn.co.kr",
    "biz.chosun.com",
    "etoday.co.kr",
    "theguru.co.kr",
    "dailian.co.kr",
    "dealsite.co.kr",
    "e2news.com",
    "ekn.kr",
    "hyundaimotorgroup.com",
    "dart.fss.or.kr",
}
TRUSTED_SOURCE_KEYWORDS = {
    "연합뉴스",
    "뉴시스",
    "뉴스1",
    "이데일리",
    "한국경제",
    "매일경제",
    "서울경제",
    "아시아경제",
    "전자신문",
    "ZDNET",
    "디지털데일리",
    "블로터",
    "더벨",
    "더구루",
    "머니투데이",
    "머니투데이방송",
    "파이낸셜뉴스",
    "조선비즈",
    "중앙일보",
    "조선일보",
    "동아일보",
    "한겨레",
    "경향신문",
    "에너지경제신문",
    "딜사이트",
    "현대자동차그룹",
    "Hyundai Motor Group",
    "DART",
}
IRRELEVANT_TOPIC_KEYWORDS = {
    "배구",
    "축구",
    "야구",
    "농구",
    "골프",
    "v리그",
    "리그",
    "득점",
    "우승",
    "감독",
    "선수",
    "세트스코어",
    "라스트 댄스",
    "양효진",
}
IMPORTANT_NEWS_KEYWORDS = {
    "실적",
    "매출",
    "영업이익",
    "수주",
    "계약",
    "투자",
    "증설",
    "생산",
    "공장",
    "신사업",
    "전략",
    "파트너십",
    "제휴",
    "인수",
    "합병",
    "AI",
    "반도체",
    "배터리",
    "채용",
    "인재",
    "조직",
    "전망",
    "성장",
}


class CompanyNewsReport(BaseModel):
    summary: str = Field(description="최근 회사/산업 뉴스 핵심 요약 3~5문장")
    outlook: str = Field(description="향후 3~6개월 관점의 전망 3~4문장")
    recurring_topics: list[str] = Field(description="반복적으로 관찰된 핵심 주제 2~4개")
    key_points: list[str] = Field(description="지원자 관점 핵심 이슈 4개 이하")
    watch_points: list[str] = Field(description="주의해서 볼 변수 4개 이하")
    application_tips: list[str] = Field(description="자소서나 면접에서 반영할 포인트 4개 이하")


class NewsArticleAssessment(BaseModel):
    index: int = Field(description="기사 인덱스")
    keep: bool = Field(description="브리프에 반영할 가치가 있는 기사인지 여부")
    relevance: str = Field(description="높음, 중간, 낮음 중 하나")
    topic: str = Field(description="기사의 주제 분류")
    theme: str = Field(description="반복 이슈로 묶기 위한 짧은 테마")
    reason: str = Field(description="선정 또는 제외 이유 한 문장")


class NewsAssessmentBatch(BaseModel):
    items: list[NewsArticleAssessment]


def _parse_pub_date(pub_date: str) -> str:
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.strptime(pub_date, fmt).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    return pub_date[:10] if pub_date else ""


def _strip_html_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def _extract_domain(url: str) -> str:
    if not url:
        return ""
    hostname = urlparse(url).hostname or ""
    return hostname.lower().removeprefix("www.")


def _parse_date_object(date_str: str) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def _is_recent(date_str: str, max_age_days: int) -> bool:
    parsed = _parse_date_object(date_str)
    if parsed is None:
        return False
    cutoff = datetime.now() - timedelta(days=max_age_days)
    return parsed.date() >= cutoff.date()


def _is_allowed_domain(domain: str) -> bool:
    if not domain:
        return False
    return all(not domain.endswith(blocked) for blocked in BLOCKED_NEWS_DOMAINS)


def _is_trusted_source(source: str, domain: str) -> bool:
    if any(domain == trusted or domain.endswith(f".{trusted}") for trusted in TRUSTED_NEWS_DOMAINS):
        return True
    return any(keyword.lower() in source.lower() for keyword in TRUSTED_SOURCE_KEYWORDS)


def _normalize_query(query_text: str) -> str:
    return " ".join(query_text.split())


def _build_search_queries(company_name: str, industry: str = "") -> list[str]:
    queries: list[str] = []
    for suffix in COMPANY_QUERY_SUFFIXES:
        base = f"\"{company_name}\" {suffix}".strip()
        queries.append(_normalize_query(base))

    cleaned_industry = (industry or "").strip()
    if cleaned_industry:
        for suffix in INDUSTRY_QUERY_SUFFIXES:
            queries.append(_normalize_query(f"\"{cleaned_industry}\" {suffix}"))

    unique_queries: list[str] = []
    seen: set[str] = set()
    for query in queries:
        if not query or query in seen:
            continue
        unique_queries.append(query)
        seen.add(query)
    return unique_queries


def _dedupe_and_filter_items(items: list[dict], max_results: int, max_age_days: int) -> list[dict]:
    filtered = []
    seen_titles: set[str] = set()

    for item in items:
        title = " ".join((item.get("title") or "").split())
        source = (item.get("source") or "").strip()
        domain = (item.get("domain") or "").strip().lower()
        date = item.get("date", "")
        description = " ".join((item.get("description") or "").split())
        combined_text = f"{title} {description}".lower()

        if not title or title in seen_titles:
            continue
        if not _is_recent(date, max_age_days):
            continue
        if any(keyword.lower() in combined_text for keyword in IRRELEVANT_TOPIC_KEYWORDS):
            continue
        if not _is_allowed_domain(domain):
            continue
        if not _is_trusted_source(source, domain):
            continue

        normalized = dict(item)
        normalized["title"] = title
        normalized["source"] = source or domain
        normalized["description"] = description
        filtered.append(normalized)
        seen_titles.add(title)

    filtered.sort(
        key=lambda item: _parse_date_object(item.get("date", "")) or datetime.min,
        reverse=True,
    )
    return filtered[:max_results]


def _format_news_items(items: list[dict]) -> str:
    lines = []
    for i, item in enumerate(items, 1):
        title = item.get("title", "")
        source = item.get("source", "")
        date = item.get("date", "")
        description = item.get("description", "")
        meta = ", ".join(filter(None, [source, date]))
        header = f"[{i}] {title}" + (f" ({meta})" if meta else "")
        lines.append(header)
        if description:
            lines.append(f"    {description}")
    return "\n".join(lines)


def _format_news_sources(items: list[dict]) -> str:
    lines = []
    for i, item in enumerate(items, 1):
        title = item.get("title", "")
        source = item.get("source", "")
        date = item.get("date", "")
        description = item.get("description", "")
        url = item.get("url", "")
        meta = " | ".join(filter(None, [source, date]))
        line = f"- [{i}] {title}" + (f" ({meta})" if meta else "")
        if url:
            line += f"\n  링크: {url}"
        if description:
            line += f"\n  요약: {description}"
        lines.append(line)
    return "\n".join(lines)


def _format_articles_for_review(items: list[dict]) -> str:
    lines = []
    for index, item in enumerate(items):
        lines.append(
            f"[{index}] query={item.get('query_text', '')} | "
            f"title={item.get('title', '')} | source={item.get('source', '')} | "
            f"date={item.get('date', '')} | summary={item.get('description', '')}",
        )
    return "\n".join(lines)


def _search_naver(query_text: str, max_results: int) -> list[dict]:
    client_id = os.getenv("NAVER_CLIENT_ID", "")
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return []

    response = httpx.get(
        NAVER_NEWS_URL,
        params={
            "query": query_text,
            "sort": "date",
            "display": max_results,
        },
        headers={
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    items = []
    for item in data.get("items", []):
        title = _strip_html_tags(item.get("title", ""))
        description = _strip_html_tags(item.get("description", ""))
        original_link = item.get("originallink", "")
        domain = _extract_domain(original_link)
        items.append({
            "query_text": query_text,
            "title": title,
            "source": domain,
            "domain": domain,
            "date": _parse_pub_date(item.get("pubDate", "")),
            "description": description,
            "url": original_link,
        })
    return items


def _search_google_rss(query_text: str, max_results: int, max_age_days: int) -> list[dict]:
    query = quote(f"{query_text} when:{max_age_days}d")
    url = f"{GOOGLE_NEWS_RSS_URL}?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    response = httpx.get(url, timeout=10, follow_redirects=True)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for item_el in channel.findall("item")[:max_results]:
        title = item_el.findtext("title", "")
        pub_date = item_el.findtext("pubDate", "")
        source = item_el.findtext("source", "")
        link = item_el.findtext("link", "")
        items.append({
            "query_text": query_text,
            "title": title.rsplit(" - ", 1)[0].strip(),
            "source": source.strip(),
            "domain": _extract_domain(link),
            "date": _parse_pub_date(pub_date),
            "description": "",
            "url": link,
        })
    return items


def _collect_news_items(
    company_name: str,
    industry: str,
    max_age_days: int,
    raw_limit: int,
    per_query_results: int,
) -> tuple[list[str], list[dict]]:
    queries = _build_search_queries(company_name, industry)
    items: list[dict] = []

    for query_text in queries:
        try:
            items.extend(_search_naver(query_text, per_query_results))
        except Exception:
            pass

        try:
            items.extend(_search_google_rss(query_text, per_query_results, max_age_days))
        except Exception:
            pass

    if not items:
        return queries, []

    filtered = _dedupe_and_filter_items(items, max_results=raw_limit, max_age_days=max_age_days)
    return queries, filtered


def _heuristic_review_items(items: list[dict]) -> list[dict]:
    reviewed = []
    for item in items:
        combined = f"{item.get('title', '')} {item.get('description', '')}".lower()
        hit_count = sum(1 for keyword in IMPORTANT_NEWS_KEYWORDS if keyword.lower() in combined)
        keep = hit_count > 0
        relevance = "높음" if hit_count >= 2 else "중간" if hit_count == 1 else "낮음"
        reviewed.append(
            {
                **item,
                "keep": keep,
                "relevance": relevance,
                "topic": "회사/산업 동향" if keep else "노이즈 가능성",
                "theme": item.get("query_text", "") or "기타",
                "reason": "핵심 사업/실적/채용 관련 키워드가 포함돼 있습니다." if keep else "지원자 관점 관련성이 약합니다.",
            },
        )
    return reviewed


def _review_news_items(
    company_name: str,
    industry: str,
    items: list[dict],
    model_name: str,
    temperature: float,
) -> list[dict]:
    if not items:
        return []

    parser = PydanticOutputParser(pydantic_object=NewsAssessmentBatch)
    prompt = PromptTemplate(
        template=(
            "당신은 취업 지원자를 위한 기업 뉴스 선별기다.\n"
            "목표는 회사 이해, 사업 방향, 실적 흐름, 수주/투자, 조직/채용, 산업 전망을 파악하는 데 도움되는 기사만 남기는 것이다.\n"
            "- keep=true: 지원자가 자소서나 면접에서 언급할 가치가 있는 기사\n"
            "- keep=false: 스포츠, 연예, 단순 화제성 기사, 중복성이 크거나 취업 맥락과 약한 기사\n"
            "- relevance는 높음/중간/낮음 중 하나\n"
            "- topic은 예: 실적, 수주, 투자, 신사업, 조직/채용, 산업전망, 정책/규제\n"
            "- theme는 반복 이슈를 묶는 짧은 표현\n"
            "- 기사에 없는 사실을 추가하지 말 것\n\n"
            "회사명: {company_name}\n"
            "업종: {industry}\n"
            "기사 후보:\n{article_lines}\n\n"
            "{format_instructions}"
        ),
        input_variables=["company_name", "industry", "article_lines"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | ChatOpenAI(model=model_name, temperature=min(temperature, 0.2)) | parser

    reviewed_items = list(items)
    chunk_size = 10
    try:
        for start in range(0, len(items), chunk_size):
            chunk = items[start:start + chunk_size]
            result = chain.invoke({
                "company_name": company_name,
                "industry": industry or "정보 없음",
                "article_lines": _format_articles_for_review(chunk),
            })
            assessment_map = {entry.index: entry for entry in result.items}
            for offset, article in enumerate(chunk):
                assessment = assessment_map.get(offset)
                if assessment is None:
                    continue
                reviewed_items[start + offset] = {
                    **article,
                    "keep": assessment.keep,
                    "relevance": assessment.relevance,
                    "topic": assessment.topic,
                    "theme": assessment.theme,
                    "reason": assessment.reason,
                }
        return reviewed_items
    except Exception:
        return _heuristic_review_items(items)


def _select_relevant_items(items: list[dict], final_limit: int) -> list[dict]:
    if not items:
        return []

    relevance_rank = {"높음": 0, "중간": 1, "낮음": 2}
    kept = [item for item in items if item.get("keep")]
    if len(kept) < 5:
        kept = [
            item for item in items
            if item.get("relevance") in {"높음", "중간"}
        ] or list(items)

    kept.sort(
        key=lambda item: (
            relevance_rank.get(item.get("relevance", "낮음"), 9),
            -((_parse_date_object(item.get("date", "")) or datetime.min).toordinal()),
        ),
    )
    return kept[:final_limit]


def _build_briefing_text(report: dict) -> str:
    sections = []

    summary = (report.get("summary") or "").strip()
    outlook = (report.get("outlook") or "").strip()
    recurring_topics = report.get("recurring_topics") or []
    key_points = report.get("key_points") or []
    watch_points = report.get("watch_points") or []
    application_tips = report.get("application_tips") or []

    if summary:
        sections.append(f"핵심 요약:\n{summary}")
    if outlook:
        sections.append(f"향후 전망:\n{outlook}")
    if recurring_topics:
        sections.append("반복 이슈:\n" + "\n".join(f"- {item}" for item in recurring_topics))
    if key_points:
        sections.append("핵심 이슈:\n" + "\n".join(f"- {item}" for item in key_points))
    if watch_points:
        sections.append("체크 포인트:\n" + "\n".join(f"- {item}" for item in watch_points))
    if application_tips:
        sections.append("자소서/면접 반영 포인트:\n" + "\n".join(f"- {item}" for item in application_tips))

    return "\n\n".join(sections).strip()


def _build_fallback_report(company_name: str, items: list[dict]) -> dict:
    top_items = items[:5]
    recurring_topics = []
    key_points = []
    summary_parts = []

    for item in top_items:
        title = item.get("title", "")
        theme = item.get("theme", "")
        source = item.get("source", "")
        date = item.get("date", "")
        if theme and theme not in recurring_topics:
            recurring_topics.append(theme)
        if title:
            key_points.append(title)
            summary_parts.append(f"{date} 기준 {source}는 {title} 이슈를 다뤘습니다.".strip())

    summary = (
        " ".join(summary_parts)
        if summary_parts
        else f"{company_name} 관련 최근 보도는 확인됐지만 구조화 요약 생성에는 실패했습니다. 다만 반복 기사 기준으로 보면 사업 실행이 실제 실적과 조직 변화로 이어지는지가 핵심 관찰 포인트로 보입니다."
    )
    outlook = (
        f"{company_name}의 최근 보도는 단기 화제성보다 실제 사업 실행과 실적 연결 여부가 향후 3~6개월의 핵심 평가 포인트가 될 가능성을 시사합니다. "
        "다만 기사 수와 출처가 제한적일 수 있으므로, 향후 공시나 추가 보도로 같은 흐름이 이어지는지 보수적으로 확인할 필요가 있습니다."
    )

    return {
        "summary": summary,
        "outlook": outlook,
        "recurring_topics": recurring_topics[:4],
        "key_points": key_points[:3],
        "watch_points": [
            "반복 보도된 계획이 실제 수주·실적·조직 변화로 이어지는지 확인이 필요합니다.",
            "기사 수가 적거나 출처가 제한적이면 해석을 보수적으로 가져가야 합니다.",
        ],
        "application_tips": [
            "지원동기에 최근 반복 이슈 중 하나를 짧게 연결하세요.",
            "면접에서는 최근 사업 방향에 본인이 어떤 기여를 할 수 있는지 준비하세요.",
            "단순 뉴스 나열보다 기사 흐름과 본인 경험을 연결하는 문장 구조가 더 효과적입니다.",
        ],
    }


def _summarize_news_items(
    company_name: str,
    industry: str,
    items: list[dict],
    model_name: str,
    temperature: float,
) -> dict:
    parser = PydanticOutputParser(pydantic_object=CompanyNewsReport)
    prompt = PromptTemplate(
        template=(
            "당신은 채용 지원자를 위한 기업 뉴스 브리핑 작성자다.\n"
            "아래 기사 목록을 읽고 반복적으로 등장하는 이슈를 중심으로 요약하라.\n"
            "- 기사 여러 건에서 공통적으로 보이는 흐름을 우선 정리할 것\n"
            "- 단일 기사에만 나온 내용을 전체 흐름처럼 과장하지 말 것\n"
            "- summary는 현재 상황을 3~5문장으로 요약하고, 사업/조직/산업 흐름이 왜 중요한지도 함께 설명\n"
            "- outlook은 향후 3~6개월 관점의 전망을 3~4문장으로 정리하되, 기대 요인과 불확실성을 함께 명시\n"
            "- recurring_topics는 반복 등장 주제 2~4개\n"
            "- key_points, watch_points, application_tips는 각 4개 이하\n"
            "- bullet도 너무 짧게 끊지 말고, 한 항목이 독립적으로 이해될 정도로 작성\n"
            "- 채용 지원자의 자소서/면접 활용 관점이 드러나야 함\n"
            "- summary와 outlook은 자연스러운 존댓말 문단으로 작성하고, '향후 흐름은 ...으로 정리됩니다' 같은 기계적 표현은 피할 것\n"
            "- 기사 내용을 나열하는 데서 끝내지 말고, 반복적으로 보이는 맥락을 해석해서 설명할 것\n\n"
            "회사명: {company_name}\n"
            "업종: {industry}\n"
            "선별된 기사 목록:\n{news_items}\n\n"
            "{format_instructions}"
        ),
        input_variables=["company_name", "industry", "news_items"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | ChatOpenAI(model=model_name, temperature=min(temperature, 0.2)) | parser
    return chain.invoke({
        "company_name": company_name,
        "industry": industry or "정보 없음",
        "news_items": _format_news_items(items),
    }).model_dump()


def search_company_news(
    company_name: str,
    max_results: int = 5,
    max_age_days: int = DEFAULT_NEWS_WINDOW_DAYS,
) -> str:
    """
    회사 관련 최신 뉴스를 검색하고 선별된 기사 목록을 문자열로 반환한다.
    """
    report = get_company_news_report(
        company_name=company_name,
        max_age_days=max_age_days,
        final_article_limit=max_results,
    )
    used_articles = report.get("used_articles", [])
    if not used_articles:
        return ""
    return _format_news_items(used_articles[:max_results])


def get_company_news_report(
    company_name: str,
    industry: str = "",
    max_age_days: int = DEFAULT_NEWS_WINDOW_DAYS,
    raw_limit: int = DEFAULT_RAW_RESULT_LIMIT,
    final_article_limit: int = DEFAULT_FINAL_ARTICLE_LIMIT,
    model_name: str = DEFAULT_MODEL,
    temperature: float = 0.1,
    use_cache: bool = True,
    cache_freshness_hours: int = DEFAULT_CACHE_FRESHNESS_HOURS,
) -> dict:
    if use_cache:
        cached = load_recent_news_report(company_name, freshness_hours=cache_freshness_hours)
        if cached:
            return cached

    queries, raw_items = _collect_news_items(
        company_name=company_name,
        industry=industry,
        max_age_days=max_age_days,
        raw_limit=raw_limit,
        per_query_results=RAW_RESULTS_PER_QUERY,
    )
    if not raw_items:
        return {}

    reviewed_items = _review_news_items(
        company_name=company_name,
        industry=industry,
        items=raw_items,
        model_name=model_name,
        temperature=temperature,
    )
    used_articles = _select_relevant_items(reviewed_items, final_limit=final_article_limit)
    if not used_articles:
        used_articles = reviewed_items[: min(len(reviewed_items), final_article_limit)]

    try:
        report = _summarize_news_items(
            company_name=company_name,
            industry=industry,
            items=used_articles,
            model_name=model_name,
            temperature=temperature,
        )
    except Exception:
        report = _build_fallback_report(company_name, used_articles)

    report["company_name"] = company_name
    report["industry"] = industry
    report["query_terms"] = queries
    report["article_count"] = len(reviewed_items)
    report["relevant_article_count"] = len([item for item in reviewed_items if item.get("keep")])
    report["used_article_count"] = len(used_articles)
    report["articles"] = reviewed_items
    report["used_articles"] = used_articles
    report["source_lines"] = _format_news_sources(used_articles)
    report["briefing_text"] = _build_briefing_text(report)

    save_news_report(company_name, report)
    return report
