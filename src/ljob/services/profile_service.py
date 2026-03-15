from pathlib import Path
from ..db import get_conn
from ..utils import dumps, loads


def import_profile_from_resume(file_path: str) -> None:
    text = Path(file_path).read_text(encoding="utf-8")

    skills_pool = [
        "python", "java", "javascript", "typescript", "react", "node.js",
        "sql", "postgresql", "docker", "kubernetes", "aws", "azure",
        "ai", "llm", "prompt engineering", "agent", "mcp", "git"
    ]
    found_skills = [s for s in skills_pool if s.lower() in text.lower()]

    languages = []
    if "japanese" in text.lower() or "日语" in text or "日本語" in text:
        languages.append("Japanese")
    if "english" in text.lower() or "英语" in text or "英語" in text:
        languages.append("English")
    if "中文" in text or "chinese" in text.lower():
        languages.append("Chinese")

    conn = get_conn()
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
    conn.close()


def get_profile():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM candidate_profile LIMIT 1")
    row = cur.fetchone()
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
