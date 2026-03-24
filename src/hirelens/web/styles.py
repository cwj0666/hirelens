import streamlit as st


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --font-body: "SUIT Variable", "Pretendard Variable", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(224, 242, 254, 0.9), transparent 28%),
                radial-gradient(circle at top right, rgba(254, 240, 138, 0.45), transparent 24%),
            linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
            font-family: var(--font-body);
        }
        .stApp p,
        .stApp label,
        .stApp button,
        .stApp input,
        .stApp textarea,
        .stApp li {
            font-family: var(--font-body);
        }
        .stApp code,
        .stApp pre {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace !important;
        }
        .material-symbols-rounded,
        .material-symbols-outlined,
        .material-icons {
            font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
            font-style: normal !important;
            font-weight: normal !important;
        }
        .main .block-container {
            padding-top: 2.2rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }
        .main .block-container [data-testid="stHorizontalBlock"] {
            gap: 1rem;
        }
        .hero-panel {
            padding: 2rem 2.1rem;
            border-radius: 24px;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 55%, #334155 100%);
            color: #f8fafc;
            border: 1px solid rgba(148, 163, 184, 0.22);
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
        .section-title {
            font-family: var(--font-body);
            font-size: 1.26rem;
            font-weight: 850;
            letter-spacing: -0.015em;
            color: #0f172a;
            margin-bottom: 0.35rem;
        }
        .section-copy {
            color: #475569;
            margin-bottom: 0.65rem;
            font-size: 0.92rem;
        }
        .section-copy:empty {
            display: none;
        }
        .workspace-banner {
            padding: 0.95rem 1.1rem;
            border-radius: 22px;
            background: rgba(255,255,255,0.88);
            border: 1px solid rgba(148, 163, 184, 0.16);
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
            margin-bottom: 0.9rem;
        }
        .workspace-banner-compact {
            margin-bottom: 0;
        }
        .workspace-banner-title {
            color: #0f172a;
            font-size: 1rem;
            font-weight: 900;
            margin-bottom: 0;
        }
        .role-title {
            color: #0f172a;
            font-weight: 800;
            font-size: 1rem;
            margin-bottom: 0.3rem;
        }
        .surface-card {
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 16px;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
            padding: 1rem 1.05rem;
            margin-bottom: 0.9rem;
        }
        .surface-card-title {
            font-family: var(--font-body);
            color: #0f172a;
            font-size: 1.06rem;
            font-weight: 820;
            letter-spacing: -0.01em;
            margin-bottom: 0.55rem;
        }
        .surface-card-body > *:first-child {
            margin-top: 0;
        }
        .surface-card-body > *:last-child {
            margin-bottom: 0;
        }
        .toolbar-card {
            margin-bottom: 0.55rem;
        }
        .toolbar-copy {
            margin-bottom: 0;
        }
        .surface-copy {
            color: #334155;
            font-size: 0.95rem;
            line-height: 1.78;
            margin-bottom: 0.75rem;
        }
        .surface-split {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.9rem;
            margin-top: 0.55rem;
        }
        .surface-subtitle {
            color: #475569;
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }
        .surface-list {
            margin: 0;
            padding-left: 1rem;
            color: #0f172a;
        }
        .surface-list li {
            margin-bottom: 0.35rem;
            line-height: 1.62;
            font-size: 0.93rem;
        }
        .surface-empty {
            color: #64748b;
            font-size: 0.9rem;
            line-height: 1.5;
        }
        .surface-meta-line {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            flex-wrap: wrap;
            margin-bottom: 0.65rem;
        }
        .status-banner {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.38rem 0.8rem;
            font-size: 0.82rem;
            font-weight: 900;
            margin-bottom: 0.9rem;
        }
        .status-banner-pass {
            background: #dcfce7;
            color: #166534;
        }
        .status-banner-hold {
            background: #ffedd5;
            color: #9a3412;
        }
        .status-banner-fail {
            background: #fee2e2;
            color: #991b1b;
        }
        .decision-chip {
            display: inline-block;
            border-radius: 999px;
            padding: 0.24rem 0.7rem;
            font-size: 0.82rem;
            font-weight: 800;
            margin-right: 0.45rem;
        }
        .decision-pass {
            background: #dcfce7;
            color: #166534;
        }
        .decision-hold {
            background: #ffedd5;
            color: #9a3412;
        }
        .decision-fail {
            background: #fee2e2;
            color: #991b1b;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.12);
            border-radius: 16px;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.035);
        }
        .score-text {
            color: #334155;
            font-weight: 700;
        }
        [data-testid="stSidebar"] {
            background:
                radial-gradient(circle at top, rgba(59, 130, 246, 0.16), transparent 22%),
                linear-gradient(180deg, #0f172a 0%, #172033 100%);
            border-right: 1px solid rgba(148, 163, 184, 0.16);
        }
        [data-testid="stSidebar"] .block-container {
            padding-top: 1.2rem;
            padding-bottom: 1.8rem;
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .st-emotion-cache-10trblm,
        [data-testid="stSidebar"] .st-emotion-cache-16idsys {
            color: #e2e8f0;
        }
        [data-testid="stSidebar"] div[data-testid="stTextArea"],
        [data-testid="stSidebar"] div[data-testid="stSelectbox"],
        [data-testid="stSidebar"] div[data-testid="stNumberInput"],
        [data-testid="stSidebar"] div[data-testid="stFileUploader"],
        [data-testid="stSidebar"] div[data-testid="stSlider"],
        [data-testid="stSidebar"] div[data-testid="stRadio"] {
            background: transparent;
            border-radius: 0;
            padding: 0;
            margin-bottom: 0.28rem;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] > div,
        [data-testid="stSidebar"] [data-testid="stNumberInput"] > div {
            color: #f8fafc;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] textarea {
            min-height: 2.65rem;
            border-radius: 12px;
            font-size: 1rem;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: rgba(255, 255, 255, 0.96);
            padding-left: 0.2rem;
            padding-right: 0.2rem;
        }
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] textarea {
            background: rgba(255, 255, 255, 0.96);
            padding-top: 0.45rem;
            padding-bottom: 0.45rem;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] span,
        [data-testid="stSidebar"] input::placeholder,
        [data-testid="stSidebar"] textarea::placeholder {
            font-size: 1rem;
        }
        [data-testid="stSidebar"] label p {
            font-size: 0.98rem;
        }
        [data-testid="stSidebar"] [data-testid="stSlider"] > div {
            padding-left: 0.15rem;
            padding-right: 0.15rem;
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] {
            border: none;
            background: transparent;
            box-shadow: none;
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] details {
            border: none;
            background: transparent;
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] summary {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 14px;
            padding: 0.55rem 0.7rem;
            color: #f8fafc;
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] details[open] summary {
            margin-bottom: 0.7rem;
            background: rgba(255, 255, 255, 0.10);
        }
        [data-testid="stSidebar"] [data-testid="stExpanderDetails"] {
            background: transparent;
            border: none;
            padding: 0 0.12rem;
        }
        .sidebar-panel {
            padding: 0 0 0.8rem;
            background: transparent;
            border: none;
            box-shadow: none;
            margin-bottom: 0.6rem;
        }
        .sidebar-brand {
            font-size: 0.76rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #93c5fd;
            font-weight: 800;
        }
        .sidebar-pill-row {
            display: flex;
            gap: 0.4rem;
            flex-wrap: wrap;
        }
        .sidebar-pill {
            display: inline-block;
            padding: 0.24rem 0.58rem;
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 800;
        }
        .sidebar-pill-ready {
            background: rgba(34, 197, 94, 0.18);
            color: #bbf7d0;
            border: 1px solid rgba(34, 197, 94, 0.25);
        }
        .sidebar-pill-warn {
            background: rgba(251, 191, 36, 0.16);
            color: #fde68a;
            border: 1px solid rgba(251, 191, 36, 0.22);
        }
        .sidebar-section-copy {
            color: #94a3b8;
            font-size: 0.82rem;
            margin-bottom: 0.85rem;
            line-height: 1.45;
        }
        .sidebar-model-note {
            color: #93c5fd;
            font-size: 0.78rem;
            line-height: 1.5;
            margin-top: -0.15rem;
            margin-bottom: 0.7rem;
        }
        .stButton > button, div[data-testid="stFormSubmitButton"] > button {
            border-radius: 14px;
            border: 1px solid rgba(15, 23, 42, 0.08);
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
            font-weight: 700;
            min-height: 2.9rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 16px;
            padding: 0.8rem 0.9rem;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
        }
        .result-summary-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.9rem;
            margin-bottom: 0.9rem;
        }
        .result-summary-card {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 16px;
            padding: 0.95rem 1rem;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
        }
        .result-summary-label {
            color: #475569;
            font-size: 0.9rem;
            font-weight: 780;
            letter-spacing: -0.01em;
            margin-bottom: 0.32rem;
        }
        .result-summary-value {
            color: #0f172a;
            font-family: var(--font-body);
            font-size: 1.08rem;
            font-weight: 820;
            letter-spacing: -0.01em;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.7rem;
        }
        .info-grid-item {
            background: rgba(248, 250, 252, 0.92);
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 14px;
            padding: 0.8rem 0.9rem;
        }
        .info-grid-label {
            color: #64748b;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            margin-bottom: 0.28rem;
        }
        .info-grid-value {
            color: #0f172a;
            font-size: 0.98rem;
            font-weight: 760;
            line-height: 1.55;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        .result-hero-card {
            padding: 1.55rem 1.65rem;
            border-radius: 24px;
            background:
                radial-gradient(circle at top right, rgba(186, 230, 253, 0.7), transparent 26%),
                linear-gradient(135deg, rgba(255,255,255,0.98), rgba(239,246,255,0.94));
            border: 1px solid rgba(125, 211, 252, 0.24);
            box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
            margin-bottom: 1rem;
            margin-top: 0.55rem;
        }
        .result-hero-card-clean {
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
            background: rgba(255, 255, 255, 0.86);
        }
        .result-hero-eyebrow {
            font-size: 0.8rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #2563eb;
            font-weight: 800;
            margin-bottom: 0.55rem;
        }
        .result-hero-line {
            display: flex;
            gap: 0.65rem;
            align-items: center;
            flex-wrap: wrap;
            margin-bottom: 0.7rem;
        }
        .result-hero-meta {
            color: #475569;
            font-weight: 700;
        }
        .result-hero-copy {
            color: #0f172a;
            line-height: 1.82;
            font-size: 1.04rem;
            font-weight: 580;
        }
        .main h4 {
            font-family: var(--font-body);
            font-size: 1.06rem;
            font-weight: 820;
            letter-spacing: -0.01em;
            color: #0f172a;
        }
        [data-testid="stTabs"] {
            margin-top: 0.55rem;
        }
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 0.35rem;
            background: rgba(255, 255, 255, 0.74);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 18px;
            padding: 0.35rem;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
        }
        [data-testid="stTabs"] [data-baseweb="tab"] {
            height: 2.7rem;
            border-radius: 14px;
            font-weight: 800;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        [data-testid="stTabs"] [aria-selected="true"] {
            background: linear-gradient(135deg, #0f172a, #1d4ed8);
            color: #f8fafc;
        }
        [data-testid="stTabs"] [data-baseweb="tab-panel"] {
            padding-top: 1.05rem;
        }
        [data-testid="stExpander"] details {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 16px;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.03);
        }
        [data-testid="stExpander"] summary {
            border-radius: 16px;
            padding: 0.35rem 0.75rem;
        }
        [data-testid="stExpanderDetails"] {
            padding: 0.2rem 0.8rem 0.8rem;
        }
        .news-source-card {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 16px;
            padding: 1rem 1.05rem;
            margin-bottom: 0.8rem;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        .news-source-title {
            color: #0f172a;
            font-family: var(--font-body);
            font-size: 1rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
            line-height: 1.5;
        }
        .news-source-meta {
            color: #64748b;
            font-size: 0.88rem;
            margin-bottom: 0.55rem;
        }
        .news-source-copy {
            color: #334155;
            line-height: 1.6;
            margin-bottom: 0.7rem;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        .news-source-link {
            display: inline-flex;
            align-items: center;
            padding: 0.42rem 0.75rem;
            border-radius: 999px;
            background: #e0f2fe;
            color: #075985 !important;
            font-weight: 800;
            text-decoration: none;
        }
        .stCodeBlock, [data-testid="stCodeBlock"] {
            border-radius: 14px;
        }
        div[data-testid="stTextArea"], div[data-testid="stSelectbox"], div[data-testid="stNumberInput"],
        div[data-testid="stFileUploader"], div[data-testid="stSlider"], div[data-testid="stRadio"] {
            background: rgba(255, 255, 255, 0.74);
            border-radius: 14px;
        }
        .input-card-title {
            font-family: var(--font-body);
            font-size: 1.04rem;
            font-weight: 800;
            letter-spacing: -0.01em;
            color: #0f172a;
            margin-bottom: 0.45rem;
        }
        .input-card-title-tight {
            margin-top: 0.9rem;
        }
        .input-card-copy {
            color: #475569;
            margin-bottom: 1rem;
        }
        .input-card-copy:empty {
            display: none;
        }
        @media (max-width: 900px) {
            .result-summary-grid,
            .info-grid,
            .surface-split {
                grid-template-columns: 1fr;
            }
        }
        .main div[data-testid="stRadio"] {
            margin-bottom: 0.25rem;
        }
        .main div[data-testid="stRadio"] [role="radiogroup"] {
            background: transparent;
            border: none;
            border-radius: 0;
            padding: 0.15rem 0;
            gap: 0.9rem;
            min-height: auto;
        }
        .main div[data-testid="stRadio"] [role="radiogroup"] > label {
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 999px;
            padding: 1rem 1.45rem;
            min-height: 3.6rem;
            min-width: 9.5rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .main div[data-testid="stRadio"] [role="radiogroup"] > label p {
            font-size: 1rem;
            line-height: 1.3;
        }
        .main div[data-testid="stTextArea"] textarea {
            min-height: 20rem;
            font-size: 1.03rem;
            line-height: 1.72;
            border-radius: 20px;
            padding: 1.2rem 1.2rem 1.25rem;
            background: rgba(255, 255, 255, 0.97);
            border: 1px solid rgba(148, 163, 184, 0.20);
        }
        .main div[data-testid="stFileUploader"] section {
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.20);
            background: rgba(255, 255, 255, 0.97);
            padding: 1.1rem;
        }
        @media (max-width: 900px) {
            .hero-title {
                font-size: 1.6rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
