import os
import shutil
from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.config.database import get_db
from app.infrastructure.db.models import ResumeModel, CandidateModel
from app.presentation.routers.auth import get_current_user
from app.domain.entities.tenant import User
from app.infrastructure.queue.tasks import process_resume_task

router = APIRouter(prefix="/resumes", tags=["resumes"])

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# DTO Schemas
class ResumeResponseSchema(BaseModel):
    id: UUID
    filename: str
    file_path: str
    parsed_data: Dict[str, Any]
    organization_id: UUID
    created_at: Any


class CandidateResponseSchema(BaseModel):
    id: UUID
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    resume_id: UUID
    organization_id: UUID
    created_at: Any


@router.post("/upload", response_model=ResumeResponseSchema, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    filename = file.filename
    _, ext = os.path.splitext(filename.lower())
    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only PDF, DOCX, and TXT files are accepted."
        )

    # 1. Save file locally
    # We assign a unique prefix to prevent collision
    import uuid
    file_id = uuid.uuid4()
    safe_filename = f"{file_id}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # 2. Save in database
    resume = ResumeModel(
        id=file_id,
        filename=filename,
        file_path=dest_path,
        raw_text="",
        parsed_data={},
        organization_id=current_user.organization_id
    )
    
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # 3. Trigger async Celery task
    # Using delay() submits the job to Redis/Celery queue
    try:
        process_resume_task.delay(str(resume.id))
    except Exception as queue_err:
        # Fallback to local synchronous processing if Redis/Celery broker isn't active
        # This keeps local testing incredibly smooth!
        print(f"Celery queue error: {queue_err}. Running processing synchronously for local testing.")
        process_resume_task(str(resume.id))

    return resume


@router.get("/", response_model=List[ResumeResponseSchema])
def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resumes = db.query(ResumeModel).filter(
        ResumeModel.organization_id == current_user.organization_id
    ).order_by(ResumeModel.created_at.desc()).all()
    return resumes


@router.get("/candidates", response_model=List[CandidateResponseSchema])
def list_candidates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    candidates = db.query(CandidateModel).filter(
        CandidateModel.organization_id == current_user.organization_id
    ).order_by(CandidateModel.created_at.desc()).all()
    return candidates


@router.get("/{resume_id}", response_model=ResumeResponseSchema)
def get_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = db.query(ResumeModel).filter(
        ResumeModel.id == resume_id,
        ResumeModel.organization_id == current_user.organization_id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    return resume


@router.delete("/{resume_id}")
def delete_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = db.query(ResumeModel).filter(
        ResumeModel.id == resume_id,
        ResumeModel.organization_id == current_user.organization_id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Delete file
    if os.path.exists(resume.file_path):
        try:
            os.remove(resume.file_path)
        except Exception as e:
            print(f"Failed to delete file {resume.file_path}: {e}")

    # Delete vector from Qdrant
    from app.infrastructure.search.qdrant_store import qdrant_store
    qdrant_store.delete_resume(resume.id)

    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted successfully"}
