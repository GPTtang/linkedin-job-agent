from pathlib import Path
from ..db import get_conn
from ..utils import dumps, loads
from ..config import MUST_SKILLS, NICE_SKILLS


def import_profile_from_resume(file_path: str) -> None:
    try:
        text = Path(file_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"简历文件不存在：{file_path}")
    except OSError as e:
        raise OSError(f"读取简历文件失败：{e}")

    skills_pool = MUST_SKILLS + NICE_SKILLS
    found_skills = [s for s in skills_pool if s.lower() in text.lower()]

    languages = []
    text_lower = text.lower()
    if "japanese" in text_lower or "日语" in text or "日本語" in text:
        languages.append("Japanese")
    if "english" in text_lower or "英语" in text or "英語" in text:
        languages.append("English")
    if "中文" in text or "chinese" in text_lower:
        languages.append("Chinese")

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM candidate_profile")
        cur.execute("""
            INSERT INTO candidate_profile (
                id, name, headline, location, target_roles,
                skills_json, languages_json, preferences_json, raw_resume_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            1,
            "",
            "AI / Software / Product-oriented Candidate",
            "Japan",
            dumps(["AI Engineer", "Backend Engineer", "Product Engineer"]),
            dumps(found_skills),
            dumps(languages),
            dumps(["Japan", "AI", "Software"]),
            text,
        ))
        conn.commit()
    finally:
        conn.close()


def get_profile():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM candidate_profile LIMIT 1")
        row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return None

    return {
        "name": row["name"],
        "headline": row["headline"],
        "location": row["location"],
        "target_roles": loads(row["target_roles"], []),
        "skills": loads(row["skills_json"], []),
        "languages": loads(row["languages_json"], []),
        "preferences": loads(row["preferences_json"], []),
        "raw_resume_text": row["raw_resume_text"],
    }
