"use client";

import React, { useState } from "react";
import SidebarLayout from "../../../components/SidebarLayout";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../../services/api";
import { 
  Cpu, 
  CheckCircle, 
  AlertTriangle, 
  User, 
  Search, 
  TrendingUp, 
  FileText, 
  ArrowLeft,
  Award,
  Layers,
  ChevronRight,
  Sparkles,
  ClipboardList
} from "lucide-react";

export default function MatchingDetailPage() {
  const router = useRouter();
  const { runId } = useParams();
  
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [activeReportTab, setActiveReportTab] = useState<"match" | "gap" | "interview" | "assessment">("match");

  // Fetch pipeline status (polls every 2 seconds if status is running/pending)
  const { data: run, isLoading: loadingRun } = useQuery({
    queryKey: ["run", runId],
    queryFn: async () => {
      const res = await api.get(`/matching/runs/${runId}`);
      return res.data;
    },
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "running" ? 2000 : false;
    }
  });

  // Fetch job title
  const { data: jobs = [] } = useQuery({
    queryKey: ["jobs"],
    queryFn: async () => {
      const res = await api.get("/jobs/");
      return res.data;
    }
  });

  const job = jobs.find((j: any) => j.id === run?.job_description_id);
  const graphState = run?.graph_state || {};
  const currentNode = graphState.current_node || "";
  const rankings = graphState.rankings || [];
  const matchingResults = graphState.matching_results || [];
  const skillGaps = graphState.skill_gaps || [];
  const interviewQuestions = graphState.interview_questions || [];
  const assessments = graphState.assessments || [];

  // Default select first ranked candidate once loaded
  React.useEffect(() => {
    if (rankings.length > 0 && !selectedCandidateId) {
      setSelectedCandidateId(rankings[0].candidate_id);
    }
  }, [rankings, selectedCandidateId]);

  // Node checklist for visual graph representation
  const workflowNodes = [
    { id: "ResumeParserAgent", label: "Resume Parse" },
    { id: "JDAnalyzerAgent", label: "JD Analyze" },
    { id: "CandidateRetrievalAgent", label: "Retrieve CVs" },
    { id: "MatchingAgent", label: "Screening" },
    { id: "SkillGapAgent", label: "Gap Analysis" },
    { id: "InterviewGeneratorAgent", label: "Interview Set" },
    { id: "AssessmentGeneratorAgent", label: "Test Design" },
    { id: "RankingAgent", label: "Final Rank" }
  ];

  const getActiveNodeIndex = () => {
    return workflowNodes.findIndex(node => node.id === currentNode);
  };

  const activeNodeIdx = getActiveNodeIndex();

  // Selected candidate reports
  const selectedCandidateRank = rankings.find((c: any) => c.candidate_id === selectedCandidateId);
  const selectedCandidateMatch = matchingResults.find((c: any) => c.candidate_id === selectedCandidateId);
  const selectedCandidateGap = skillGaps.find((c: any) => c.candidate_id === selectedCandidateId);
  const selectedCandidateInterview = interviewQuestions.find((c: any) => c.candidate_id === selectedCandidateId);
  const selectedCandidateAssessment = assessments.find((c: any) => c.candidate_id === selectedCandidateId);

  return (
    <SidebarLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push("/jobs")}
            className="p-2 bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200 rounded-xl transition-all"
          >
            <ArrowLeft size={16} />
          </button>
          <div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              {job ? `${job.title} Matching` : "Matching Pipeline"}
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Pipeline ID: <span className="font-mono text-xs text-indigo-400">{runId}</span>
            </p>
          </div>
        </div>

        {/* Telemetry Workflow Indicator */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-6 backdrop-blur-sm space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-bold text-white text-base">Agent Orchestration Telemetry</h3>
              <p className="text-xs text-slate-500 mt-0.5">LangGraph Workflow state machine status</p>
            </div>
            
            <div className="flex items-center gap-2">
              <span className={`h-2.5 w-2.5 rounded-full ${
                run?.status === "completed" 
                  ? "bg-emerald-500" 
                  : run?.status === "failed" 
                  ? "bg-rose-500" 
                  : "bg-indigo-500 animate-ping"
              }`} />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                {run?.status || "loading"}
              </span>
            </div>
          </div>

          {/* Graphical nodes track */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 relative">
            {workflowNodes.map((node, idx) => {
              const isPast = activeNodeIdx > idx || run?.status === "completed";
              const isCurrent = currentNode === node.id && run?.status !== "completed" && run?.status !== "failed";
              
              return (
                <div 
                  key={node.id}
                  className={`p-3 border rounded-xl flex flex-col justify-between h-20 transition-all duration-300 ${
                    isCurrent 
                      ? "bg-indigo-600/10 border-indigo-500 shadow-md shadow-indigo-500/5" 
                      : isPast 
                      ? "bg-slate-900/40 border-emerald-500/30 text-slate-400" 
                      : "bg-slate-950/20 border-slate-850 text-slate-600"
                  }`}
                >
                  <span className="text-[10px] font-bold tracking-wider text-slate-500">STEP 0{idx + 1}</span>
                  <div className="flex items-center gap-1.5 justify-between">
                    <span className={`text-xs font-bold ${isCurrent ? "text-indigo-400" : isPast ? "text-slate-300" : "text-slate-500"}`}>
                      {node.label}
                    </span>
                    {isPast && <CheckCircle size={12} className="text-emerald-500 shrink-0" />}
                    {isCurrent && <div className="h-2 w-2 rounded-full bg-indigo-500 animate-ping shrink-0" />}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Failed Pipeline Run Alert */}
        {run?.status === "failed" && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-2xl flex gap-3 text-sm font-semibold">
            <AlertTriangle size={18} className="shrink-0 mt-0.5" />
            <div>
              <p>Pipeline run failed. Errors encountered:</p>
              <ul className="list-disc pl-5 mt-2 font-mono text-xs">
                {graphState.errors?.map((err: string, i: number) => <li key={i}>{err}</li>) || <li>Unknown error</li>}
              </ul>
            </div>
          </div>
        )}

        {/* Pipeline Completed: Render Matching Report */}
        {run?.status === "completed" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Col: Ranked Candidates checklist */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-6 backdrop-blur-sm h-fit">
              <h3 className="font-bold text-white text-base mb-4 flex items-center gap-2">
                <Award size={18} className="text-indigo-400" />
                Rankings
              </h3>
              
              <div className="space-y-3">
                {rankings.map((c: any) => {
                  const isSelected = selectedCandidateId === c.candidate_id;
                  
                  return (
                    <button
                      key={c.candidate_id}
                      onClick={() => setSelectedCandidateId(c.candidate_id)}
                      className={`w-full text-left p-4 rounded-2xl border transition-all duration-200 flex items-center justify-between gap-3 ${
                        isSelected 
                          ? "bg-indigo-600/10 border-indigo-500 shadow-lg shadow-indigo-500/5" 
                          : "bg-slate-950 border-slate-850 hover:border-slate-800"
                      }`}
                    >
                      <div className="overflow-hidden space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full">
                            Rank #{c.rank}
                          </span>
                          <span className="text-xs text-slate-500">Score: {c.score}%</span>
                        </div>
                        <h4 className="font-bold text-white text-sm truncate">{c.candidate_name}</h4>
                      </div>
                      
                      <ChevronRight size={16} className={`text-slate-650 transition-transform ${isSelected ? "translate-x-1" : ""}`} />
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Right Col: Multi-Agent details report for selected candidate */}
            <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800 rounded-3xl p-6 backdrop-blur-sm flex flex-col space-y-6">
              {/* Report Header */}
              {selectedCandidateRank && (
                <div className="p-4 bg-slate-950 border border-slate-850 rounded-2xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div>
                    <h3 className="font-bold text-white text-lg">{selectedCandidateRank.candidate_name}</h3>
                    <p className="text-xs text-indigo-400 font-semibold mt-0.5">Rank Placement: #{selectedCandidateRank.rank}</p>
                  </div>
                  <p className="text-xs text-slate-500 max-w-sm sm:text-right leading-relaxed italic">
                    &ldquo;{selectedCandidateRank.key_reason}&rdquo;
                  </p>
                </div>
              )}

              {/* Detail Tabs */}
              <div className="flex border-b border-slate-850">
                {[
                  { id: "match", label: "Match Score", icon: TrendingUp },
                  { id: "gap", label: "Skill Gaps", icon: Layers },
                  { id: "interview", label: "Interviews", icon: ClipboardList },
                  { id: "assessment", label: "Coding Tests", icon: Sparkles }
                ].map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeReportTab === tab.id;
                  
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveReportTab(tab.id as any)}
                      className={`flex items-center gap-2 px-5 py-3 font-semibold text-xs transition-all duration-200 border-b-2 -mb-[2px] ${
                        isActive 
                          ? "border-indigo-500 text-indigo-400" 
                          : "border-transparent text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <Icon size={14} />
                      {tab.label}
                    </button>
                  );
                })}
              </div>

              {/* Tab Contents */}
              <div className="flex-1 space-y-4">
                {/* 1. Match Report Tab */}
                {activeReportTab === "match" && selectedCandidateMatch && (
                  <div className="space-y-5">
                    <div className="flex items-center gap-4">
                      {/* Giant score circle */}
                      <div className="flex items-center justify-center w-16 h-16 rounded-2xl border border-indigo-500/25 bg-indigo-500/5 text-indigo-400 font-extrabold text-2xl shadow-inner">
                        {selectedCandidateMatch.score}%
                      </div>
                      <div>
                        <h4 className="font-bold text-white text-sm">Overall Alignment Rating</h4>
                        <p className="text-xs text-slate-500 mt-0.5">Evaluated against parsed job skills and experience</p>
                      </div>
                    </div>

                    <div className="space-y-1 bg-slate-950/40 p-4 border border-slate-850 rounded-2xl">
                      <h5 className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Overall Fit Summary</h5>
                      <p className="text-sm text-slate-300 leading-relaxed mt-1">{selectedCandidateMatch.overall_fit_summary}</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-emerald-500/5 border border-emerald-500/10 p-4 rounded-2xl space-y-2">
                        <h5 className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Core Strengths</h5>
                        <ul className="list-disc pl-4 text-xs text-slate-300 space-y-1.5">
                          {selectedCandidateMatch.strengths.map((str: string, i: number) => <li key={i}>{str}</li>)}
                        </ul>
                      </div>

                      <div className="bg-rose-500/5 border border-rose-500/10 p-4 rounded-2xl space-y-2">
                        <h5 className="text-xs font-bold text-rose-400 uppercase tracking-wider">Key Weaknesses / Gaps</h5>
                        <ul className="list-disc pl-4 text-xs text-slate-300 space-y-1.5">
                          {selectedCandidateMatch.weaknesses.map((weak: string, i: number) => <li key={i}>{weak}</li>)}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}

                {/* 2. Skill Gaps Tab */}
                {activeReportTab === "gap" && selectedCandidateGap && (
                  <div className="space-y-6">
                    <div className="bg-slate-950/40 p-4 border border-slate-850 rounded-2xl">
                      <h5 className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Upskilling Recommendations</h5>
                      <p className="text-sm text-slate-300 leading-relaxed mt-1">{selectedCandidateGap.upskilling_recommendations}</p>
                    </div>

                    <div className="space-y-3">
                      <h5 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Level Gaps</h5>
                      
                      {selectedCandidateGap.level_gaps.length === 0 ? (
                        <p className="text-xs text-slate-600 italic">No significant level gaps detected.</p>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {selectedCandidateGap.level_gaps.map((gap: any, i: number) => (
                            <div key={i} className="p-3.5 bg-slate-950 border border-slate-850 rounded-xl flex justify-between items-center text-xs">
                              <div>
                                <p className="font-bold text-slate-200">{gap.skill}</p>
                                <p className="text-[10px] text-slate-500 mt-0.5">Required: {gap.required}</p>
                              </div>
                              <span className="text-[10px] font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full">
                                Candidate has: {gap.candidate_has}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* 3. Interview Set Tab */}
                {activeReportTab === "interview" && selectedCandidateInterview && (
                  <div className="space-y-4">
                    <h5 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Structured Interview Questions</h5>
                    
                    <div className="space-y-4">
                      {selectedCandidateInterview.questions?.map((q: any, i: number) => (
                        <div key={i} className="p-4 bg-slate-950 border border-slate-850 rounded-2xl space-y-3">
                          <div className="flex justify-between items-center">
                            <span className="text-[10px] font-bold text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full">
                              Question #{i + 1}
                            </span>
                            <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">
                              Topic: {q.topic}
                            </span>
                          </div>
                          
                          <p className="text-sm font-bold text-slate-200">{q.question}</p>
                          
                          <div className="p-3 bg-slate-900/50 border border-slate-850/50 rounded-xl text-xs">
                            <p className="font-bold text-slate-400 uppercase tracking-wider text-[9px] mb-1">Expected Answer Criteria</p>
                            <p className="text-slate-350 leading-relaxed">{q.expected_answer}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 4. Assessments Tab */}
                {activeReportTab === "assessment" && selectedCandidateAssessment && (
                  <div className="space-y-6">
                    {/* Coding Challenges */}
                    {selectedCandidateAssessment.coding_challenges?.length > 0 && (
                      <div className="space-y-3">
                        <h5 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Coding Challenge</h5>
                        
                        {selectedCandidateAssessment.coding_challenges.map((challenge: any, i: number) => (
                          <div key={i} className="p-4 bg-slate-950 border border-slate-850 rounded-2xl space-y-3">
                            <h6 className="text-sm font-bold text-slate-250">{challenge.title}</h6>
                            <p className="text-xs text-slate-450 leading-relaxed">{challenge.description}</p>
                            
                            <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl font-mono text-xs text-indigo-300 overflow-x-auto">
                              <pre>{challenge.starter_code}</pre>
                            </div>
                            
                            <div className="text-[11px] text-slate-500 bg-slate-900/50 p-2.5 rounded-lg border border-slate-850">
                              <span className="font-bold text-slate-400">Test Cases:</span> {challenge.test_cases}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Multiple Choice */}
                    {selectedCandidateAssessment.multiple_choice?.length > 0 && (
                      <div className="space-y-4">
                        <h5 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Multiple Choice Questions</h5>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {selectedCandidateAssessment.multiple_choice.map((mcq: any, i: number) => (
                            <div key={i} className="p-4 bg-slate-950 border border-slate-850 rounded-2xl space-y-3 text-xs">
                              <p className="font-bold text-slate-200 leading-relaxed">{mcq.question}</p>
                              
                              <div className="space-y-1.5">
                                {mcq.options.map((opt: string, idx: number) => (
                                  <div 
                                    key={idx} 
                                    className={`p-2 rounded-lg border text-slate-400 ${
                                      opt === mcq.correct_answer 
                                        ? "bg-emerald-500/5 border-emerald-500/20 text-emerald-400" 
                                        : "bg-slate-900 border-slate-850"
                                    }`}
                                  >
                                    {opt} {opt === mcq.correct_answer && "(Correct)"}
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </SidebarLayout>
  );
}
