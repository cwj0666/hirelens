# HireLens

자기소개서를 3인 평가자(HR 담당자, 현업 부서장, 인재개발팀)가 협상 기반으로 평가하고, 평가 결과를 바탕으로 코칭까지 연결하는 멀티 에이전트 시스템입니다.

평가 엔진은 LangChain + LangGraph로 구현했으며, 평가 결과 리포트는 Streamlit으로, 코칭 대화는 Google ADK로 각각 제공합니다. 두 인터페이스는 SQLite 세션 저장소를 공유하여 Streamlit에서 생성한 평가 결과를 ADK 코칭 에이전트가 이어받을 수 있습니다.


## 핵심 구조

### 평가 워크플로우 (LangGraph)

평가 파이프라인은 LangGraph의 `StateGraph`로 구성됩니다. 상태 객체 `NegotiationState`가 그래프 전체를 관통하며, 각 노드는 상태를 읽고 갱신하는 순수 함수로 작성되어 있습니다.
<img width="578" height="531" alt="image" src="https://github.com/user-attachments/assets/71ea7059-4282-4022-94f3-8d7786411d7d" />


```
START
  -> evaluate_hr -> evaluate_dept_head -> evaluate_talent_dev
  -> check_consensus
       |-- 합의 도달 또는 최대 라운드 초과 -> finalize
       |-- 불일치 -> negotiate -> check_consensus (반복)
  -> finalize -> generate_interview_questions -> END
```

3인 평가자가 순차적으로 독립 평가를 수행합니다. `check_consensus`에서 판정(통과/보류/불통과)이 일치하면 바로 `finalize`로 진행하고, 불일치하면 `negotiate` 노드에서 각 평가자가 다른 평가자들의 의견을 참고하여 재평가합니다. 협상은 최대 라운드(기본 3회)까지 반복됩니다.

`finalize`에서는 역할별 가중치(HR 0.30, 부서장 0.45, 인재개발 0.25)를 적용해 가중 점수를 산출하고, 다수결로 최종 판정을 결정합니다. 동률일 경우 가중 점수가 높은 판정이 채택됩니다.

### 상태 누적 방식

`NegotiationState`의 평가 리스트 필드(`hr_evals`, `dept_head_evals`, `talent_dev_evals`)는 `Annotated[list, operator.add]`로 선언되어 있습니다. LangGraph의 리듀서 메커니즘에 의해 각 노드가 반환하는 리스트가 기존 리스트에 append됩니다. 따라서 1차 평가와 협상 라운드별 결과가 순서대로 누적되며, `evals[-1]`로 항상 최신 평가에 접근할 수 있습니다.

### 평가자별 프롬프트 설계

각 평가자는 고유한 역할과 평가 기준을 갖습니다.

- **HR 담당자**: 조직문화 적합성, 이직 리스크, 커뮤니케이션 스타일, 지원 동기 진정성을 평가합니다. 기술 역량은 평가 범위에서 제외됩니다.
- **현업 부서장**: 직무 수행 능력, 기술 스택 일치도, 실무 성과, 문제 해결 접근 방식을 평가합니다. 조직 적합성은 평가 범위에서 제외됩니다.
- **인재개발팀**: 성장 잠재력, 학습 속도, 리더십 가능성, 자기 인식 수준을 평가합니다. 당장의 실무 역량보다 장기적 성장 가치를 봅니다.

각 프롬프트에는 점수 기준표(90~100 즉시 합격 ~ 0~39 평가 불가), 가점/감점 요인, 경력 수준별 평가 지침이 포함됩니다. 협상 프롬프트에서는 역할별로 양보 조건 점수(HR 5점, 부서장 8점, 인재개발 5점)를 다르게 설정하여 각 역할의 고집 정도에 차이를 두었습니다.

### 구조화된 출력

모든 평가 결과는 `EvaluatorOutput` Pydantic 모델로 파싱됩니다. LangChain의 `PydanticOutputParser`가 LLM 출력을 자동으로 검증하고 타입 변환합니다.

```python
class EvaluatorOutput(BaseModel):
    decision: Literal["통과", "보류", "불통과"]
    score: float          # 0.0 ~ 100.0
    reasoning: str        # 판정 근거 3~5문장
    key_strengths: list[str]   # 핵심 강점 1~3개
    key_weaknesses: list[str]  # 핵심 약점 1~3개
```


## 부가 기능

### 회사 뉴스 수집

네이버 뉴스 API와 Google News RSS를 병합하여 지원 회사의 최근 뉴스를 수집합니다. 블로그, 카페, 유튜브 등 비신뢰 소스는 차단하고, 주요 언론사 화이트리스트를 적용합니다. 수집된 기사는 LLM이 주제별로 분류하고 관련도를 판단하여 최종 브리프를 생성합니다.

