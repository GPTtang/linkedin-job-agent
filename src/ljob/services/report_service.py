from datetime import datetime
from ..config import REPORTS_DIR
from .jobs_service import list_jobs
from .match_service import top_matches


def generate_daily_report() -> str:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    file_path = REPORTS_DIR / f"{today}.md"

    jobs = list_jobs()
    matches = top_matches()

    lines = []
    lines.append(f"# Daily Job Report - {today}")
    lines.append("")
    lines.append("## Imported Jobs")
    lines.append("")
    for row in jobs[:20]:
        lines.append(f"- [{row['id']}] {row['title']} @ {row['company']} | {row['location']} | {row['status']}")

    lines.append("")
    lines.append("## Top Matches")
    lines.append("")
    for row in matches[:10]:
        lines.append(f"- Job {row['job_id']}: {row['title']} @ {row['company']} | score={row['score']} | {row['decision']}")

    content = "\n".join(lines)
    try:
        file_path.write_text(content, encoding="utf-8")
    except OSError as e:
        raise OSError(f"生成报告失败：{e}")
    return str(file_path)
