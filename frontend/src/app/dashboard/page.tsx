"use client";

import React from "react";
import SidebarLayout from "../../components/SidebarLayout";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../services/api";
import { 
  FileText, 
  Briefcase, 
  PlayCircle, 
  TrendingUp, 
  Clock, 
  CheckCircle2, 
  AlertCircle 
} from "lucide-react";
import Link from "next/link";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from "recharts";

export default function DashboardPage() {
  // Fetch summaries
  const { data: resumes = [], isLoading: loadingResumes } = useQuery({
    queryKey: ["resumes"],
    queryFn: async () => {
      const res = await api.get("/resumes/");
      return res.data;
    }
  });

  const { data: jobs = [], isLoading: loadingJobs } = useQuery({
    queryKey: ["jobs"],
    queryFn: async () => {
      const res = await api.get("/jobs/");
      return res.data;
    }
  });

  const { data: runs = [], isLoading: loadingRuns } = useQuery({
    queryKey: ["runs"],
    queryFn: async () => {
      const res = await api.get("/matching/runs");
      return res.data;
    }
  });

  // Calculate high-level stats
  const totalResumes = resumes.length;
  const totalJobs = jobs.length;
  const totalRuns = runs.length;
  const activeRuns = runs.filter((r: any) => r.status === "running" || r.status === "pending").length;
  const completedRuns = runs.filter((r: any) => r.status === "completed").length;
  const failedRuns = runs.filter((r: any) => r.status === "failed").length;

  // Mock data for Recharts matching trend
  const chartData = [
    { name: "Mon", score: 65 },
    { name: "Tue", score: 72 },
    { name: "Wed", score: 85 },
    { name: "Thu", score: 80 },
    { name: "Fri", score: 88 },
    { name: "Sat", score: 90 },
    { name: "Sun", score: 87 }
  ];

  return (
    <SidebarLayout>
      <div className="space-y-8">
        {/* Welcome Banner */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">Hiring Dashboard</h1>
            <p className="text-slate-400 text-sm mt-1">
              Overview of your AI recruitment pipeline and tenant metrics.
            </p>
          </div>
          
          <div className="flex gap-3">
            <Link 
              href="/resumes" 
              className="px-4 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-200 text-sm font-semibold rounded-xl transition-all duration-200"
            >
              Upload Resumes
            </Link>
            <Link 
              href="/jobs" 
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-xl transition-all duration-200 shadow-lg shadow-indigo-600/20"
            >
              Configure Job
            </Link>
          </div>
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { 
              label: "Parsed Resumes", 
              value: loadingResumes ? "..." : totalResumes, 
              icon: FileText, 
              color: "text-indigo-400", 
              bg: "bg-indigo-500/10" 
            },
            { 
              label: "Active Jobs", 
              value: loadingJobs ? "..." : totalJobs, 
              icon: Briefcase, 
              color: "text-emerald-400", 
              bg: "bg-emerald-500/10" 
            },
            { 
              label: "Matching Pipelines", 
              value: loadingRuns ? "..." : totalRuns, 
              icon: PlayCircle, 
              color: "text-amber-400", 
              bg: "bg-amber-500/10" 
            },
            { 
              label: "Active Executions", 
              value: loadingRuns ? "..." : activeRuns, 
              icon: Clock, 
              color: "text-sky-400", 
              bg: "bg-sky-500/10" 
            }
          ].map((card, i) => {
            const Icon = card.icon;
            return (
              <div key={i} className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 relative overflow-hidden group hover:border-slate-700 transition-colors">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{card.label}</p>
                    <h4 className="text-3xl font-extrabold text-white mt-2 tracking-tight">{card.value}</h4>
                  </div>
                  <div className={`p-2.5 rounded-xl ${card.color} ${card.bg}`}>
                    <Icon size={20} />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Visual Charts & List */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recharts Analytics Area */}
          <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800 rounded-3xl p-6 backdrop-blur-sm">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="font-bold text-white text-base">Match Quality Index</h3>
                <p className="text-xs text-slate-500 mt-0.5">Scoring average of top matched profiles</p>
              </div>
              <div className="flex items-center gap-1 text-xs text-emerald-400 font-semibold bg-emerald-500/10 px-2.5 py-1 rounded-full">
                <TrendingUp size={12} />
                +8.2%
              </div>
            </div>
            
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                    labelStyle={{ color: '#94a3b8', fontSize: '11px', fontWeight: 'bold' }}
                    itemStyle={{ color: '#f8fafc', fontSize: '12px' }}
                  />
                  <Area type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2.5} fillOpacity={1} fill="url(#colorScore)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Recent Runs List */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-6 backdrop-blur-sm flex flex-col">
            <h3 className="font-bold text-white text-base mb-4">Pipeline History</h3>
            
            {loadingRuns ? (
              <div className="flex-1 flex items-center justify-center text-xs text-slate-500">
                Loading runs...
              </div>
            ) : runs.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-6 border border-dashed border-slate-800 rounded-2xl">
                <Clock size={24} className="text-slate-700 mb-2" />
                <p className="text-xs text-slate-500">No pipelines executed yet.</p>
              </div>
            ) : (
              <div className="flex-1 space-y-4 overflow-y-auto max-h-[260px] pr-1">
                {runs.slice(0, 5).map((run: any) => {
                  const jd = jobs.find((j: any) => j.id === run.job_description_id);
                  const isCompleted = run.status === "completed";
                  const isFailed = run.status === "failed";
                  
                  return (
                    <Link
                      key={run.id}
                      href={`/matching/${run.id}`}
                      className="flex items-center justify-between p-3 bg-slate-950 border border-slate-850 hover:border-slate-800 rounded-xl transition-all duration-200 group"
                    >
                      <div className="overflow-hidden">
                        <p className="text-xs font-bold text-slate-200 group-hover:text-indigo-400 transition-colors truncate">
                          {jd?.title || "Matching Pipeline"}
                        </p>
                        <p className="text-[10px] text-slate-500 mt-0.5">
                          {new Date(run.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      
                      <div className="flex items-center gap-1.5 font-semibold text-[10px] uppercase tracking-wider px-2 py-1 rounded-md">
                        {isCompleted && (
                          <span className="text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full flex items-center gap-1">
                            <CheckCircle2 size={10} /> Done
                          </span>
                        )}
                        {isFailed && (
                          <span className="text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full flex items-center gap-1">
                            <AlertCircle size={10} /> Fail
                          </span>
                        )}
                        {!isCompleted && !isFailed && (
                          <span className="text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded-full flex items-center gap-1 animate-pulse">
                            Processing
                          </span>
                        )}
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </SidebarLayout>
  );
}
