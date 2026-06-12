from datetime import datetime
from uuid import UUID, uuid4
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class Resume(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    filename: str
    file_path: str
    raw_text: str
    parsed_data: Dict[str, Any] = Field(default_factory=dict)  # skills, experience, education, projects
    organization_id: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Candidate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    resume_id: UUID
    organization_id: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobDescription(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    raw_text: str
    parsed_data: Dict[str, Any] = Field(default_factory=dict)  # skills_required, experience_required, etc.
    organization_id: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PipelineRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    job_description_id: UUID
    organization_id: UUID
    status: str = "pending"  # "pending", "running", "completed", "failed"
    graph_state: Dict[str, Any] = Field(default_factory=dict)  # Stores the full output of LangGraph
    created_at: datetime = Field(default_factory=datetime.utcnow)
