from typing import List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.config.database import get_db
from app.infrastructure.db.models import JobDescriptionModel
from app.presentation.routers.auth import get_current_user
from app.domain.entities.tenant import User

router = APIRouter(prefix="/jobs", tags=["jobs"])


# DTO Schemas
class JdCreateSchema(BaseModel):
    title: str
    raw_text: str


class JdResponseSchema(BaseModel):
    id: UUID
    title: str
    raw_text: str
    parsed_data: Dict[str, Any]
    organization_id: UUID
    created_at: datetime


@router.post("/", response_model=JdResponseSchema, status_code=status.HTTP_201_CREATED)
def create_job_description(
    data: JdCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Analyze and parse asynchronously or synchronously? 
    # For user ease, we create the model, then standard task will analyze it. 
    # To keep it quick, we store raw data. In celery task run, we parse it if not already parsed.
    
    jd = JobDescriptionModel(
        title=data.title,
        raw_text=data.raw_text,
        parsed_data={},
        organization_id=current_user.organization_id
    )
    
    db.add(jd)
    db.commit()
    db.refresh(jd)
    
    return jd


@router.get("/", response_model=List[JdResponseSchema])
def list_job_descriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    jds = db.query(JobDescriptionModel).filter(
        JobDescriptionModel.organization_id == current_user.organization_id
    ).order_by(JobDescriptionModel.created_at.desc()).all()
    
    return jds


@router.get("/{jd_id}", response_model=JdResponseSchema)
def get_job_description(
    jd_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    jd = db.query(JobDescriptionModel).filter(
        JobDescriptionModel.id == jd_id,
        JobDescriptionModel.organization_id == current_user.organization_id
    ).first()
    
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
        
    return jd


@router.delete("/{jd_id}")
def delete_job_description(
    jd_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    jd = db.query(JobDescriptionModel).filter(
        JobDescriptionModel.id == jd_id,
        JobDescriptionModel.organization_id == current_user.organization_id
    ).first()
    
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
        
    db.delete(jd)
    db.commit()
    return {"message": "Job description deleted successfully"}
