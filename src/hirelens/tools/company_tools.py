import httpx
import pandas as pd
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = PROJECT_ROOT / "data" / "reference" / "companies_krx_20260323.csv"
TOSS_API_URL = "https://wts-info-api.tossinvest.com/api/v2/stock-infos"


def _normalize_corporate_text(text: str | None) -> str:
    if not text:
        return ""

    normalized = " ".join(str(text).split())
    replacements = {
        "동사는": "이 회사는",
        "당사는": "이 회사는",
        "하였음": "했습니다",
        "했음": "했습니다",
        "되었음": "되었습니다",
        "였음": "였습니다",
        "임.": "입니다.",
        "임": "입니다",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)

    normalized = re.sub(r"\s+([.,])", r"\1", normalized)
    return normalized.strip()


def _normalize_text_list(items: list | None) -> list[str]:
    if not items:
        return []
    normalized_items: list[str] = []
    for item in items:
        if not item:
            continue
        text = _normalize_corporate_text(str(item))
        if text:
            normalized_items.append(text)
    return normalized_items


def get_code(company_name: str) -> str:
    """
    회사 이름으로 CSV에서 종목 정보를 검색하여 JSON 문자열로 반환한다.
    """
    df = pd.read_csv(DATA_PATH, encoding='cp949')
    matched = df[df['한글 종목명'].str.contains(company_name, na=False)]
    return matched.to_json(force_ascii=False)


def get_company_info(stock_code: str) -> dict:
    """
    종목 코드(예: '090430' 또는 'A090430')로 토스증권 API에서 회사 개요를 조회하여
    주요 정보만 추려서 반환한다.
    """
    if not stock_code.startswith('A'):
        stock_code = f'A{stock_code}'
    url = f"{TOSS_API_URL}/{stock_code}/overview"
    r = httpx.get(url)
    r.raise_for_status()
    data = r.json()

    result = data.get('result') or {}
    company = result.get('company') or {}
    market = result.get('market') or {}
    wics = company.get('wics') or {}
    comment = company.get('comment') or {}

    if not company:
        return {'error': f'{stock_code}에 해당하는 회사 정보가 없다'}

    return {
        '종목코드': company.get('code'),
        '회사명': company.get('name'),
        '시장': market.get('displayName'),
        '업종': wics.get('displayName'),
        'CEO': company.get('ceo'),
        '회사소개': _normalize_corporate_text(company.get('description')),
        '시가총액': result.get('marketValueKrw'),
        '발행주식수': company.get('sharesOutstanding'),
        '상장일': company.get('listDate'),
        '홈페이지': company.get('homepageUrl'),
        '기업코멘트': _normalize_text_list(comment.get('comments')),
        '전망': _normalize_text_list(comment.get('forecasts')),
    }
