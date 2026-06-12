from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class Organization(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    password_hash: str
    role: str  # "admin", "recruiter", "candidate"
    organization_id: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)
