import json
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from hirelens.evaluation.models import EVALUATOR_ROLES, EvaluatorOutput

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RUNTIME_DIR = DATA_DIR / "runtime"
DB_PATH = RUNTIME_DIR / "cover_letters.db"
CHROMA_DIR = str(RUNTIME_DIR / "chroma" / "cover_letters")
COLLECTION_NAME = "cover_letter_examples"
EMBED_MODEL = "text-embedding-3-small"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)
    conn = _get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cover_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            industry TEXT NOT NULL,
            job_role TEXT NOT NULL,
            company TEXT DEFAULT '',
            result TEXT NOT NULL,
            score REAL DEFAULT 0.0,
            strengths TEXT DEFAULT '[]',
            weaknesses TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluation_sessions (
            session_id TEXT PRIMARY KEY,
            company_name TEXT DEFAULT '',
            final_decision TEXT DEFAULT '',
            final_score REAL DEFAULT 0.0,
            result_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            query_text TEXT DEFAULT '',
            title TEXT NOT NULL,
            source TEXT DEFAULT '',
            domain TEXT DEFAULT '',
            url TEXT DEFAULT '',
            date TEXT DEFAULT '',
            description TEXT DEFAULT '',
            topic TEXT DEFAULT '',
            theme TEXT DEFAULT '',
            relevance TEXT DEFAULT '',
            keep_flag INTEGER DEFAULT 0,
            reason TEXT DEFAULT '',
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(company_name, title, source, date)
        )
        """,
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS news_briefs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            report_json TEXT NOT NULL,
            article_count INTEGER DEFAULT 0,
            relevant_article_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
    )
    conn.commit()
    conn.close()


def add_example(
    text: str,
    industry: str,
    job_role: str,
    result: str,
    company: str = "",
    score: float = 0.0,
    strengths: list[str] | None = None,
    weaknesses: list[str] | None = None,
) -> int:
    strengths = strengths or []
    weaknesses = weaknesses or []

    conn = _get_conn()
    cursor = conn.execute(
        """
        INSERT INTO cover_letters (text, industry, job_role, company, result, score, strengths, weaknesses)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            text,
            industry,
            job_role,
            company,
            result,
            score,
            json.dumps(strengths, ensure_ascii=False),
            json.dumps(weaknesses, ensure_ascii=False),
        ),
    )
    example_id = cursor.lastrowid
    conn.commit()
    conn.close()

    try:
        vectorstore = _get_vectorstore()
        doc = Document(
            page_content=text,
            metadata={
                "id": example_id,
                "industry": industry,
                "job_role": job_role,
                "result": result,
                "company": company,
                "score": score,
            },
        )
        vectorstore.add_documents([doc], ids=[str(example_id)])
    except Exception:
        cleanup_conn = _get_conn()
        cleanup_conn.execute("DELETE FROM cover_letters WHERE id = ?", (example_id,))
        cleanup_conn.commit()
        cleanup_conn.close()
        raise

    return example_id


def delete_example(example_id: int) -> None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT id FROM cover_letters WHERE id = ?",
        (example_id,),
    ).fetchone()
    if row is None:
        conn.close()
        raise ValueError(f"사례 #{example_id}를 찾을 수 없습니다.")

    conn.execute("DELETE FROM cover_letters WHERE id = ?", (example_id,))
    conn.commit()
    conn.close()

    vectorstore = _get_vectorstore()
    vectorstore.delete(ids=[str(example_id)])


def list_examples(
    industry: str | None = None,
    job_role: str | None = None,
) -> list[dict]:
    conn = _get_conn()
    query = "SELECT * FROM cover_letters WHERE 1=1"
    params = []

    if industry:
        query += " AND industry = ?"
        params.append(industry)
    if job_role:
        query += " AND job_role = ?"
        params.append(job_role)

    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = []
    for row in rows:
        data = dict(row)
        data["strengths"] = json.loads(data["strengths"])
        data["weaknesses"] = json.loads(data["weaknesses"])
        results.append(data)
    return results


def get_distinct_values(column: str) -> list[str]:
    allowed = {"industry", "job_role", "company", "result"}
    if column not in allowed:
        raise ValueError(f"허용되지 않은 컬럼: {column}")

    conn = _get_conn()
    rows = conn.execute(
        f"SELECT DISTINCT {column} FROM cover_letters ORDER BY {column}",
    ).fetchall()
    conn.close()
    return [row[0] for row in rows if row[0]]


def count_examples() -> int:
    conn = _get_conn()
    count = conn.execute("SELECT COUNT(*) FROM cover_letters").fetchone()[0]
    conn.close()
    return count


def _get_vectorstore() -> Chroma:
    embedding = OpenAIEmbeddings(model=EMBED_MODEL)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding,
        persist_directory=CHROMA_DIR,
    )


def get_retriever(
    industry: str | None = None,
    job_role: str | None = None,
    result: str | None = None,
    k: int = 3,
) -> Chroma:
    vectorstore = _get_vectorstore()

    search_kwargs = {"k": k}
    filter_conditions = {}

    if industry:
        filter_conditions["industry"] = industry
    if job_role:
        filter_conditions["job_role"] = job_role
    if result:
        filter_conditions["result"] = result

    if filter_conditions:
        search_kwargs["filter"] = filter_conditions

    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs=search_kwargs,
    )


