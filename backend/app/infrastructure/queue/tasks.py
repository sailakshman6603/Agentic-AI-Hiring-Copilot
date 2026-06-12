import logging
from uuid import UUID
from app.infrastructure.queue.celery_app import celery_app
from app.config.database import SessionLocal
from app.infrastructure.db.models import ResumeModel, CandidateModel, JobDescriptionModel, PipelineRunModel
from app.infrastructure.utils.file_parser import extract_text_from_file
from app.infrastructure.ai.groq_client import groq_llm_service
from app.infrastructure.ai.agents.implementations import ResumeParserAgent
from app.infrastructure.ai.embedding_service import embedding_service
from app.infrastructure.search.qdrant_store import qdrant_store
from app.infrastructure.ai.agents.workflow import run_hiring_workflow

logger = logging.getLogger(__name__)


@celery_app.task(name="app.infrastructure.queue.tasks.process_resume_task")
def process_resume_task(resume_id_str: str) -> bool:
    logger.info(f"Asynchronously processing resume ID: {resume_id_str}")
    db = SessionLocal()
    try:
        resume_id = UUID(resume_id_str)
        resume = db.query(ResumeModel).filter(ResumeModel.id == resume_id).first()
        if not resume:
            logger.error(f"Resume with ID {resume_id_str} not found in DB.")
            return False

        # 1. Extract text from document
        raw_text = extract_text_from_file(resume.file_path)
        resume.raw_text = raw_text
        db.commit()

        # 2. Parse text with ResumeParserAgent
        parser = ResumeParserAgent(groq_llm_service)
        parse_result = parser.execute({"resume_text": raw_text})
        
        parsed_data = parse_result.get("parsed_resume", {})
        if not parsed_data:
            error_msg = f"Parsing failed for resume {resume_id_str}: {parse_result.get('errors')}"
            logger.error(error_msg)
            return False
            
        resume.parsed_data = parsed_data
        db.commit()

        # 3. Create Candidate profile
        personal_info = parsed_data.get("personal_info", {})
        candidate = db.query(CandidateModel).filter(CandidateModel.resume_id == resume_id).first()
        if not candidate:
            candidate = CandidateModel(
                first_name=personal_info.get("first_name", ""),
                last_name=personal_info.get("last_name", ""),
                email=personal_info.get("email", ""),
                phone=personal_info.get("phone", ""),
                resume_id=resume_id,
                organization_id=resume.organization_id
            )
            db.add(candidate)
        else:
            candidate.first_name = personal_info.get("first_name", candidate.first_name)
            candidate.last_name = personal_info.get("last_name", candidate.last_name)
            candidate.email = personal_info.get("email", candidate.email)
            candidate.phone = personal_info.get("phone", candidate.phone)
            
        db.commit()
        db.refresh(candidate)

        # 4. Generate Embeddings & index to Qdrant vector database
        # We index a combination of the candidate's skills and roles description
        skills_list = parsed_data.get("skills", [])
        experience_summary = " ".join([
            f"{exp.get('role')} at {exp.get('company')}: {exp.get('description')}"
            for exp in parsed_data.get("experience", [])
        ])
        indexing_text = f"Skills: {', '.join(skills_list)}. Experience: {experience_summary}"
        
        resume_vector = embedding_service.get_embedding(indexing_text)
        
        # Metadata payload for Qdrant (scoped with tenant ID for security)
        metadata = {
            "organization_id": str(resume.organization_id),
            "candidate_id": str(candidate.id),
            "first_name": candidate.first_name,
            "last_name": candidate.last_name,
            "email": candidate.email,
            "skills": skills_list,
            "parsed_data": parsed_data
        }
        
        qdrant_store.upsert_resume(
            resume_id=resume_id,
            vector=resume_vector,
            metadata=metadata
        )
        
        logger.info(f"Resume {resume_id_str} indexed successfully. Candidate ID: {candidate.id}")
        return True

    except Exception as e:
        logger.error(f"Error in process_resume_task: {e}", exc_info=True)
        return False
    finally:
        db.close()


@celery_app.task(name="app.infrastructure.queue.tasks.run_matching_pipeline_task")
def run_matching_pipeline_task(pipeline_run_id_str: str) -> bool:
    logger.info(f"Asynchronously running matching pipeline for run ID: {pipeline_run_id_str}")
    db = SessionLocal()
    try:
        run_id = UUID(pipeline_run_id_str)
        run = db.query(PipelineRunModel).filter(PipelineRunModel.id == run_id).first()
        if not run:
            logger.error(f"Pipeline run ID {pipeline_run_id_str} not found in DB.")
            return False

        run.status = "running"
        db.commit()

        # Load JD
        jd = db.query(JobDescriptionModel).filter(JobDescriptionModel.id == run.job_description_id).first()
        if not jd:
            run.status = "failed"
            run.graph_state = {"errors": ["Job Description not found."]}
            db.commit()
            return False

        # If JD is not parsed yet, parse it now
        if not jd.parsed_data:
            from app.infrastructure.ai.agents.implementations import JDAnalyzerAgent
            analyzer = JDAnalyzerAgent(groq_llm_service)
            jd_analysis = analyzer.execute({"jd_text": jd.raw_text})
            parsed_jd = jd_analysis.get("parsed_jd", {})
            if parsed_jd:
                jd.parsed_data = parsed_jd
                db.commit()

        # Initialize input state for LangGraph
        initial_state = {
            "organization_id": str(run.organization_id),
            "jd_id": str(jd.id),
            "jd_text": jd.raw_text,
            "parsed_jd": jd.parsed_data,
            "candidates_data": []  # Empty prompts retrieval agent to fetch from Qdrant
        }

        # Run compiled LangGraph workflow
        final_state = run_hiring_workflow(initial_state)

        # Update run results in database
        run.graph_state = final_state
        if final_state.get("errors"):
            run.status = "failed"
        else:
            run.status = "completed"
            
        db.commit()
        logger.info(f"Pipeline run {pipeline_run_id_str} finished with status: {run.status}")
        return True

    except Exception as e:
        logger.error(f"Error in run_matching_pipeline_task: {e}", exc_info=True)
        try:
            run = db.query(PipelineRunModel).filter(PipelineRunModel.id == UUID(pipeline_run_id_str)).first()
            if run:
                run.status = "failed"
                run.graph_state = {"errors": [f"Runtime error: {str(e)}"]}
                db.commit()
        except Exception as inner_e:
            logger.error(f"Failed to write failure status to DB: {inner_e}")
        return False
    finally:
        db.close()
