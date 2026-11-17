from typing import List, Optional
from pydantic import BaseModel, Field

class JobResult(BaseModel):
    """Schema for individual job search result item."""
    job_id: int
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    score: float = Field(description="Similarity score or fused RRF rank score")
    snippet: str = Field(description="First ~250 characters of job description")

class Profile(BaseModel):
    """Structured candidate profile extracted from resume."""
    headline: str
    skills: List[str]
    roles: List[str]
    years_experience: float
    education: Optional[str] = None
    summary: str

class Explanation(BaseModel):
    """Match explanation grounded in candidate profile and job posting."""
    matched_skills: List[str] = Field(description="Skills present in both profile and job description")
    missing_skills: List[str] = Field(description="Skills requested in job description that profile lacks")
    reason: str = Field(description="2-3 sentence grounded explanation of fit")

class SearchQuery(BaseModel):
    """Search request parameters."""
    q: str
    k: int = 10
    mode: str = Field(default="hybrid", description="One of: keyword, vector, hybrid")
