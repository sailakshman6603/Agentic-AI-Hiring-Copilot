import logging
from typing import Dict, Any, List
from uuid import UUID
from app.infrastructure.ai.agents.base import BaseAgent
from app.infrastructure.ai.agents.models import (
    ParsedResumeSchema, ParsedJDSchema, CandidateMatchSchema,
    SkillGapSchema, InterviewQuestionsSchema, AssessmentSchema, RankingSchema
)
from app.infrastructure.search.qdrant_store import qdrant_store
from app.infrastructure.ai.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class ResumeParserAgent(BaseAgent):
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing ResumeParserAgent...")
        resume_text = state.get("resume_text", "")
        
        if not resume_text:
            return {"errors": state.get("errors", []) + ["No resume text provided for parsing."]}

        prompt = f"""
        Analyze the following candidate resume text.
        Extract the personal details (name, email, phone), list of skills, work history (company, role, duration, description), and educational qualifications.
        
        Resume Text:
        {resume_text}
        """
        
        try:
            parsed_resume = self.llm_service.generate_json(
                prompt=prompt,
                response_schema=ParsedResumeSchema,
                system_prompt="You are a professional recruiting assistant specialized in parsing CVs into high-fidelity structured JSON data."
            )
            return {"parsed_resume": parsed_resume.model_dump(), "current_node": "ResumeParserAgent"}
        except Exception as e:
            logger.error(f"Error parsing resume: {e}")
            return {"errors": state.get("errors", []) + [f"ResumeParserAgent failed: {str(e)}"]}


class JDAnalyzerAgent(BaseAgent):
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing JDAnalyzerAgent...")
        jd_text = state.get("jd_text", "")
        
        if not jd_text:
            return {"errors": state.get("errors", []) + ["No job description text provided for parsing."]}

        prompt = f"""
        Analyze the following Job Description (JD).
        Extract the job title, required skills, preferred skills, required years of experience, and core responsibilities.
        
        Job Description:
        {jd_text}
        """
        
        try:
            parsed_jd = self.llm_service.generate_json(
                prompt=prompt,
                response_schema=ParsedJDSchema,
                system_prompt="You are an expert HR systems analyst. Parse job descriptions into structured requirements."
            )
            return {"parsed_jd": parsed_jd.model_dump(), "current_node": "JDAnalyzerAgent"}
        except Exception as e:
            logger.error(f"Error parsing job description: {e}")
            return {"errors": state.get("errors", []) + [f"JDAnalyzerAgent failed: {str(e)}"]}


class CandidateRetrievalAgent(BaseAgent):
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing CandidateRetrievalAgent...")
        parsed_jd = state.get("parsed_jd", {})
        org_id = state.get("organization_id")
        
        # If the state already has direct candidate_data (e.g. user selected specific resumes to match), we skip retrieval
        if state.get("candidates_data"):
            logger.info("Candidates already provided in state. Skipping Qdrant vector retrieval.")
            return {"current_node": "CandidateRetrievalAgent"}
            
        if not parsed_jd or not org_id:
            return {"errors": state.get("errors", []) + ["Missing parsed JD or Organization ID for retrieval."]}
            
        # Create a search query based on JD title and key skills
        skills_str = ", ".join(parsed_jd.get("skills_required", [])[:5])
        search_query = f"{parsed_jd.get('title', '')} {skills_str}"
        
        try:
            # Generate query embedding
            query_vector = embedding_service.get_embedding(search_query)
            
            # Fetch candidates from Qdrant
            results = qdrant_store.search_similar_resumes(
                vector=query_vector,
                organization_id=UUID(org_id),
                limit=5
            )
            
            candidates_data = []
            retrieved_ids = []
            
            for res in results:
                # Store candidate details mapped from index payloads
                meta = res.get("metadata", {})
                candidates_data.append({
                    "candidate_id": meta.get("candidate_id"),
                    "resume_id": str(res.get("resume_id")),
                    "name": f"{meta.get('first_name', '')} {meta.get('last_name', '')}".strip() or "Unnamed Candidate",
                    "email": meta.get("email"),
                    "skills": meta.get("skills", []),
                    "parsed_data": meta.get("parsed_data", {})
                })
                retrieved_ids.append(meta.get("candidate_id"))
                
            logger.info(f"Retrieved {len(candidates_data)} candidates from vector store.")
            return {
                "retrieved_candidate_ids": retrieved_ids,
                "candidates_data": candidates_data,
                "current_node": "CandidateRetrievalAgent"
            }
        except Exception as e:
            logger.error(f"Error in candidate retrieval: {e}")
            return {"errors": state.get("errors", []) + [f"CandidateRetrievalAgent failed: {str(e)}"]}


