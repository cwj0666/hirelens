import json
import logging
import os

import streamlit as st
import streamlit.components.v1 as st_components
import st_yled as styled
from dotenv import load_dotenv

from hirelens.evaluation.models import (
    DEFAULT_MAX_ROUNDS,
    DEFAULT_TEMPERATURE,
    DEFAULT_WEIGHTS,
    OPENAI_MODEL_OPTIONS,
    RAG_APPROVED_RESULT,
    SUPPORTED_FILE_ENCODINGS,
    NegotiationState,
)
from hirelens.evaluation.storage import (
    format_retrieved_examples,
    get_retriever,
    init_db,
    save_session,
)
from hirelens.evaluation.workflow import build_graph, configure_llm
from hirelens.tools.company_tools import get_code, get_company_info
from hirelens.tools.news_tools import get_company_news_report
from hirelens.web.archive import (
    build_news_archive_html,
    build_result_archive_html,
    make_archive_filename,
    make_news_archive_filename,
)
from hirelens.web.components import (
    RESULT_SECTION_OPTIONS,
    render_hero,
    render_model_note,
    render_results,
    render_section_header,
    render_sidebar_intro,
)
from hirelens.web.styles import inject_styles

logger = logging.getLogger(__name__)

load_dotenv()


def decode_uploaded_text(uploaded_file) -> str:
    raw = uploaded_file.read()
    for enc in SUPPORTED_FILE_ENCODINGS:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def set_session_value(key: str, value: str) -> None:
    st.session_state[key] = value


SCROLL_TO_TOP_JS = "<script>window.parent.document.querySelector('section.main').scrollTo(0,0);</script>"


