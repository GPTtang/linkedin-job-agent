from pathlib import Path
import json
from ..db import get_conn
from ..utils import dumps
from ..config import MUST_SKILLS, NICE_SKILLS


def import_jobs(file_path: str) -> int:
    try:
        raw = Path(file_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"文件不存在：{file_path}")
    except OSError as e:
        raise OSError(f"读取文件失败：{e}")

    try:
        items = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 格式错误：{e}")

    if not isinstance(items, list):
        raise ValueError("JSON 文件应为数组格式")

    conn = get_conn()
    try:
        cur = conn.cursor()
        count = 0
        for item in items:
            source_url = item.get("source_url", "")
            if source_url:
                cur.execute("SELECT id FROM jobs WHERE source_url = ?", (source_url,))
                if cur.fetchone():
                    continue  # 跳过重复
            cur.execute("""
                INSERT INTO jobs (
                    source, source_url, title, company, location, raw_text, parsed_json, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get("source", "linkedin"),
                source_url,
                item.get("title", ""),
                item.get("company", ""),
                item.get("location", ""),
                item.get("raw_text", ""),
                dumps({}),
                item.get("status", "saved"),
            ))
            count += 1
        conn.commit()
    finally:
        conn.close()
    return count


def list_jobs():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, title, company, location, status FROM jobs ORDER BY id DESC")
        rows = cur.fetchall()
    finally:
        conn.close()
    return rows


def get_job(job_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cur.fetchone()
    finally:
        conn.close()
    return row


def analyze_job(job_id: int):
    row = get_job(job_id)
    if not row:
        return None

    text = (row["raw_text"] or "").lower()

    required_skills = [s for s in MUST_SKILLS if s in text]
    preferred_skills = [s for s in NICE_SKILLS if s in text]

    languages = []
    if "japanese" in text or "日本語" in text or "日语" in text:
        languages.append("Japanese")
    if "english" in text or "英語" in text or "英语" in text:
        languages.append("English")

    years_required = None
    import re
    match = re.search(r"(\d+)\+?\s*years?", text)
    if match:
        years_required = int(match.group(1))

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
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE jobs SET parsed_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (dumps(parsed), job_id),
        )
        conn.commit()
    finally:
        conn.close()
    return parsed


def analyze_all_jobs():
    rows = list_jobs()
    results = []
    for row in rows:
        parsed = analyze_job(row["id"])
        results.append({"id": row["id"], "title": row["title"], "parsed": parsed})
    return results