class MatchingAgent(BaseAgent):
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing MatchingAgent...")
        parsed_jd = state.get("parsed_jd", {})
        candidates = state.get("candidates_data", [])

        if not parsed_jd or not candidates:
            return {"errors": state.get("errors", []) + ["Missing JD or candidate data in MatchingAgent."]}

        matching_results = []
        
        for cand in candidates:
            cand_id = cand.get("candidate_id")
            cand_name = cand.get("name", "Candidate")
            cand_skills = cand.get("skills", [])
            cand_parsed = cand.get("parsed_data", {})
            
            prompt = f"""
            Compare the candidate profile against the job description requirements.
            
            Candidate Name: {cand_name}
            Candidate Skills: {', '.join(cand_skills)}
            Candidate Profile Summary: {json_to_str(cand_parsed)}
            
            Job Requirements:
            {json_to_str(parsed_jd)}
            
            Calculate a score (0 to 100) based on skill match and experience fit. 
            Identify key strengths, weaknesses (gaps), and write a summary.
            """
            
            try:
                match_info = self.llm_service.generate_json(
                    prompt=prompt,
                    response_schema=CandidateMatchSchema,
                    system_prompt="You are a senior technical hiring manager. Perform a rigorous match scoring analysis."
                )
                # Ensure the returned JSON has the correct candidate ID
                res_dict = match_info.model_dump()
                res_dict["candidate_id"] = cand_id
                matching_results.append(res_dict)
            except Exception as e:
                logger.error(f"Matching failed for candidate {cand_id}: {e}")
                matching_results.append({
                    "candidate_id": cand_id,
                    "score": 50,
                    "strengths": ["Data loaded"],
                    "weaknesses": ["Analysis failed"],
                    "overall_fit_summary": f"Could not compute LLM match for this candidate: {e}"
                })
                
        return {"matching_results": matching_results, "current_node": "MatchingAgent"}


class SkillGapAgent(BaseAgent):
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing SkillGapAgent...")
        parsed_jd = state.get("parsed_jd", {})
        candidates = state.get("candidates_data", [])

        if not parsed_jd or not candidates:
            return {"errors": state.get("errors", []) + ["Missing JD or candidates data in SkillGapAgent."]}

        skill_gaps = []
        for cand in candidates:
            cand_id = cand.get("candidate_id")
            cand_skills = cand.get("skills", [])
            
            prompt = f"""
            Perform a skill gap analysis for the candidate.
            Compare candidate skills: {', '.join(cand_skills)}
            Against required skills: {', '.join(parsed_jd.get('skills_required', []))}
            And preferred skills: {', '.join(parsed_jd.get('skills_preferred', []))}
            
            Detail the specific missing skills.
            Rate the level gaps (e.g., if a skill is required, but candidate lacks it, represent it as required: "Yes", candidate_has: "None" or "Beginner").
            Provide clear upskilling recommendations (training paths, courses, projects).
            """
            
            try:
                gap_analysis = self.llm_service.generate_json(
                    prompt=prompt,
                    response_schema=SkillGapSchema,
                    system_prompt="You are a corporate training and technical development specialist."
                )
                res_dict = gap_analysis.model_dump()
                res_dict["candidate_id"] = cand_id
                skill_gaps.append(res_dict)
            except Exception as e:
                logger.error(f"SkillGap calculation failed for {cand_id}: {e}")
                skill_gaps.append({
                    "candidate_id": cand_id,
                    "missing_skills": [],
                    "level_gaps": [],
                    "upskilling_recommendations": "No recommendations available due to analysis error."
                })
                
        return {"skill_gaps": skill_gaps, "current_node": "SkillGapAgent"}


class InterviewGeneratorAgent(BaseAgent):
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing InterviewGeneratorAgent...")
        parsed_jd = state.get("parsed_jd", {})
        candidates = state.get("candidates_data", [])

        if not parsed_jd or not candidates:
            return {"errors": state.get("errors", []) + ["Missing data in InterviewGeneratorAgent."]}

        interview_questions = []
        for cand in candidates:
            cand_id = cand.get("candidate_id")
            cand_skills = cand.get("skills", [])
            cand_name = cand.get("name", "Candidate")
            
            prompt = f"""
            Generate 3 custom technical or situational interview questions for {cand_name}.
            
            Candidate Skills: {', '.join(cand_skills)}
            Job Title: {parsed_jd.get('title')}
            Required Skills: {', '.join(parsed_jd.get('skills_required', []))}
            
            Provide:
            - The question
            - Topic (e.g., System Design, Database Optimization, Behavioral)
            - The expected/ideal answer details that the interviewer should look for.
            """
            
            try:
                questions = self.llm_service.generate_json(
                    prompt=prompt,
                    response_schema=InterviewQuestionsSchema,
                    system_prompt="You are an expert technical interviewer."
                )
                res_dict = questions.model_dump()
                res_dict["candidate_id"] = cand_id
                interview_questions.append(res_dict)
            except Exception as e:
                logger.error(f"Interview questions generation failed for {cand_id}: {e}")
                interview_questions.append({
                    "candidate_id": cand_id,
                    "questions": [
                        {"question": f"Describe your experience working with {parsed_jd.get('title')}.", "topic": "General", "expected_answer": "Demonstrated technical skills."}
                    ]
                })
                
        return {"interview_questions": interview_questions, "current_node": "InterviewGeneratorAgent"}


