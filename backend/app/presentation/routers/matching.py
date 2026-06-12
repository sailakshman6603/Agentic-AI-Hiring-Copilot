from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.config.database import get_db
from app.infrastructure.db.models import PipelineRunModel, JobDescriptionModel
from app.presentation.routers.auth import get_current_user
from app.domain.entities.tenant import User
from app.infrastructure.queue.tasks import run_matching_pipeline_task
from app.infrastructure.search.qdrant_store import qdrant_store
from app.infrastructure.ai.embedding_service import embedding_service

router = APIRouter(prefix="/matching", tags=["matching"])


# DTO Schemas
class PipelineRunRequestSchema(BaseModel):
    job_description_id: UUID


class PipelineRunResponseSchema(BaseModel):
    id: UUID
    job_description_id: UUID
    organization_id: UUID
    status: str
    graph_state: Dict[str, Any]
    created_at: Any


class SemanticSearchRequestSchema(BaseModel):
    query: str
    limit: int = 5


class SemanticSearchResultSchema(BaseModel):
    candidate_id: UUID
    resume_id: UUID
    score: float
    name: str
    email: str
    skills: List[str]
    parsed_data: Dict[str, Any]


@router.post("/run", response_model=PipelineRunResponseSchema, status_code=status.HTTP_201_CREATED)
def start_matching_pipeline(
    data: PipelineRunRequestSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify JD exists and belongs to organization
    jd = db.query(JobDescriptionModel).filter(
        JobDescriptionModel.id == data.job_description_id,
        JobDescriptionModel.organization_id == current_user.organization_id
    ).first()
    
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job Description not found"
        )

    # 1. Create pipeline run entry
    run = PipelineRunModel(
        job_description_id=data.job_description_id,
        organization_id=current_user.organization_id,
        status="pending",
        graph_state={}
    )
    
    db.add(run)
    db.commit()
    db.refresh(run)

    # 2. Queue Celery task
    try:
        run_matching_pipeline_task.delay(str(run.id))
    except Exception as queue_err:
        # Fallback to local synchronous processing if Redis/Celery broker isn't active
        print(f"Celery queue error: {queue_err}. Running matching pipeline synchronously for local testing.")
        run_matching_pipeline_task(str(run.id))
        db.refresh(run)

    return run


@router.get("/runs", response_model=List[PipelineRunResponseSchema])
def list_pipeline_runs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    runs = db.query(PipelineRunModel).filter(
        PipelineRunModel.organization_id == current_user.organization_id
    ).order_by(PipelineRunModel.created_at.desc()).all()
    
    return runs


@router.get("/runs/{run_id}", response_model=PipelineRunResponseSchema)
def get_pipeline_run(
    run_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    run = db.query(PipelineRunModel).filter(
        PipelineRunModel.id == run_id,
        PipelineRunModel.organization_id == current_user.organization_id
    ).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
        
    return run


@router.post("/search", response_model=List[SemanticSearchResultSchema])
def semantic_search_candidates(
    data: SemanticSearchRequestSchema,
    current_user: User = Depends(get_current_user)
):
    if not data.query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    try:
        # 1. Generate query embedding
        query_vector = embedding_service.get_embedding(data.query)
        
        # 2. Query Qdrant with tenant payload isolation filter
        results = qdrant_store.search_similar_resumes(
            vector=query_vector,
            organization_id=current_user.organization_id,
            limit=data.limit
        )
        
        # 3. Format results
        output = []
        for r in results:
            meta = r.get("metadata", {})
            output.append({
                "candidate_id": UUID(meta.get("candidate_id")),
                "resume_id": r.get("resume_id"),
                "score": r.get("score", 0.0),
                "name": f"{meta.get('first_name', '')} {meta.get('last_name', '')}".strip() or "Unnamed Candidate",
                "email": meta.get("email", ""),
                "skills": meta.get("skills", []),
                "parsed_data": meta.get("parsed_data", {})
            })
            
        return output
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {str(e)}"
        )
