from pathlib import Path
from .profile_service import get_profile
from .jobs_service import get_job
from ..utils import loads
from ..config import OUTREACH_DIR


def recruiter_message(job_id: int):
    profile = get_profile()
    job = get_job(job_id)
    if not profile or not job:
        return None

    parsed = loads(job["parsed_json"], {})
    skills = parsed.get("required_skills", [])[:3]
    skill_text = ", ".join(skills) if skills else "relevant technical skills"

    short_msg = (
        f"Hi, I'm interested in the {job['title']} role at {job['company']}. "
        f"My background aligns with {skill_text}, and I'm currently based in Japan. "
        f"I'd be glad to share more if relevant."
    )

    full_msg = (
        f"Hi, I came across the {job['title']} role at {job['company']} and found it highly relevant.\n\n"
        f"I have a background in software / AI-related work, and my experience overlaps with {skill_text}. "
        f"I'm also currently based in Japan, so the location context is a good fit.\n\n"
        f"If this role is still open, I'd be happy to share my background and learn more.\n"
        f"Thank you."
    )

    return {
        "subject": f"Interest in {job['title']} role",
        "message": full_msg,
        "shorter_version": short_msg,
    }


def save_recruiter_message(job_id: int):
    result = recruiter_message(job_id)
    if not result:
        return None
    OUTREACH_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTREACH_DIR / f"recruiter_job_{job_id}.md"
    content = "\n".join([
        f"# {result['subject']}",
        "",
        "## Standard",
        "",
        result["message"],
        "",
        "## Shorter Version",
        "",
        result["shorter_version"],
        "",
    ])
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as e:
        raise OSError(f"保存外联文案失败：{e}")
    return str(path)