class AssessmentGeneratorAgent(BaseAgent):
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing AssessmentGeneratorAgent...")
        parsed_jd = state.get("parsed_jd", {})
        candidates = state.get("candidates_data", [])

        if not parsed_jd or not candidates:
            return {"errors": state.get("errors", []) + ["Missing data in AssessmentGeneratorAgent."]}

        assessments = []
        for cand in candidates:
            cand_id = cand.get("candidate_id")
            cand_skills = cand.get("skills", [])
            
            prompt = f"""
            Generate a custom technical assessment challenge tailored to this candidate for the job: {parsed_jd.get('title')}.
            Provide:
            1. One coding challenge (with title, description, starting boilerplate code, and verification test cases).
            2. Two multiple choice questions (with options and correct answers) mapping to core skills required.
            
            Candidate Skills: {', '.join(cand_skills)}
            Job Required Skills: {', '.join(parsed_jd.get('skills_required', []))}
            """
            
            try:
                assessment = self.llm_service.generate_json(
                    prompt=prompt,
                    response_schema=AssessmentSchema,
                    system_prompt="You are a senior technical assessment designer. Generate clean coding exercises."
                )
                res_dict = assessment.model_dump()
                res_dict["candidate_id"] = cand_id
                assessments.append(res_dict)
            except Exception as e:
                logger.error(f"Assessment generation failed for {cand_id}: {e}")
                assessments.append({
                    "candidate_id": cand_id,
                    "coding_challenges": [],
                    "multiple_choice": []
                })
                
        return {"assessments": assessments, "current_node": "AssessmentGeneratorAgent"}


class RankingAgent(BaseAgent):
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing RankingAgent...")
        matching_results = state.get("matching_results", [])
        candidates = state.get("candidates_data", [])

        if not matching_results or not candidates:
            return {"errors": state.get("errors", []) + ["No matching results to rank in RankingAgent."]}

        # Prepare summary of candidates scores
        cand_map = {c["candidate_id"]: c["name"] for c in candidates}
        
        candidates_summary = []
        for res in matching_results:
            cand_id = res["candidate_id"]
            name = cand_map.get(cand_id, "Unknown Candidate")
            candidates_summary.append({
                "candidate_id": cand_id,
                "candidate_name": name,
                "score": res["score"],
                "summary": res["overall_fit_summary"]
            })
            
        prompt = f"""
        Analyze these candidate match evaluations and sort them to construct a final ranked checklist.
        
        Candidate Summaries:
        {json_to_str(candidates_summary)}
        
        Rank the candidates from best to worst fit. Assign rank numbers (1, 2, 3, ...). Provide a key_reason explanation for their specific placement.
        """
        
        try:
            ranking_output = self.llm_service.generate_json(
                prompt=prompt,
                response_schema=RankingSchema,
                system_prompt="You are a lead talent acquisition strategist. Compile and rank candidates objectively."
            )
            return {"rankings": ranking_output.model_dump()["ranked_candidates"], "current_node": "RankingAgent"}
        except Exception as e:
            logger.error(f"Ranking failed: {e}")
            # Fallback ranking: Sort purely by matching scores in Python
            sorted_summary = sorted(candidates_summary, key=lambda x: x["score"], reverse=True)
            ranks = []
            for i, cand in enumerate(sorted_summary):
                ranks.append({
                    "candidate_id": cand["candidate_id"],
                    "candidate_name": cand["candidate_name"],
                    "score": cand["score"],
                    "rank": i + 1,
                    "key_reason": f"Ranked #{i+1} based on simple percentage score matching ({cand['score']}%)."
                })
            return {"rankings": ranks, "current_node": "RankingAgent"}


# Utility function to represent nested structures cleanly inside prompts
def json_to_str(data: Any) -> str:
    try:
        return json.dumps(data, indent=2)
    except:
        import json
        return json.dumps(data, default=str)
