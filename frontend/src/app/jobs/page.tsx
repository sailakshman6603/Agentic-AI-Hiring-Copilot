"use client";

import React, { useState } from "react";
import SidebarLayout from "../../components/SidebarLayout";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../services/api";
import { useRouter } from "next/navigation";
import { 
  Briefcase, 
  Play, 
  Trash2, 
  CheckCircle2, 
  ArrowRight,
  PlusCircle
} from "lucide-react";

export default function JobsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [rawText, setRawText] = useState("");
  const [creating, setCreating] = useState(false);
  const [runningId, setRunningId] = useState<string | null>(null);

  // Fetch JDs
  const { data: jobs = [], isLoading: loadingJobs } = useQuery({
    queryKey: ["jobs"],
    queryFn: async () => {
      const res = await api.get("/jobs/");
      return res.data;
    }
  });

  // Create JD Mutation
  const createMutation = useMutation({
    mutationFn: async (data: { title: string; raw_text: string }) => {
      const res = await api.post("/jobs/", data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setTitle("");
      setRawText("");
    }
  });

  // Run pipeline Mutation
  const runMutation = useMutation({
    mutationFn: async (jdId: string) => {
      const res = await api.post("/matching/run", { job_description_id: jdId });
      return res.data;
    },
    onSuccess: (data) => {
      // Redirect to execution visualization
      router.push(`/matching/${data.id}`);
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await createMutation.mutateAsync({ title, raw_text: rawText });
    } catch (err) {
      console.error(err);
    } finally {
      setCreating(false);
    }
  };

  const handleRunPipeline = async (jdId: string) => {
    setRunningId(jdId);
    try {
      await runMutation.mutateAsync(jdId);
    } catch (err) {
      console.error(err);
      setRunningId(null);
    }
  };

  // Delete Job
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/jobs/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    }
  });

  return (
    <SidebarLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Jobs & Matching</h1>
          <p className="text-slate-400 text-sm mt-1">
            Setup Job Descriptions and trigger the AI candidate screening & matching agents.
          </p>
        </div>

        {/* Input Form & List Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Configure Job Card */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-6 backdrop-blur-sm h-fit">
            <h3 className="font-bold text-white text-base mb-4 flex items-center gap-2">
              <PlusCircle size={18} className="text-indigo-400" />
              Configure Job
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Job Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Senior Backend Architect"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-950 border border-slate-850 focus:border-indigo-500 rounded-xl text-sm text-slate-100 placeholder-slate-650 focus:outline-none transition-all duration-200"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Job Requirements (Paste JD)
                </label>
                <textarea
                  required
                  rows={6}
                  placeholder="Paste roles, responsibilities, required and preferred skills..."
                  value={rawText}
                  onChange={(e) => setRawText(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-950 border border-slate-850 focus:border-indigo-500 rounded-xl text-sm text-slate-100 placeholder-slate-650 focus:outline-none transition-all duration-200 resize-none"
                />
              </div>

              <button
                type="submit"
                disabled={creating}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm rounded-xl transition-all duration-200 shadow-lg shadow-indigo-600/15 disabled:opacity-50"
              >
                {creating ? "Saving..." : "Save Job Description"}
              </button>
            </form>
          </div>

          {/* Jobs List database card */}
          <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800 rounded-3xl p-6 backdrop-blur-sm">
            <h3 className="font-bold text-white text-base mb-6">Job Catalog</h3>

            {loadingJobs ? (
              <div className="py-12 text-center text-sm text-slate-500">
                Loading jobs...
              </div>
            ) : jobs.length === 0 ? (
              <div className="py-16 text-center border border-dashed border-slate-850 rounded-2xl flex flex-col items-center justify-center gap-3">
                <Briefcase size={32} className="text-slate-850" />
                <div>
                  <p className="text-sm font-semibold text-slate-400">No job catalogs setup</p>
                  <p className="text-xs text-slate-600 mt-1">Configure a job description card to start matching.</p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {jobs.map((job: any) => {
                  const isRunning = runningId === job.id;
                  
                  return (
                    <div
                      key={job.id}
                      className="p-5 bg-slate-950 border border-slate-850 hover:border-slate-800 rounded-2xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 transition-all duration-200"
                    >
                      <div className="space-y-1.5">
                        <h4 className="font-bold text-white text-base">{job.title}</h4>
                        <p className="text-xs text-slate-500">
                          Created on {new Date(job.created_at).toLocaleDateString()}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleRunPipeline(job.id)}
                          disabled={isRunning || runMutation.isPending}
                          className="px-4 py-2 bg-indigo-600/10 hover:bg-indigo-600 text-indigo-400 hover:text-white border border-indigo-500/20 hover:border-indigo-500 text-xs font-semibold rounded-xl flex items-center gap-2 transition-all duration-200"
                        >
                          {isRunning ? (
                            <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent" />
                          ) : (
                            <Play size={12} className="fill-current" />
                          )}
                          Screen Candidates
                        </button>
                        
                        <button
                          onClick={() => deleteMutation.mutate(job.id)}
                          className="p-2.5 text-slate-600 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl transition-all duration-200"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
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
