"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { 
  LayoutDashboard, 
  FileText, 
  Briefcase, 
  LogOut, 
  Cpu, 
  Layers 
} from "lucide-react";
import { useAuthStore } from "../store/auth";

interface SidebarLayoutProps {
  children: React.ReactNode;
}

export default function SidebarLayout({ children }: SidebarLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, userEmail, logout } = useAuthStore();
  const [mounted, setMounted] = React.useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, router, mounted]);

  if (!mounted) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-slate-400">
        Loading session...
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const navItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Resumes & Search", href: "/resumes", icon: FileText },
    { name: "Jobs & Pipelines", href: "/jobs", icon: Briefcase },
  ];

  return (
    <div className="flex min-h-screen bg-slate-950">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/50 backdrop-blur-md flex flex-col fixed h-full z-10">
        {/* Brand Logo */}
        <div className="p-6 border-b border-slate-800 flex items-center gap-3">
          <div className="p-2 bg-indigo-600 rounded-lg text-white shadow-lg shadow-indigo-500/30">
            <Cpu size={20} className="animate-pulse" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-white leading-none">Hiring Copilot</h1>
            <span className="text-xs text-indigo-400 font-medium tracking-wide uppercase">AI Multi-Tenant</span>
          </div>
        </div>

        {/* Navigation links */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            const Icon = item.icon;
            
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl font-medium text-sm transition-all duration-200 ${
                  isActive 
                    ? "bg-indigo-600/10 text-indigo-400 border-l-4 border-indigo-500 shadow-md shadow-indigo-500/5" 
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                }`}
              >
                <Icon size={18} />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* Footer profile & logout */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/30">
          <div className="flex items-center gap-3 mb-4 px-2">
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-indigo-400 text-xs uppercase shadow-inner">
              {userEmail ? userEmail.substring(0, 2) : "US"}
            </div>
            <div className="overflow-hidden">
              <p className="text-xs text-slate-400 font-medium truncate">{userEmail}</p>
              <p className="text-[10px] text-slate-500">Recruiter Profile</p>
            </div>
          </div>
          
          <button
            onClick={() => {
              logout();
              router.push("/login");
            }}
            className="flex items-center gap-2 justify-center w-full px-4 py-2.5 rounded-xl border border-slate-850 hover:border-rose-500/30 hover:bg-rose-500/5 hover:text-rose-400 text-slate-400 text-sm font-medium transition-all duration-200"
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 ml-64 min-h-screen flex flex-col">
        <div className="flex-1 p-8 md:p-10 max-w-7xl w-full mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
