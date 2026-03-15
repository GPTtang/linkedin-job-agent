from pathlib import Path
import os

APP_ROOT = Path(".").resolve()
STORAGE_DIR = APP_ROOT / "storage"
DATA_DIR = APP_ROOT / "data"
REPORTS_DIR = APP_ROOT / "reports"
OUTREACH_DIR = APP_ROOT / "outreach"

DB_PATH = Path(os.getenv("DB_PATH", STORAGE_DIR / "ljob.db"))
BROWSER_PROFILE_DIR = Path(
    os.getenv("BROWSER_PROFILE_DIR", STORAGE_DIR / "browser" / "linkedin-profile")
)


def ensure_dirs() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTREACH_DIR.mkdir(parents=True, exist_ok=True)
    BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
