"""
LLM-powered services using Claude API.
Replaces keyword matching with real AI analysis.
"""
import json
from typing import Optional
import anthropic
from ..db import get_conn
from ..utils import dumps, loads
from .profile_service import get_profile
from .jobs_service import get_job

client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"


def _call_llm(system: str, user: str) -> str:
    """Call Claude with streaming, return final text."""
    with client.messages.stream(
        model=MODEL,
        max_tokens=2048,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        response = stream.get_final_message()
    return next((b.text for b in response.content if b.type == "text"), "{}")


def _parse_json(text: str, fallback: dict) -> dict:
    """Parse JSON from LLM response, stripping markdown fences if present."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0]
    try:
        return json.loads(text)
    except Exception:
        return fallback


def analyze_job_with_llm(job_id: int) -> Optional[dict]:
    """Use Claude to extract structured info from a job description."""
    job = get_job(job_id)
    if not job:
        return None

    text = _call_llm(
        system="You are an expert job analyst. Always respond with valid JSON only.",
        user=f"""Analyze this job description and return a JSON object.

Job: {job['title']} at {job['company']}, {job['location']}

Description:
{job['raw_text'] or '(no description provided)'}

Return ONLY a JSON object with these fields:
- required_skills: list of must-have technical skills (strings)
- preferred_skills: list of nice-to-have skills (strings)
- language_requirements: list of required languages e.g. ["Japanese", "English"]
- years_required: minimum years of experience as integer, or null
- summary: one-sentence job summary
- risks: list of potential concerns (e.g. "Requires native Japanese", "No visa support")
""",
    )

    parsed = _parse_json(text, {
        "required_skills": [],
        "preferred_skills": [],
        "language_requirements": [],
        "years_required": None,
        "summary": f"{job['title']} @ {job['company']}",
        "risks": [],
    })

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


def match_job_with_llm(job_id: int) -> Optional[dict]:
    """Use Claude to evaluate fit between candidate profile and job."""
    profile = get_profile()
    job = get_job(job_id)
    if not profile or not job:
        return None

    parsed = loads(job["parsed_json"], {})

    text = _call_llm(
        system="You are a senior career advisor. Evaluate job matches objectively. Always respond with valid JSON only.",
        user=f"""Evaluate the match between this candidate and job.

CANDIDATE:
- Skills: {', '.join(profile['skills']) or 'Not specified'}
- Languages: {', '.join(profile['languages']) or 'Not specified'}
- Target roles: {', '.join(profile['target_roles']) or 'Not specified'}
- Location: {profile['location']}
- Background: {profile['headline']}

JOB:
- Title: {job['title']} at {job['company']}
- Location: {job['location']}
- Required Skills: {', '.join(parsed.get('required_skills', [])) or 'Not specified'}
- Preferred Skills: {', '.join(parsed.get('preferred_skills', [])) or 'None'}
- Languages: {', '.join(parsed.get('language_requirements', [])) or 'Not specified'}
- Experience: {parsed.get('years_required', 'Not specified')} years
- Risks: {', '.join(parsed.get('risks', [])) or 'None'}

Return ONLY a JSON object with:
- score: integer 0-100 (honest assessment)
- decision: "apply", "maybe", or "skip"
- strengths: list of candidate's matching strengths
- gaps: list of areas where candidate falls short
- risks: list of specific concerns for this application
- next_actions: list of concrete recommended steps
""",
    )

    fallback = {
        "score": 30,
        "decision": "skip",
        "strengths": [],
        "gaps": [],
        "risks": [],
        "next_actions": [],
    }
    result = _parse_json(text, fallback)

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO job_matches (
                job_id, score, decision, strengths_json, gaps_json, risks_json, next_actions_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            result.get("score", 30),
            result.get("decision", "skip"),
            dumps(result.get("strengths", [])),
            dumps(result.get("gaps", [])),
            dumps(result.get("risks", [])),
            dumps(result.get("next_actions", [])),
        ))
        conn.commit()
    finally:
        conn.close()

    return result


def generate_outreach_with_llm(job_id: int) -> Optional[dict]:
    """Use Claude to generate a personalized recruiter outreach message."""
    profile = get_profile()
    job = get_job(job_id)
    if not profile or not job:
        return None

    parsed = loads(job["parsed_json"], {})
    top_skills = ", ".join(parsed.get("required_skills", [])[:4]) or "relevant skills"

    text = _call_llm(
        system="You are an expert at writing professional, personalized LinkedIn outreach messages. Always respond with valid JSON only.",
        user=f"""Write personalized LinkedIn outreach messages for this candidate applying to this job.

CANDIDATE:
- Background: {profile['headline']}
- Key Skills: {', '.join(profile['skills'][:6]) or 'Not specified'}
- Location: {profile['location']}
- Languages: {', '.join(profile['languages'])}

JOB:
- Title: {job['title']} at {job['company']}
- Location: {job['location']}
- Key Requirements: {top_skills}
- Summary: {parsed.get('summary', '')}

Write two versions:
1. Full message (3 paragraphs, professional tone, references specific skills and role)
2. Short version (2-3 sentences, suitable for LinkedIn 300-char connection request)

Return ONLY a JSON object with:
- subject: concise email subject line
- message: full version
- shorter_version: short version
""",
    )

    fallback = {
        "subject": f"Interest in {job['title']} at {job['company']}",
        "message": f"Hi, I'm interested in the {job['title']} role at {job['company']}.",
        "shorter_version": f"Interested in {job['title']} at {job['company']}.",
    }
    return _parse_json(text, fallback)
