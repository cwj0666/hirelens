import os

from google.adk.agents import Agent

from ..evaluation.models import DEFAULT_ADK_MODEL
from ..tools.company_tools import get_code, get_company_info

company_info_agent = Agent(
    name='company_info_agent',
    model=os.getenv("ADK_MODEL", DEFAULT_ADK_MODEL),
    description='사용자가 입력한 회사명으로 종목 코드를 검색하고 회사 상세 정보를 조회하는 에이전트',
    instruction=(
        '사용자의 메시지에서 회사명을 추출한다. '
        'get_code로 종목코드를 찾고, get_company_info로 상세 정보를 조회한다. '
        '조회한 회사 정보를 요약하여 전달한다. '
        '시가총액은 억 원 단위로 환산하여 읽기 쉽게 표현한다.'
    ),
    output_key='company_info',
    tools=[get_code, get_company_info],
)
