"""
Use Claude to generate optimized LinkedIn profile content from the candidate's resume.
"""
from typing import Optional
from .profile_service import get_profile
from .llm_service import _call_llm, _parse_json


def generate_linkedin_content() -> Optional[dict]:
    """
    Generate optimized LinkedIn profile content using Claude.
    Returns:
        {
          "headline": str,       # ≤120 chars
          "about": str,          # ≤2600 chars
          "skills": list[str],   # top 15 skills
        }
    """
    profile = get_profile()
    if not profile:
        return None

    resume_text = profile.get("raw_resume_text", "") or ""

    text = _call_llm(
        system="You are a LinkedIn profile optimization expert. Always respond with valid JSON only.",
        user=f"""Optimize this candidate's LinkedIn profile content based on their resume.

CURRENT PROFILE:
- Headline: {profile['headline']}
- Location: {profile['location']}
- Skills: {', '.join(profile['skills'])}
- Languages: {', '.join(profile['languages'])}
- Target Roles: {', '.join(profile['target_roles'])}

RESUME TEXT:
{resume_text[:4000] if resume_text else '(not provided)'}

Generate optimized LinkedIn content. Return ONLY a JSON object with:
- headline: keyword-rich professional headline (max 120 chars, e.g. "AI Engineer | LLM & Agent Systems | Python · AWS · Japan")
- about: compelling first-person About section (max 2000 chars, include skills, experience highlights, what you're looking for)
- skills: list of exactly 15 most relevant skills to showcase on LinkedIn (strings)
""",
    )

    return _parse_json(text, {
        "headline": profile["headline"],
        "about": "",
        "skills": profile["skills"][:15],
    })
