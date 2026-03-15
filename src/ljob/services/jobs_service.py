from pathlib import Path
import json
from ..db import get_conn
from ..utils import dumps


def import_jobs(file_path: str) -> int:
    raw = Path(file_path).read_text(encoding="utf-8")
    items = json.loads(raw)

    conn = get_conn()
    cur = conn.cursor()

    count = 0
    for item in items:
        cur.execute("""
            INSERT INTO jobs (
                source, source_url, title, company, location, raw_text, parsed_json, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get("source", "linkedin"),
            item.get("source_url", ""),
            item.get("title", ""),
            item.get("company", ""),
            item.get("location", ""),
            item.get("raw_text", ""),
            dumps({}),
            item.get("status", "saved"),
        ))
        count += 1

    conn.commit()
    conn.close()
    return count


def list_jobs():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, company, location, status FROM jobs ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_job(job_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = cur.fetchone()
    conn.close()
    return row


def analyze_job(job_id: int):
    row = get_job(job_id)
    if not row:
        return None

    text = (row["raw_text"] or "").lower()

    required_skills = []
    preferred_skills = []

    must_pool = ["python", "java", "sql", "docker", "kubernetes", "aws", "azure", "react", "typescript", "ai", "llm"]
    nice_pool = ["mcp", "agent", "redis", "graphql", "gcp"]

    for s in must_pool:
        if s in text:
            required_skills.append(s)

    for s in nice_pool:
        if s in text:
            preferred_skills.append(s)

    languages = []
    if "japanese" in text or "日本語" in text:
        languages.append("Japanese")
    if "english" in text or "英語" in text:
        languages.append("English")

    years_required = None
    for n in range(1, 11):
        if f"{n} years" in text or f"{n}+ years" in text:
            years_required = n
            break

    summary = f"{row['title']} @ {row['company']}，地点：{row['location']}"
    risks = []
    if "visa" in text:
        risks.append("需要确认签证支持")
    if "native japanese" in text:
        risks.append("可能要求高阶日语")

    parsed = {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "language_requirements": languages,
        "years_required": years_required,
        "summary": summary,
        "risks": risks,
    }

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE jobs SET parsed_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (dumps(parsed), job_id),
    )
    conn.commit()
    conn.close()
    return parsed


def analyze_all_jobs():
    rows = list_jobs()
    results = []
    for row in rows:
        results.append((row["id"], analyze_job(row["id"])))
    return results
