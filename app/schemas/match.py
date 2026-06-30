from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Optional

class EducationEntry(BaseModel):
    degree: str = Field(..., description="Degree or certification name")
    institution: Optional[str] = Field(None, description="Name of the institution")
    year: Optional[str] = Field(None, description="Graduation year or time period")

class Preferences(BaseModel):
    roles: List[str] = Field(default_factory=list, description="Target job titles")
    locations: List[str] = Field(default_factory=list, description="Preferred locations")
    remote: Optional[str] = Field(None, description="Prefers remote work (e.g. remote, hybrid, on-site)")

class Logistics(BaseModel):
    location: Optional[str] = Field(None, description="Job location")
    remote: Optional[str] = Field(None, description="Is the job remote (e.g. remote, hybrid, on-site)")
    timezone: Optional[str] = Field(None, description="Timezone requirements")

class CandidateProfile(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the candidate")
    contact: Dict[str, Optional[str]] = Field(default_factory=dict, description="Contact information")
    skills: List[str] = Field(default_factory=list, description="List of technical and soft skills")
    experience_years: float = Field(0.0, description="Total years of experience")
    education: List[EducationEntry] = Field(default_factory=list, description="Educational background")
    preferences: Preferences = Field(default_factory=Preferences, description="Career preferences and logistics")

    @model_validator(mode='after')
    def normalize_skills(self) -> 'CandidateProfile':
        """
        Deduplicates the skills list while preserving the casing of the *first* 
        occurrence of each skill. E.g., ["Python", "python"] -> ["Python"].
        """
        if self.skills:
            normalized = []
            seen = set()
            for s in self.skills:
                s_stripped = s.strip()
                s_lower = s_stripped.lower()
                if s_lower and s_lower not in seen:
                    seen.add(s_lower)
                    normalized.append(s_stripped)
            self.skills = normalized
        return self

class MatchScoreDetails(BaseModel):
    hard_skills_score: int = Field(..., ge=0, le=40, description="Hard Skills Fit (Max 40 points)")
    experience_score: int = Field(..., ge=0, le=30, description="Experience Level Fit (Max 30 points)")
    soft_skills_score: int = Field(..., ge=0, le=20, description="Soft Skills & Domain Knowledge (Max 20 points)")
    logistics_score: int = Field(..., ge=0, le=10, description="Career Preferences & Logistics (Max 10 points)")

class JobMatchResult(BaseModel):
    match_analysis: str = Field(..., description="Step-by-step analysis comparing candidate skills against mandatory job skills.")
    score_details: MatchScoreDetails
    total_score: int = Field(..., ge=0, le=100, description="Sum of score details")
    explanation: str = Field(..., description="Detailed explanation of the derived score")
    key_matched_skills: List[str] = Field(default_factory=list, description="Key strengths and matching skills")
    missing_skills: List[str] = Field(default_factory=list, description="Required skills the candidate lacks (weaknesses)")
    recommendation: str = Field(..., description="Actionable advice for the candidate")

    @model_validator(mode='after')
    def validate_total_score(self) -> 'JobMatchResult':
        calculated_total = (
            self.score_details.hard_skills_score +
            self.score_details.experience_score +
            self.score_details.soft_skills_score +
            self.score_details.logistics_score
        )
        if self.total_score != calculated_total:
            raise ValueError(f"total_score ({self.total_score}) must equal the sum of score details ({calculated_total})")
        return self

class JobProfile(BaseModel):
    title: str = Field(..., description="Job title")
    mandatory_skills: List[str] = Field(default_factory=list, description="Mandatory technical and soft skills required")
    nice_to_have_skills: List[str] = Field(default_factory=list, description="Preferred or bonus skills")
    experience_years_required: float = Field(0.0, description="Minimum years of experience required")
    education_required: Optional[str] = Field("", description="Educational requirements")
    logistics: Logistics = Field(default_factory=Logistics, description="Logistics like remote, location, timezone")

class JobMatchResponse(BaseModel):
    parsed_candidate: CandidateProfile
    parsed_job: JobProfile
    match_result: JobMatchResult