def format_retrieved_examples(docs: list[Document]) -> str:
    if not docs:
        return ""

    parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        part = (
            f"### 사례 {i} ({meta.get('industry', '')}/{meta.get('job_role', '')})\n"
            f"- 결과: {meta.get('result', '')}, 점수: {meta.get('score', 0)}\n"
            f"- 내용 발췌:\n{doc.page_content[:500]}"
        )
        parts.append(part)

    return "\n\n".join(parts)


def to_serializable_result(result: dict) -> dict:
    """세션 state 저장용으로 EvaluatorOutput을 기본 타입으로 변환한다."""
    serializable = {}
    for key, value in result.items():
        if isinstance(value, list) and value and hasattr(value[0], "model_dump"):
            serializable[key] = [item.model_dump() for item in value]
        elif hasattr(value, "model_dump"):
            serializable[key] = value.model_dump()
        else:
            serializable[key] = value
    return serializable


def _serialize_result(result: dict) -> str:
    """EvaluatorOutput 리스트를 model_dump로 변환 후 JSON 직렬화."""
    return json.dumps(to_serializable_result(result), ensure_ascii=False)


def _deserialize_result(json_str: str) -> dict:
    """JSON에서 복원하고 평가자 리스트를 EvaluatorOutput으로 역직렬화."""
    data = json.loads(json_str)
    for role_key in EVALUATOR_ROLES:
        evals_key = f"{role_key}_evals"
        if evals_key in data and isinstance(data[evals_key], list):
            data[evals_key] = [EvaluatorOutput(**item) for item in data[evals_key]]
    return data


def generate_session_id() -> str:
    date_str = datetime.now().strftime("%Y%m%d")
    rand_hex = secrets.token_hex(2).upper()
    return f"HL-{date_str}-{rand_hex}"


def save_session(result: dict, company_name: str = "") -> str:
    """평가 결과를 DB에 저장하고 세션 ID를 반환한다."""
    init_db()
    session_id = generate_session_id()
    result_json = _serialize_result(result)
    final_decision = result.get("final_decision", "")
    final_score = result.get("final_score", 0.0)

    conn = _get_conn()
    conn.execute(
        """
        INSERT INTO evaluation_sessions (session_id, company_name, final_decision, final_score, result_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (session_id, company_name, final_decision, float(final_score), result_json),
    )
    conn.commit()
    conn.close()
    return session_id


def load_session(session_id: str) -> dict | None:
    """세션 ID로 평가 결과를 로드하고 EvaluatorOutput을 복원해 반환한다."""
    init_db()
    conn = _get_conn()
    row = conn.execute(
        "SELECT result_json FROM evaluation_sessions WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return _deserialize_result(row["result_json"])


def list_sessions(limit: int = 10) -> list[dict]:
    """최근 세션 목록을 반환한다."""
    init_db()
    conn = _get_conn()
    rows = conn.execute(
        """
        SELECT session_id, company_name, final_decision, final_score, created_at
        FROM evaluation_sessions
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_news_report(company_name: str, report: dict) -> int:
    """회사 뉴스 원문과 브리프를 DB에 저장한다."""
    init_db()

    articles = report.get("articles", [])
    article_count = int(report.get("article_count", len(articles)))
    relevant_count = int(report.get("relevant_article_count", 0))

    conn = _get_conn()
    for article in articles:
        conn.execute(
            """
            INSERT INTO news_articles (
                company_name, query_text, title, source, domain, url, date,
                description, topic, theme, relevance, keep_flag, reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(company_name, title, source, date) DO UPDATE SET
                query_text = excluded.query_text,
                domain = excluded.domain,
                url = excluded.url,
                description = excluded.description,
                topic = excluded.topic,
                theme = excluded.theme,
                relevance = excluded.relevance,
                keep_flag = excluded.keep_flag,
                reason = excluded.reason,
                fetched_at = CURRENT_TIMESTAMP
            """,
            (
                company_name,
                article.get("query_text", ""),
                article.get("title", ""),
                article.get("source", ""),
                article.get("domain", ""),
                article.get("url", ""),
                article.get("date", ""),
                article.get("description", ""),
                article.get("topic", ""),
                article.get("theme", ""),
                article.get("relevance", ""),
                1 if article.get("keep") else 0,
                article.get("reason", ""),
            ),
        )

    cursor = conn.execute(
        """
        INSERT INTO news_briefs (company_name, report_json, article_count, relevant_article_count)
        VALUES (?, ?, ?, ?)
        """,
        (
            company_name,
            json.dumps(report, ensure_ascii=False),
            article_count,
            relevant_count,
        ),
    )
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return int(report_id)


def load_recent_news_report(company_name: str, freshness_hours: int = 12) -> dict | None:
    """최근 생성된 뉴스 브리프 캐시를 반환한다."""
    init_db()
    conn = _get_conn()
    row = conn.execute(
        """
        SELECT report_json
        FROM news_briefs
        WHERE company_name = ?
          AND created_at >= datetime('now', ?)
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (company_name, f"-{freshness_hours} hours"),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return json.loads(row["report_json"])
