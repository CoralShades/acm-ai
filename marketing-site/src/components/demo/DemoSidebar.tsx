"use client";

import { useEffect, useRef, useState } from "react";
import {
  Building,
  Zap,
  Table,
  MessageSquare,
  Download,
  TrendingUp,
  Settings,
  Users,
  Shield,
} from "lucide-react";
import { cn } from "@/lib/cn";

const sections = [
  { id: "overview", icon: Building, label: "Overview", key: "1" },
  { id: "pipeline", icon: Zap, label: "Pipeline", key: "2" },
  { id: "spreadsheet", icon: Table, label: "Spreadsheet", key: "3" },
  { id: "chat", icon: MessageSquare, label: "Chat", key: "4" },
  { id: "export", icon: Download, label: "Export", key: "5" },
  { id: "progress", icon: TrendingUp, label: "Progress", key: "6" },
  { id: "architecture", icon: Settings, label: "Architecture", key: "7" },
  { id: "stakeholders", icon: Users, label: "Stakeholders", key: "8" },
];

export function DemoSidebar() {
  const [activeSection, setActiveSection] = useState("overview");
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    const sectionElements = sections.map((s) =>
      document.getElementById(s.id)
    );

    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      {
        rootMargin: "-40% 0px -50% 0px",
        threshold: 0,
      }
    );

    sectionElements.forEach((el) => {
      if (el) observerRef.current?.observe(el);
    });

    return () => observerRef.current?.disconnect();
  }, []);

  function scrollToSection(id: string) {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName.toLowerCase();
      if (tag === "input" || tag === "textarea") return;
      const idx = parseInt(e.key, 10) - 1;
      if (idx >= 0 && idx < sections.length) {
        scrollToSection(sections[idx].id);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <aside className="hidden lg:flex w-14 shrink-0 flex-col fixed top-0 left-0 h-screen z-40 border-r border-white/10 bg-vaea-navy">
      {/* Logo mark */}
      <div className="flex items-center justify-center h-14 border-b border-white/10 shrink-0">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-vaea-teal-300">
          <Shield size={16} className="text-white" />
        </div>
      </div>

      {/* Nav icons */}
      <nav className="flex-1 flex flex-col items-center py-3 gap-1 overflow-y-auto">
        {sections.map((s) => {
          const Icon = s.icon;
          const isActive = activeSection === s.id;
          return (
            <button
              key={s.id}
              onClick={() => scrollToSection(s.id)}
              title={`${s.label} (${s.key})`}
              aria-label={s.label}
              className={cn(
                "group relative w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-200",
                isActive
                  ? "bg-vaea-teal-300/20"
                  : "hover:bg-white/8"
              )}
            >
              <Icon
                size={18}
                className={cn(
                  "transition-colors duration-200",
                  isActive ? "text-vaea-teal-300" : "text-white/40 group-hover:text-white/70"
                )}
              />
              {isActive && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 rounded-r bg-vaea-teal-300" />
              )}
              {/* Tooltip */}
              <span className="absolute left-full ml-2 px-2 py-1 rounded text-xs font-medium whitespace-nowrap bg-vaea-navy-light text-white opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-150 z-50 shadow-lg border border-white/10">
                {s.label}
                <span className="ml-1.5 text-white/40 font-[family-name:var(--font-jetbrains-mono)] text-[10px]">{s.key}</span>
              </span>
            </button>
          );
        })}
      </nav>

      {/* Bottom status */}
      <div className="flex items-center justify-center h-12 border-t border-white/10 shrink-0">
        <div className="w-2 h-2 rounded-full bg-vaea-green-500 animate-pulse" title="Feature Complete" />
      </div>
    </aside>
  );
}