def ensure_defaults() -> None:
    defaults = {
        "career_level": "자동",
        "posting_method": "직접 입력",
        "letter_method": "직접 입력",
        "workspace_tab": "입력",
        "scroll_to_top": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def render_input_intro(has_result: bool) -> None:
    if has_result:
        st.caption("새 분석을 실행하면 이전 결과를 덮어씁니다.")


def render_sidebar() -> tuple[str, float, int, bool, dict[str, float]]:
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_google = bool(os.getenv("GOOGLE_API_KEY"))
    render_sidebar_intro(has_openai, has_google)

    with st.sidebar.expander("모델 설정", expanded=False):
        selected_model = st.selectbox(
            "기본 모델",
            OPENAI_MODEL_OPTIONS,
            index=0,
        )
        render_model_note(selected_model)
        custom_model_name = st.text_input("모델 ID 입력", value="")
        model_name = custom_model_name.strip() or selected_model
        st.caption(f"현재 적용 모델: `{model_name}`")
        temperature = st.slider("응답 다양성", 0.0, 1.0, DEFAULT_TEMPERATURE, 0.1)
        max_rounds = st.slider("최대 협상 라운드", 1, 5, DEFAULT_MAX_ROUNDS)

    with st.sidebar.expander("평가자 가중치", expanded=False):
        hr_weight = st.slider("HR 담당자", 0.1, 0.6, DEFAULT_WEIGHTS["hr"], 0.05)
        dept_weight = st.slider("현업 부서장", 0.1, 0.6, DEFAULT_WEIGHTS["dept_head"], 0.05)
        talent_weight = st.slider("인재개발팀", 0.1, 0.6, DEFAULT_WEIGHTS["talent_dev"], 0.05)

    total_weight = hr_weight + dept_weight + talent_weight
    weights_valid = abs(total_weight - 1.0) <= 0.01
    weights = {
        "hr": hr_weight,
        "dept_head": dept_weight,
        "talent_dev": talent_weight,
    }

    return model_name, temperature, max_rounds, weights_valid, weights


def render_input_screen(weights_valid: bool) -> tuple[bool, dict]:
    with st.container(border=True):
        st.markdown(
            '<div class="input-card-title">회사명</div>',
            unsafe_allow_html=True,
        )
        company_name = st.text_input(
            "회사명",
            key="company_name_input",
            label_visibility="collapsed",
        )

    with st.container(border=True):
        st.markdown(
            '<div class="input-card-title">경력 수준</div>',
            unsafe_allow_html=True,
        )
        cl1, cl2, cl3 = st.columns(3)
        with cl1:
            st.button(
                "자동",
                key="career_auto",
                use_container_width=True,
                type="primary" if st.session_state["career_level"] == "자동" else "secondary",
                on_click=set_session_value,
                args=("career_level", "자동"),
            )
        with cl2:
            st.button(
                "신입",
                key="career_entry",
                use_container_width=True,
                type="primary" if st.session_state["career_level"] == "신입" else "secondary",
                on_click=set_session_value,
                args=("career_level", "신입"),
            )
        with cl3:
            st.button(
                "경력",
                key="career_exp",
                use_container_width=True,
                type="primary" if st.session_state["career_level"] == "경력" else "secondary",
                on_click=set_session_value,
                args=("career_level", "경력"),
            )

    col_posting, col_letter = st.columns(2)

    with col_posting:
        with st.container(border=True):
            st.markdown('<div class="input-card-title">모집공고</div>', unsafe_allow_html=True)
            pc1, pc2 = st.columns(2)
            with pc1:
                st.button(
                    "직접 입력",
                    key="posting_direct",
                    use_container_width=True,
                    type="primary" if st.session_state["posting_method"] == "직접 입력" else "secondary",
                    on_click=set_session_value,
                    args=("posting_method", "직접 입력"),
                )
            with pc2:
                st.button(
                    "파일 업로드",
                    key="posting_file_btn",
                    use_container_width=True,
                    type="primary" if st.session_state["posting_method"] == "파일 업로드" else "secondary",
                    on_click=set_session_value,
                    args=("posting_method", "파일 업로드"),
                )

        with st.container(border=True):
            if st.session_state["posting_method"] == "직접 입력":
                st.markdown('<div class="input-card-title">본문</div>', unsafe_allow_html=True)
                job_posting = st.text_area(
                    "모집공고 내용",
                    key="job_posting_input",
                    height=220,
                    placeholder="모집공고 전문을 붙여넣어주세요.",
                    label_visibility="collapsed",
                )
            else:
                st.markdown('<div class="input-card-title">파일 업로드</div>', unsafe_allow_html=True)
                posting_file = st.file_uploader(
                    "모집공고 파일",
                    type=["txt"],
                    key="posting_file",
                    label_visibility="collapsed",
                )
                job_posting = decode_uploaded_text(posting_file) if posting_file else ""

    with col_letter:
        with st.container(border=True):
            st.markdown('<div class="input-card-title">자기소개서</div>', unsafe_allow_html=True)
            lc1, lc2 = st.columns(2)
            with lc1:
                st.button(
                    "직접 입력",
                    key="letter_direct",
                    use_container_width=True,
                    type="primary" if st.session_state["letter_method"] == "직접 입력" else "secondary",
                    on_click=set_session_value,
                    args=("letter_method", "직접 입력"),
                )
            with lc2:
                st.button(
                    "파일 업로드",
                    key="letter_file_btn",
                    use_container_width=True,
                    type="primary" if st.session_state["letter_method"] == "파일 업로드" else "secondary",
                    on_click=set_session_value,
                    args=("letter_method", "파일 업로드"),
                )

        with st.container(border=True):
            if st.session_state["letter_method"] == "직접 입력":
                st.markdown('<div class="input-card-title">본문</div>', unsafe_allow_html=True)
                cover_letter = st.text_area(
                    "자기소개서 내용",
                    key="cover_letter_input",
                    height=220,
                    placeholder="자기소개서 전문을 붙여넣어주세요.",
                    label_visibility="collapsed",
                )
            else:
                st.markdown('<div class="input-card-title">파일 업로드</div>', unsafe_allow_html=True)
                letter_file = st.file_uploader(
                    "자기소개서 파일",
                    type=["txt"],
                    key="letter_file",
                    label_visibility="collapsed",
                )
                cover_letter = decode_uploaded_text(letter_file) if letter_file else ""

    with st.container(border=True):
        if not weights_valid:
            st.warning("평가자 가중치 합계는 1.0이어야 합니다.")
        should_run = st.button(
            "분석 시작",
            type="primary",
            use_container_width=True,
            disabled=not cover_letter.strip() or not weights_valid,
        )

    return should_run, {
        "company_name": company_name.strip(),
        "career_level": st.session_state["career_level"],
        "job_posting": job_posting or "",
        "cover_letter": cover_letter.strip(),
    }


def run_analysis(
    company_name: str,
    career_level: str,
    job_posting: str,
    cover_letter: str,
    model_name: str,
    temperature: float,
    max_rounds: int,
    weights: dict[str, float] | None = None,
) -> dict:
    company_info = None
    company_news = ""
    company_news_report = {}

    if company_name:
        with st.spinner("회사 정보 조회 중..."):
            try:
                code_result = get_code(company_name)
                code_data = json.loads(code_result)
                short_codes = code_data.get("단축코드", {})
                if short_codes:
                    first_code = list(short_codes.values())[0]
                    company_info = get_company_info(str(first_code))
                else:
                    st.warning(f"'{company_name}'에 해당하는 종목을 찾을 수 없습니다.")
            except Exception as exc:
                st.warning(f"회사 정보 조회 실패: {exc}")

        with st.spinner("최근 뉴스를 가져오는 중..."):
            try:
                company_news_report = get_company_news_report(
                    company_name,
                    industry=(company_info or {}).get("업종", ""),
                    model_name=model_name,
                    temperature=min(temperature, 0.2),
                )
                company_news = company_news_report.get("briefing_text", "")
            except Exception:
                logger.warning("뉴스 수집 실패: %s", company_name, exc_info=True)

    configure_llm(
        model_name=model_name,
        temperature=temperature,
        weights=weights,
    )

    reference_text = ""
    rag_used = False
    with st.spinner("합격 사례를 검색하고 있습니다..."):
        init_db()
        retriever = get_retriever(
            industry=(company_info or {}).get("업종") or None,
            job_role=None,
            result=RAG_APPROVED_RESULT,
            k=3,
        )
        try:
            docs = retriever.invoke(cover_letter[:500])
            reference_text = format_retrieved_examples(docs)
            rag_used = bool(reference_text)
        except Exception:
            pass

    initial_state = NegotiationState(
        cover_letter=cover_letter,
        job_posting=job_posting or "모집공고 정보 없음",
        max_rounds=max_rounds,
        career_level=career_level,
        company_news=company_news,
        use_rag=rag_used,
        reference_examples=reference_text,
    )

    graph = build_graph(max_rounds=max_rounds)

    with st.spinner("평가자들이 자기소개서를 검토하고 있습니다..."):
        result = {}
        for event in graph.stream(initial_state, stream_mode="updates"):
            for _node_name, node_output in event.items():
                for key, value in node_output.items():
                    if key in result and isinstance(result[key], list):
                        result[key].extend(value)
                    else:
                        result[key] = value

    result["_cover_letter"] = cover_letter
    result["_reference_text"] = reference_text
    result["_company_info"] = company_info
    result["_company_news"] = company_news
    result["_company_news_report"] = company_news_report
    result["_job_posting"] = job_posting
    session_id = save_session(result, company_name=company_name)
    result["_session_id"] = session_id
    return result


def render_result_toolbar(result: dict) -> None:
    session_id = result.get("_session_id", "")
    news_report = result.get("_company_news_report", {})
    result_archive_html = build_result_archive_html(result)
    with st.container(border=True):
        st.html('<div class="input-card-title">세션 코드 및 저장</div>')
        if session_id:
            st.code(session_id)
        button_col1, button_col2 = st.columns(2)
        with button_col1:
            st.download_button(
                "결과 저장",
                data=result_archive_html,
                file_name=make_archive_filename(),
                mime="text/html",
                use_container_width=True,
            )
        with button_col2:
            if news_report:
                news_archive_html = build_news_archive_html(news_report)
                st.download_button(
                    "뉴스 저장",
                    data=news_archive_html,
                    file_name=make_news_archive_filename(),
                    mime="text/html",
                    use_container_width=True,
                )
            else:
                st.button("뉴스 저장", use_container_width=True, disabled=True)


def render_result_screen(result: dict) -> None:
    section_tabs = styled.tabs(list(RESULT_SECTION_OPTIONS), key="result-section-tabs")
    for tab, section_name in zip(section_tabs, RESULT_SECTION_OPTIONS, strict=False):
        with tab:
            render_results(result, active_section=section_name)
    render_result_toolbar(result)
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        if st.button("입력으로 돌아가기", use_container_width=True, key="back_to_input_bottom"):
            st.session_state["workspace_tab"] = "입력"
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="자소서 최적화 에이전트", layout="wide")
    styled.init(reset_tracebacklimit=False)
    inject_styles()
    ensure_defaults()
    render_hero()

    model_name, temperature, max_rounds, weights_valid, weights = render_sidebar()
    workspace_tab = st.session_state["workspace_tab"]

    if workspace_tab == "결과":
        if st.session_state.get("scroll_to_top"):
            st_components.html(SCROLL_TO_TOP_JS, height=0)
            st.session_state["scroll_to_top"] = False
        if "result" in st.session_state:
            render_result_screen(st.session_state["result"])
        else:
            render_section_header(
                "결과",
                "아직 생성된 평가 결과가 없습니다. 입력 화면에서 먼저 분석을 실행하세요.",
            )
            with st.container(border=True):
                st.caption("입력 화면으로 이동한 뒤 회사명, 모집공고, 자기소개서를 넣고 분석을 시작하면 결과 탭으로 자동 전환됩니다.")
                if st.button("입력 화면으로 이동", use_container_width=True):
                    st.session_state["workspace_tab"] = "입력"
                    st.rerun()
    else:
        render_input_intro(has_result="result" in st.session_state)
        should_run, input_data = render_input_screen(weights_valid=weights_valid)

        if should_run:
            try:
                result = run_analysis(
                    company_name=input_data["company_name"],
                    career_level=input_data["career_level"],
                    job_posting=input_data["job_posting"],
                    cover_letter=input_data["cover_letter"],
                    model_name=model_name,
                    temperature=temperature,
                    max_rounds=max_rounds,
                    weights=weights,
                )
            except Exception as exc:
                st.session_state.pop("result", None)
                st.error("평가 실행 중 오류가 발생했습니다. API 키, 네트워크, 모델 설정을 확인하세요.")
                with st.expander("오류 상세"):
                    st.code(f"{type(exc).__name__}: {exc}")
            else:
                st.session_state["result"] = result
                st.session_state["workspace_tab"] = "결과"
                st.session_state["scroll_to_top"] = True
                st.rerun()


if __name__ == "__main__":
    main()
