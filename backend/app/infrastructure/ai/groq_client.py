import os
import json
import logging
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel
from groq import Groq
from app.config.settings import settings
from app.domain.interfaces.llm_service import ILLMService

logger = logging.getLogger(__name__)


class GroqLLMService(ILLMService):
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
        self.client = None
        
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                logger.info("Groq client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.client = None
        else:
            logger.warning(
                "GROQ_API_KEY is not set. LLM service will run in demo/simulation fallback mode."
            )

    def generate_text(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> str:
        model = model_name or "llama-3.1-8b-instant"
        
        if self.client:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                chat_completion = self.client.chat.completions.create(
                    messages=messages,
                    model=model,
                    temperature=0.3
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                logger.error(f"Groq text generation failed: {e}. Falling back to simulation.")

        return self._simulate_text_generation(prompt)

    def generate_json(
        self, 
        prompt: str, 
        response_schema: Type[BaseModel],
        system_prompt: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> BaseModel:
        # For structured parsing, prefer larger model
        model = model_name or "llama-3.3-70b-versatile"
        
        if self.client:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                
                # Enforce JSON formatting in prompt
                schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
                enriched_prompt = f"{prompt}\n\nYour output must STRICTLY follow this JSON schema:\n{schema_json}\n\nReturn ONLY the raw valid JSON object. Do not wrap it in markdown code blocks."
                
                messages.append({"role": "user", "content": enriched_prompt})
                
                chat_completion = self.client.chat.completions.create(
                    messages=messages,
                    model=model,
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                
                response_text = chat_completion.choices[0].message.content
                logger.debug(f"LLM raw response: {response_text}")
                
                # Attempt parsing
                parsed_json = json.loads(response_text)
                return response_schema.model_validate(parsed_json)
                
            except Exception as e:
                logger.error(f"Groq JSON generation/parsing failed: {e}. Falling back to simulation.")

        # Fallback structured generation
        return self._simulate_json_generation(prompt, response_schema)

    def _simulate_text_generation(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "interview" in prompt_lower:
            return "1. Tell me about a time you resolved a complex production issue.\n2. How do you design APIs for high performance and concurrency?"
        if "assessment" in prompt_lower:
            return "Write a python function to find the maximum sub-array sum using Kadane's algorithm."
        return "This is a fallback response generated locally because the Groq API key was not configured."

    def _simulate_json_generation(self, prompt: str, schema: Type[BaseModel]) -> BaseModel:
        # Return logical dummy objects matching schema
        logger.info(f"Simulating JSON structure for {schema.__name__}")
        
        schema_name = schema.__name__.lower()
        dummy_dict = {}
        
        # General heuristics to supply sensible data based on schema name
        if "parser" in schema_name or "resume" in schema_name:
            dummy_dict = {
                "personal_info": {"first_name": "Alex", "last_name": "Developer", "email": "alex.dev@example.com", "phone": "+1-555-0199"},
                "skills": ["Python", "FastAPI", "React", "PostgreSQL", "Docker", "Git"],
                "experience": [
                    {"company": "SaaS Corp", "role": "Senior Engineer", "duration": "3 years", "description": "Built backend APIs using Python and FastAPI."}
                ],
                "education": [
                    {"institution": "Tech University", "degree": "B.S. Computer Science", "year": "2020"}
                ]
            }
        elif "jd" in schema_name or "job" in schema_name:
            dummy_dict = {
                "title": "Senior Python Developer",
                "skills_required": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
                "skills_preferred": ["Kubernetes", "AWS", "Celery"],
                "experience_required_years": 5,
                "responsibilities": ["Design APIs", "Integrate databases", "Implement background workers"]
            }
        elif "matching" in schema_name or "match" in schema_name:
            dummy_dict = {
                "score": 85,
                "strengths": ["Strong FastAPI experience", "Proficient in SQL databases"],
                "weaknesses": ["Lacks production Kubernetes experience"],
                "overall_fit_summary": "Highly qualified candidate matching 80%+ of core requirements."
            }
        elif "gap" in schema_name:
            dummy_dict = {
                "missing_skills": ["Kubernetes", "Celery"],
                "level_gaps": [{"skill": "Kubernetes", "required": "Intermediate", "candidate_has": "None"}],
                "upskilling_recommendations": "Enroll in CKAD course and build a small distributed queue project."
            }
        elif "interview" in schema_name:
            dummy_dict = {
                "questions": [
                    {"question": "How do you optimize slow SQLAlchemy queries?", "topic": "Databases", "expected_answer": "Use selectinload/joinedload, create indices, analyze query execution plan."}
                ]
            }
        elif "assessment" in schema_name:
            dummy_dict = {
                "coding_challenges": [
                    {"title": "FastAPI Rate Limiter", "description": "Build a sliding-window rate limiter middleware.", "starter_code": "def rate_limiter(ip: str): pass", "test_cases": "Rate limit exceeded after 10 requests."}
                ],
                "multiple_choice": [
                    {"question": "What is the primary message broker used for Celery?", "options": ["Redis", "Postgres", "Elasticsearch", "SQLite"], "correct_answer": "Redis"}
                ]
            }
        elif "ranking" in schema_name:
            dummy_dict = {
                "ranked_candidates": [
                    {"candidate_id": "00000000-0000-0000-0000-000000000000", "score": 88, "rank": 1, "key_reason": "Matches all required tech stacks."}
                ]
            }
        else:
            # Empty fallback matching the schema keys
            for field_name, field in schema.model_fields.items():
                dummy_dict[field_name] = [] if getattr(field.annotation, "__origin__", None) is list else {}

        try:
            return schema.model_validate(dummy_dict)
        except Exception as e:
            logger.error(f"Failed to generate structured mock: {e}")
            # Try to return instantiated default
            return schema.model_construct(**dummy_dict)


# Singleton instance
groq_llm_service = GroqLLMService()
