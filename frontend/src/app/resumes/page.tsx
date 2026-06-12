"use client";

import React, { useState } from "react";
import SidebarLayout from "../../components/SidebarLayout";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../services/api";
import { 
  Upload, 
  Search, 
  User, 
  Mail, 
  FileText, 
  Trash2, 
  CheckCircle, 
  Clock, 
  Sparkles,
  ArrowRight
} from "lucide-react";

export default function ResumesPage() {
  const queryClient = useQueryClient();
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");

  // Fetch resumes
  const { data: resumes = [], isLoading: loadingResumes } = useQuery({
    queryKey: ["resumes"],
    queryFn: async () => {
      const res = await api.get("/resumes/");
      return res.data;
    },
    refetchInterval: (query) => {
      const list = query.state.data as any[] || [];
      const hasPending = list.some(
        (resume: any) => !resume.parsed_data || Object.keys(resume.parsed_data).length === 0
      );
      return hasPending ? 3000 : false;
    }
  });

  // Handle file upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    setError("");
    setUploading(true);
    const formData = new FormData();
    formData.append("file", files[0]);

    try {
      await api.post("/resumes/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      // Refetch resumes list
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to upload file.");
    } finally {
      setUploading(false);
    }
  };

  // Delete resume
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/resumes/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
    }
  });

  // Semantic search handler
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery) return;
    
    setSearching(true);
    try {
      const res = await api.post("/matching/search", {
        query: searchQuery,
        limit: 5
      });
      setSearchResults(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  return (
    <SidebarLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Resumes & Search</h1>
          <p className="text-slate-400 text-sm mt-1">
            Upload candidate resumes, check parsing results, and perform semantic vector searches.
          </p>
        </div>

        {/* Upload & Semantic Search Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* File Upload card */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-6 backdrop-blur-sm">
            <h3 className="font-bold text-white text-base mb-4 flex items-center gap-2">
              <Upload size={18} className="text-indigo-400" />
              Upload Resume
            </h3>

            {error && (
              <div className="p-3.5 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl mb-4 font-semibold">
                {error}
              </div>
            )}

            <div className="border border-dashed border-slate-800 hover:border-slate-700 bg-slate-955 rounded-2xl p-8 text-center transition-all relative overflow-hidden group">
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileUpload}
                disabled={uploading}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              
              <div className="flex flex-col items-center justify-center gap-3">
                <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-xl group-hover:scale-105 transition-transform duration-200">
                  <FileText size={24} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-200">Drag & Drop Resume</p>
                  <p className="text-xs text-slate-500 mt-1">Accepts PDF, DOCX, or TXT (Max 10MB)</p>
                </div>
              </div>

              {uploading && (
                <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-xs flex items-center justify-center flex-col gap-2">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
                  <p className="text-xs text-indigo-400 font-medium animate-pulse">Parsing file...</p>
                </div>
              )}
            </div>
          </div>

          {/* Semantic Search query box */}
          <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800 rounded-3xl p-6 backdrop-blur-sm flex flex-col justify-between">
            <div>
              <h3 className="font-bold text-white text-base mb-2 flex items-center gap-2">
                <Sparkles size={18} className="text-amber-400" />
                Semantic Search Engine
              </h3>
              <p className="text-xs text-slate-500 mb-4">
                Retrieve CVs conceptually. The system embeds your query and searches Qdrant to find matching candidates.
              </p>
            </div>

            <form onSubmit={handleSearch} className="flex gap-2">
              <input
                type="text"
                required
                placeholder="e.g. React Native developers with experience in Stripe and push notifications"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 px-4 py-3 bg-slate-950 border border-slate-850 focus:border-indigo-500 rounded-xl text-sm text-slate-100 placeholder-slate-600 focus:outline-none transition-all duration-200"
              />
              <button
                type="submit"
                disabled={searching}
                className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-xl flex items-center gap-2 transition-all duration-200 shadow-lg shadow-indigo-600/10 disabled:opacity-50"
              >
                {searching ? (
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                ) : (
                  <>
                    <Search size={16} />
                    Search
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Semantic Search Results (Conditional) */}
        {searchResults.length > 0 && (
          <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-6 backdrop-blur-sm space-y-4">
            <h3 className="font-bold text-white text-sm uppercase tracking-wider text-slate-400">Search Results</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {searchResults.map((result: any, i: number) => (
                <div key={i} className="bg-slate-950 border border-slate-850 hover:border-slate-800 rounded-2xl p-5 flex gap-4 transition-all duration-200 relative group overflow-hidden">
                  {/* Score circle */}
                  <div className="absolute top-4 right-4 flex items-center justify-center w-12 h-12 rounded-full border border-indigo-500/20 bg-indigo-500/5 text-indigo-400 font-extrabold text-sm shadow-inner shadow-indigo-500/5">
                    {Math.round(result.score * 100)}%
                  </div>

                  <div className="flex flex-col justify-between flex-1 space-y-3">
                    <div className="space-y-1">
                      <h4 className="font-bold text-white text-base">{result.name}</h4>
                      <p className="text-xs text-slate-500 flex items-center gap-1.5">
                        <Mail size={12} /> {result.email}
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-1.5">
                      {result.skills.slice(0, 5).map((skill: string, j: number) => (
                        <span key={j} className="text-[10px] font-semibold text-slate-400 bg-slate-900 border border-slate-800 px-2.5 py-1 rounded-md">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Resumes Database Table */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-6 backdrop-blur-sm">
          <h3 className="font-bold text-white text-base mb-6">Candidate Database</h3>

          {loadingResumes ? (
            <div className="py-12 text-center text-sm text-slate-500">
              Loading CV list...
            </div>
          ) : resumes.length === 0 ? (
            <div className="py-16 text-center border border-dashed border-slate-850 rounded-2xl flex flex-col items-center justify-center gap-3">
              <FileText size={32} className="text-slate-800" />
              <div>
                <p className="text-sm font-semibold text-slate-400">No resumes found</p>
                <p className="text-xs text-slate-600 mt-1">Upload files using the drag-and-drop box to begin.</p>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-500 text-xs font-semibold uppercase tracking-wider">
                    <th className="py-4 px-2">Document Name</th>
                    <th className="py-4 px-2">Skills Found</th>
                    <th className="py-4 px-2">Created At</th>
                    <th className="py-4 px-2 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850 text-sm">
                  {resumes.map((resume: any) => {
                    const isPending = !resume.parsed_data || Object.keys(resume.parsed_data).length === 0;
                    
                    return (
                      <tr key={resume.id} className="hover:bg-slate-900/20 group">
                        <td className="py-4 px-2">
                          <div className="flex items-center gap-3">
                            {isPending ? (
                              <Clock size={16} className="text-amber-400 animate-pulse shrink-0" />
                            ) : (
                              <CheckCircle size={16} className="text-emerald-400 shrink-0" />
                            )}
                            <span className="font-semibold text-slate-200 truncate max-w-[150px] sm:max-w-[200px]">{resume.filename}</span>
                          </div>
                        </td>
                        <td className="py-4 px-2">
                          <div className="flex flex-wrap gap-1">
                            {isPending ? (
                              <span className="text-[10px] text-slate-500 animate-pulse">Running parsing agent...</span>
                            ) : (
                              resume.parsed_data.skills?.slice(0, 4).map((skill: string, idx: number) => (
                                <span key={idx} className="text-[10px] font-medium text-slate-400 bg-slate-950 border border-slate-850 px-2 py-0.5 rounded">
                                  {skill}
                                </span>
                              ))
                            )}
                          </div>
                        </td>
                        <td className="py-4 px-2 text-xs text-slate-500">
                          {new Date(resume.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-4 px-2 text-right">
                          <button
                            onClick={() => deleteMutation.mutate(resume.id)}
                            className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl transition-all duration-200"
                          >
                            <Trash2 size={16} />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </SidebarLayout>
  );
}
