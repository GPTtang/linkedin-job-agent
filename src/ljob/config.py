from pathlib import Path
import os

APP_ROOT = Path(".").resolve()
STORAGE_DIR = APP_ROOT / "storage"
DATA_DIR = APP_ROOT / "data"
REPORTS_DIR = APP_ROOT / "reports"
OUTREACH_DIR = APP_ROOT / "outreach"

DB_PATH = Path(os.getenv("DB_PATH", str(STORAGE_DIR / "ljob.db")))
BROWSER_PROFILE_DIR = Path(
    os.getenv("BROWSER_PROFILE_DIR", str(STORAGE_DIR / "browser" / "linkedin-profile"))
)

# 技能池（集中定义，避免各模块重复）
MUST_SKILLS = [
    "python", "java", "javascript", "typescript", "react", "node.js",
    "sql", "postgresql", "docker", "kubernetes", "aws", "azure",
    "ai", "llm", "prompt engineering", "agent", "mcp", "git",
]
NICE_SKILLS = ["redis", "graphql", "gcp", "kafka", "elasticsearch"]


def ensure_dirs() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTREACH_DIR.mkdir(parents=True, exist_ok=True)
    BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
