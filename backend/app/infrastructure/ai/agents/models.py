from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ResumeParserAgent Schemas
class PersonalInfo(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class WorkExperience(BaseModel):
    company: str
    role: str
    duration: str
    description: str


class Education(BaseModel):
    institution: str
    degree: str
    year: Optional[str] = None


class ParsedResumeSchema(BaseModel):
    personal_info: PersonalInfo
    skills: List[str] = Field(default_factory=list)
    experience: List[WorkExperience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)


# JDAnalyzerAgent Schemas
class ParsedJDSchema(BaseModel):
    title: str
    skills_required: List[str] = Field(default_factory=list)
    skills_preferred: List[str] = Field(default_factory=list)
    experience_required_years: Optional[int] = None
    responsibilities: List[str] = Field(default_factory=list)


# MatchingAgent Schemas
class CandidateMatchSchema(BaseModel):
    candidate_id: str
    score: int = Field(description="Percentage score representing alignment from 0 to 100")
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    overall_fit_summary: str


# SkillGapAgent Schemas
class LevelGap(BaseModel):
    skill: str
    required: str
    candidate_has: str


class SkillGapSchema(BaseModel):
    candidate_id: str
    missing_skills: List[str] = Field(default_factory=list)
    level_gaps: List[LevelGap] = Field(default_factory=list)
    upskilling_recommendations: str


# InterviewGeneratorAgent Schemas
class InterviewQuestion(BaseModel):
    question: str
    topic: str
    expected_answer: str


class InterviewQuestionsSchema(BaseModel):
    candidate_id: str
    questions: List[InterviewQuestion] = Field(default_factory=list)


# AssessmentGeneratorAgent Schemas
class CodingChallenge(BaseModel):
    title: str
    description: str
    starter_code: str
    test_cases: str


class MultipleChoice(BaseModel):
    question: str
    options: List[str]
    correct_answer: str


class AssessmentSchema(BaseModel):
    candidate_id: str
    coding_challenges: List[CodingChallenge] = Field(default_factory=list)
    multiple_choice: List[MultipleChoice] = Field(default_factory=list)


# RankingAgent Schemas
class CandidateRankDetail(BaseModel):
    candidate_id: str
    candidate_name: str
    score: int
    rank: int
    key_reason: str


class RankingSchema(BaseModel):
    ranked_candidates: List[CandidateRankDetail] = Field(default_factory=list)
