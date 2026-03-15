from pydantic import BaseModel, Field
from typing import List, Optional


class CandidateProfile(BaseModel):
    name: str = ""
    headline: str = ""
    location: str = ""
    target_roles: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    preferences: List[str] = Field(default_factory=list)
    raw_resume_text: str = ""


class Job(BaseModel):
    id: Optional[int] = None
    source: str = "linkedin"
    source_url: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    raw_text: str = ""
    status: str = "saved"


class JobAnalysis(BaseModel):
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    language_requirements: List[str] = Field(default_factory=list)
    years_required: Optional[int] = None
    summary: str = ""
    risks: List[str] = Field(default_factory=list)


class MatchResult(BaseModel):
    score: int
    decision: str
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)
