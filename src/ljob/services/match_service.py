from ..db import get_conn
from ..utils import loads, dumps
from .profile_service import get_profile
from .jobs_service import get_job


def run_match(job_id: int):
    profile = get_profile()
    job = get_job(job_id)
    if not profile or not job:
        return None

    parsed = loads(job["parsed_json"], {})
    profile_skills = {s.lower() for s in profile["skills"]}
    required_skills = {s.lower() for s in parsed.get("required_skills", [])}
    preferred_skills = {s.lower() for s in parsed.get("preferred_skills", [])}

    score = 30
    matched_required = profile_skills & required_skills
    matched_preferred = profile_skills & preferred_skills

    score += min(len(matched_required) * 10, 40)
    score += min(len(matched_preferred) * 5, 15)

    strengths = []
    gaps = []
    risks = parsed.get("risks", [])
    next_actions = []

    if matched_required:
        strengths.append(f"命中核心技能：{', '.join(sorted(matched_required))}")

    missing_required = required_skills - profile_skills
    if missing_required:
        gaps.append(f"缺少或未明确体现：{', '.join(sorted(missing_required))}")
        next_actions.append("在简历中补充与岗位更相关的项目和关键词")

    if score >= 80:
        decision = "apply"
        next_actions.append("建议优先投递")
    elif score >= 60:
        decision = "maybe"
        next_actions.append("建议优化简历后再投递")
    else:
        decision = "skip"
        next_actions.append("暂不优先")

    result = {
        "score": min(score, 100),
        "decision": decision,
        "strengths": strengths,
        "gaps": gaps,
        "risks": risks,
        "next_actions": next_actions,
    }

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO job_matches (
                job_id, score, decision, strengths_json, gaps_json, risks_json, next_actions_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            result["score"],
            result["decision"],
            dumps(result["strengths"]),
            dumps(result["gaps"]),
            dumps(result["risks"]),
            dumps(result["next_actions"]),
        ))
        conn.commit()
    finally:
        conn.close()
    return result


def top_matches():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT jm.job_id, j.title, j.company, jm.score, jm.decision
            FROM job_matches jm
            JOIN jobs j ON jm.job_id = j.id
            ORDER BY jm.score DESC, jm.id DESC
            LIMIT 20
        """)
        rows = cur.fetchall()
    finally:
        conn.close()
    return rows