뉴스 데이터는 평가 프롬프트의 `{company_news}` 변수로 주입되어 평가에 반영됩니다. 브리프는 SQLite에 캐싱하여 동일 회사에 대해 12시간 이내 재요청 시 API 호출을 생략합니다.

### 회사 정보 조회

KRX 상장사 CSV에서 종목 코드를 검색하고, 토스증권 API를 통해 기업 개요, 재무 지표 등 정량 정보를 조회합니다.

### 면접 질문 예상

평가 완료 후 `generate_interview_questions` 노드에서 자소서 내용, 평가 결과의 강점/약점, 회사 뉴스를 종합하여 4개 카테고리(경험 기반, 직무 적합성, 회사 관련, 약점 보완)의 면접 예상 질문을 생성합니다.

### RAG 합격 사례 검색

Chroma 벡터 저장소에 합격 사례를 저장하고, 업종/직무 필터와 MMR 검색으로 유사 사례를 조회합니다. OpenAI `text-embedding-3-small` 모델로 임베딩하며, 검색된 사례는 평가 프롬프트에 참고 자료로 주입됩니다.


## Streamlit과 ADK의 연결

Streamlit에서 평가가 완료되면 결과를 SQLite `evaluation_sessions` 테이블에 저장하고, `HL-YYYYMMDD-XXXX` 형식의 세션 ID를 발급합니다. 이 세션 ID를 ADK 채팅에 입력하면 `before_agent_callback`이 패턴을 인식하여 자동으로 세션을 로드합니다.

ADK 코칭 에이전트는 로드된 평가 결과를 바탕으로 문단별 수정 방향 제안, 면접 답변 코칭, 수정본 재평가(MCP 경유) 및 이전 결과 비교를 수행합니다. 재평가는 FastMCP 서버를 통해 동일한 LangGraph 파이프라인을 호출합니다.


## 프로젝트 구조

```
src/
  hirelens/
    agent.py                ADK 코칭 에이전트 (root_agent)
    evaluation/
      models.py             Pydantic 모델, 상수 (가중치, 라운드, 역할 정의)
      prompts.py            4개 평가 프롬프트 (HR, 부서장, 인재개발, 협상)
      workflow.py           LangGraph StateGraph (평가 -> 합의 -> 협상 -> 최종)
      storage.py            SQLite + Chroma RAG 저장소
    tools/
      company_tools.py      KRX 종목 검색, 토스증권 API 조회
      news_tools.py         뉴스 수집, 선별, 요약 파이프라인
      session_tools.py      세션 로드/목록 (ADK tool)
    mcp/
      server.py             FastMCP 서버 (evaluate_cover_letter, search_examples)
    web/
      styles.py             Streamlit CSS
      components.py         렌더링 함수, 결과 요약 빌더
      archive.py            HTML 아카이브 생성
    specialists/            ADK sub_agent 정의 (추후 확장용)
  hirelens_app.py           Streamlit 메인 진입점
data/
  reference/                정적 참조 데이터 (KRX 상장사 CSV)
  runtime/                  실행 중 자동 생성 (SQLite DB, Chroma 벡터 저장소)
configs/                    설정 파일
```


## 환경 설정

### 필수 환경 변수

프로젝트 루트에 `.env` 파일을 생성하고 다음 키를 설정해 주세요.

```
GOOGLE_API_KEY=...    # ADK 에이전트용
OPENAI_API_KEY=...    # LangChain 평가 + 임베딩용
```

### 선택 환경 변수

```
ADK_MODEL=gemini-2.5-flash   # ADK 에이전트 모델 (기본값: gemini-2.5-flash)
```

### 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```


## 실행

### Streamlit (평가 리포트)

```bash
streamlit run src/hirelens_app.py
```

자소서와 모집공고를 입력하면 3인 평가 -> 협상 -> 최종 판정 -> 면접 질문 예상까지 한 번에 수행됩니다. 결과는 요약, 수정안, 평가 기록, 면접 질문, 회사 분석 탭으로 나뉘어 표시됩니다.

### ADK (코칭 에이전트)

```bash
adk web src
```

에이전트 목록에서 `hirelens`를 선택한 뒤, Streamlit에서 발급된 세션 ID를 입력하면 평가 결과가 자동으로 로드됩니다. 이후 자소서 수정 코칭, 면접 질문 답변 연습, 수정본 재평가를 대화 형태로 이어갈 수 있습니다.


## 기술 스택

| 구분 | 기술 |
|------|------|
| 평가 엔진 | LangChain, LangGraph, OpenAI GPT-4.1 |
| 임베딩 | OpenAI text-embedding-3-small |
| 벡터 저장소 | Chroma |
| 코칭 에이전트 | Google ADK, Gemini 2.5 Flash |
| 도구 연동 | FastMCP (MCP 프로토콜) |
| 웹 UI | Streamlit |
| 데이터 저장 | SQLite |
