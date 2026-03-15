import sqlite3
from pathlib import Path
from .config import DB_PATH, ensure_dirs


def get_conn() -> sqlite3.Connection:
    ensure_dirs()
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS candidate_profile (
            id INTEGER PRIMARY KEY,
            name TEXT,
            headline TEXT,
            location TEXT,
            target_roles TEXT,
            skills_json TEXT,
            languages_json TEXT,
            preferences_json TEXT,
            raw_resume_text TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            source_url TEXT UNIQUE,
            title TEXT,
            company TEXT,
            location TEXT,
            raw_text TEXT,
            parsed_json TEXT,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS job_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            score INTEGER,
            decision TEXT,
            strengths_json TEXT,
            gaps_json TEXT,
            risks_json TEXT,
            next_actions_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
    finally:
        conn.close()
