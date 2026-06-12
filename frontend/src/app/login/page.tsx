"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "../../store/auth";
import { api } from "../../services/api";
import { Cpu, CheckCircle2, AlertCircle, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated } = useAuthStore();
  
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [orgName, setOrgName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isLogin) {
        const res = await api.post("/auth/login", { email, password });
        login(res.data.access_token, res.data.organization_id, res.data.role, email);
        router.push("/dashboard");
      } else {
        if (!orgName) {
          setError("Organization Name is required");
          setLoading(false);
          return;
        }
        const res = await api.post("/auth/register", {
          email,
          password,
          organization_name: orgName,
          role: "recruiter"
        });
        login(res.data.access_token, res.data.organization_id, res.data.role, email);
        router.push("/dashboard");
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        "Something went wrong. Please check your inputs and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-950">
      {/* Left panel - Hero & Brand info */}
      <div className="hidden lg:flex lg:w-1/2 bg-slate-900 border-r border-slate-800 flex-col justify-between p-12 relative overflow-hidden">
        {/* Glow effect */}
        <div className="absolute top-[-10%] right-[-10%] w-96 h-96 rounded-full bg-indigo-500/10 blur-3xl" />
        <div className="absolute bottom-[-10%] left-[-10%] w-96 h-96 rounded-full bg-emerald-500/5 blur-3xl" />

        {/* Brand */}
        <div className="flex items-center gap-3 z-10">
          <div className="p-2.5 bg-indigo-600 rounded-xl text-white shadow-lg shadow-indigo-500/20">
            <Cpu size={24} className="animate-spin-slow" />
          </div>
          <span className="font-bold text-xl text-white tracking-wide">Agentic Hiring Copilot</span>
        </div>

        {/* Dynamic features checklist */}
        <div className="my-auto max-w-md z-10 space-y-8">
          <div className="space-y-4">
            <span className="text-xs text-indigo-400 font-semibold uppercase tracking-wider bg-indigo-500/10 px-3 py-1.5 rounded-full">
              Recruitment Automation
            </span>
            <h2 className="text-3xl font-extrabold text-white leading-tight">
              Smarter hiring workflows powered by AI Agents.
            </h2>
            <p className="text-slate-400 text-sm leading-relaxed">
              Parse CVs, search profiles semantically, run structured skill-gap roadmaps, and generate tailor-made interview assessments in a click.
            </p>
          </div>

          <div className="space-y-4">
            {[
              "Multi-tenant organization data isolation",
              "Agentic workflow execution telemetry",
              "Semantic resume parsing & vector search",
              "Custom assessments & coding challenges"
            ].map((feature, i) => (
              <div key={i} className="flex items-center gap-3">
                <CheckCircle2 size={18} className="text-indigo-400 shrink-0" />
                <span className="text-sm text-slate-300 font-medium">{feature}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer info */}
        <div className="z-10 text-xs text-slate-500">
          © {new Date().getFullYear()} Agentic Hiring Copilot. Production Grade Platform.
        </div>
      </div>

      {/* Right panel - Credentials Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 md:p-12 relative">
        {/* Glow effect */}
        <div className="absolute top-[20%] left-[30%] w-80 h-80 rounded-full bg-indigo-600/5 blur-3xl" />

        <div className="w-full max-w-md bg-slate-900/40 border border-slate-800 rounded-3xl p-8 backdrop-blur-xl shadow-2xl relative z-10">
          {/* Header */}
          <div className="text-center mb-8">
            <h3 className="text-2xl font-bold text-white mb-2">
              {isLogin ? "Welcome back" : "Get started"}
            </h3>
            <p className="text-slate-400 text-sm">
              {isLogin ? "Sign in to manage your pipeline" : "Create a tenant organization account"}
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-2xl flex gap-3 text-sm font-medium">
                <AlertCircle size={18} className="shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {!isLogin && (
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Organization Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Acme Corporation"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-950 border border-slate-800 hover:border-slate-700 focus:border-indigo-500 rounded-xl text-sm text-slate-100 placeholder-slate-600 focus:outline-none transition-all duration-200"
                />
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Email Address
              </label>
              <input
                type="email"
                required
                placeholder="recruiter@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-slate-950 border border-slate-800 hover:border-slate-700 focus:border-indigo-500 rounded-xl text-sm text-slate-100 placeholder-slate-600 focus:outline-none transition-all duration-200"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Password
              </label>
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-slate-950 border border-slate-800 hover:border-slate-700 focus:border-indigo-500 rounded-xl text-sm text-slate-100 placeholder-slate-600 focus:outline-none transition-all duration-200"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm rounded-xl transition-all duration-200 shadow-lg shadow-indigo-600/30 disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              {loading ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <>
                  {isLogin ? "Sign In" : "Register Organization"}
                  <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Toggle Tab */}
          <div className="text-center mt-6">
            <button
              onClick={() => {
                setError("");
                setIsLogin(!isLogin);
              }}
              className="text-xs font-medium text-slate-400 hover:text-indigo-400 transition-colors"
            >
              {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
