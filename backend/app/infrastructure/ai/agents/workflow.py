import logging
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, START, END

from app.infrastructure.ai.groq_client import groq_llm_service
from app.infrastructure.ai.agents.implementations import (
    ResumeParserAgent, JDAnalyzerAgent, CandidateRetrievalAgent, MatchingAgent,
    SkillGapAgent, InterviewGeneratorAgent, AssessmentGeneratorAgent, RankingAgent
)

logger = logging.getLogger(__name__)


class AgentWorkflowState(TypedDict, total=False):
    organization_id: str
    resume_id: Optional[str]
    resume_text: Optional[str]
    jd_id: Optional[str]
    jd_text: Optional[str]
    parsed_resume: Dict[str, Any]
    parsed_jd: Dict[str, Any]
    retrieved_candidate_ids: List[str]
    candidates_data: List[Dict[str, Any]]
    matching_results: List[Dict[str, Any]]
    skill_gaps: List[Dict[str, Any]]
    interview_questions: List[Dict[str, Any]]
    assessments: List[Dict[str, Any]]
    rankings: List[Dict[str, Any]]
    errors: List[str]
    current_node: str


# Initialize agents
resume_parser_agent = ResumeParserAgent(groq_llm_service)
jd_analyzer_agent = JDAnalyzerAgent(groq_llm_service)
candidate_retrieval_agent = CandidateRetrievalAgent(groq_llm_service)
matching_agent = MatchingAgent(groq_llm_service)
skill_gap_agent = SkillGapAgent(groq_llm_service)
interview_agent = InterviewGeneratorAgent(groq_llm_service)
assessment_agent = AssessmentGeneratorAgent(groq_llm_service)
ranking_agent = RankingAgent(groq_llm_service)


# Define node functions
def run_resume_parser(state: AgentWorkflowState) -> Dict[str, Any]:
    # Only parse if resume_text is present
    if state.get("resume_text"):
        return resume_parser_agent.execute(state)
    return {"current_node": "ResumeParserAgent"}


def run_jd_analyzer(state: AgentWorkflowState) -> Dict[str, Any]:
    if state.get("jd_text"):
        return jd_analyzer_agent.execute(state)
    return {"current_node": "JDAnalyzerAgent"}


def run_candidate_retrieval(state: AgentWorkflowState) -> Dict[str, Any]:
    return candidate_retrieval_agent.execute(state)


def run_matching(state: AgentWorkflowState) -> Dict[str, Any]:
    return matching_agent.execute(state)


def run_skill_gap(state: AgentWorkflowState) -> Dict[str, Any]:
    return skill_gap_agent.execute(state)


def run_interview_generator(state: AgentWorkflowState) -> Dict[str, Any]:
    return interview_agent.execute(state)


def run_assessment_generator(state: AgentWorkflowState) -> Dict[str, Any]:
    return assessment_agent.execute(state)


def run_ranking(state: AgentWorkflowState) -> Dict[str, Any]:
    return ranking_agent.execute(state)


# Build the state graph
workflow = StateGraph(AgentWorkflowState)

# Add nodes
workflow.add_node("ResumeParserAgent", run_resume_parser)
workflow.add_node("JDAnalyzerAgent", run_jd_analyzer)
workflow.add_node("CandidateRetrievalAgent", run_candidate_retrieval)
workflow.add_node("MatchingAgent", run_matching)
workflow.add_node("SkillGapAgent", run_skill_gap)
workflow.add_node("InterviewGeneratorAgent", run_interview_generator)
workflow.add_node("AssessmentGeneratorAgent", run_assessment_generator)
workflow.add_node("RankingAgent", run_ranking)

# Connect edges sequentially
workflow.add_edge(START, "ResumeParserAgent")
workflow.add_edge("ResumeParserAgent", "JDAnalyzerAgent")
workflow.add_edge("JDAnalyzerAgent", "CandidateRetrievalAgent")
workflow.add_edge("CandidateRetrievalAgent", "MatchingAgent")
workflow.add_edge("MatchingAgent", "SkillGapAgent")
workflow.add_edge("SkillGapAgent", "InterviewGeneratorAgent")
workflow.add_edge("InterviewGeneratorAgent", "AssessmentGeneratorAgent")
workflow.add_edge("AssessmentGeneratorAgent", "RankingAgent")
workflow.add_edge("RankingAgent", END)

# Compile graph
compiled_workflow = workflow.compile()


def run_hiring_workflow(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """Runs the LangGraph candidate hiring pipeline."""
    logger.info("Starting Hiring Workflow Pipeline...")
    
    # Initialize basic fields
    full_state = AgentWorkflowState(
        organization_id=initial_state.get("organization_id"),
        resume_id=initial_state.get("resume_id"),
        resume_text=initial_state.get("resume_text"),
        jd_id=initial_state.get("jd_id"),
        jd_text=initial_state.get("jd_text"),
        candidates_data=initial_state.get("candidates_data", []),
        parsed_resume={},
        parsed_jd={},
        retrieved_candidate_ids=[],
        matching_results=[],
        skill_gaps=[],
        interview_questions=[],
        assessments=[],
        rankings=[],
        errors=[],
        current_node=""
    )
    
    try:
        final_state = compiled_workflow.invoke(full_state)
        return dict(final_state)
    except Exception as e:
        logger.error(f"Hiring Workflow pipeline failed to execute: {e}")
        return {
            **full_state,
            "errors": full_state.get("errors", []) + [f"Pipeline crash: {str(e)}"]
        }
