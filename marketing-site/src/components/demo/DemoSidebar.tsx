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
  ChevronLeft,
  ChevronRight,
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
  const [expanded, setExpanded] = useState(false);
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
    <>
      {/* ── Desktop Sidebar (lg+) ── */}
      <aside
        className={cn(
          "hidden lg:flex flex-col fixed top-16 left-0 z-40 border-r border-white/10 bg-vaea-navy transition-all duration-200 ease-in-out",
          expanded ? "w-52" : "w-14"
        )}
        style={{ height: "calc(100vh - 4rem)" }}
        onMouseEnter={() => setExpanded(true)}
        onMouseLeave={() => setExpanded(false)}
      >
        {/* Logo mark + collapse toggle */}
        <div className="flex items-center h-12 border-b border-white/10 shrink-0 px-3 gap-2">
          <img
            src="/acm-icon.svg"
            alt="ACM-AI"
            width={32}
            height={32}
            className="w-8 h-8 rounded-lg shrink-0"
          />
          {expanded && (
            <span className="text-sm font-semibold text-white/80 whitespace-nowrap overflow-hidden">
              Demo Sections
            </span>
          )}
          <button
            onClick={() => setExpanded((v) => !v)}
            className="ml-auto text-white/40 hover:text-white/70 transition-colors shrink-0"
            aria-label={expanded ? "Collapse sidebar" : "Expand sidebar"}
          >
            {expanded ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
          </button>
        </div>

        {/* Nav items */}
        <nav className="flex-1 flex flex-col py-2 gap-0.5 overflow-y-auto px-2">
          {sections.map((s) => {
            const Icon = s.icon;
            const isActive = activeSection === s.id;
            return (
              <button
                key={s.id}
                onClick={() => scrollToSection(s.id)}
                title={expanded ? undefined : `${s.label} (${s.key})`}
                aria-label={s.label}
                className={cn(
                  "group relative flex items-center gap-3 rounded-lg transition-all duration-200",
                  expanded ? "px-3 py-2.5" : "w-10 h-10 justify-center mx-auto",
                  isActive
                    ? "bg-vaea-teal-300/20"
                    : "hover:bg-white/8"
                )}
              >
                <Icon
                  size={18}
                  className={cn(
                    "shrink-0 transition-colors duration-200",
                    isActive ? "text-vaea-teal-300" : "text-white/40 group-hover:text-white/70"
                  )}
                  aria-hidden="true"
                />
                {expanded && (
                  <span
                    className={cn(
                      "text-sm font-medium whitespace-nowrap transition-colors duration-200",
                      isActive ? "text-vaea-teal-300" : "text-white/60 group-hover:text-white/80"
                    )}
                  >
                    {s.label}
                  </span>
                )}
                {expanded && (
                  <span className="ml-auto font-[family-name:var(--font-jetbrains-mono)] text-[10px] text-white/30">
                    {s.key}
                  </span>
                )}
                {isActive && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 rounded-r bg-vaea-teal-300" />
                )}
                {/* Tooltip — only when collapsed */}
                {!expanded && (
                  <span className="absolute left-full ml-2 px-2 py-1 rounded text-xs font-medium whitespace-nowrap bg-vaea-navy-light text-white opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-150 z-50 shadow-lg border border-white/10">
                    {s.label}
                    <span className="ml-1.5 text-white/40 font-[family-name:var(--font-jetbrains-mono)] text-[10px]">{s.key}</span>
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Bottom status */}
        <div className="flex items-center gap-2 h-10 border-t border-white/10 shrink-0 px-3">
          <div className="w-2 h-2 rounded-full bg-vaea-green-500 animate-pulse shrink-0" />
          {expanded && (
            <span className="text-[10px] text-white/40 whitespace-nowrap">Feature Complete</span>
          )}
        </div>
      </aside>

      {/* ── Mobile Tab Bar (<lg) ── */}
      <div className="lg:hidden sticky top-16 z-30 border-b border-border bg-background/95 backdrop-blur-sm">
        <nav className="flex overflow-x-auto gap-1 px-3 py-2 scrollbar-hide">
          {sections.map((s) => {
            const Icon = s.icon;
            const isActive = activeSection === s.id;
            return (
              <button
                key={s.id}
                onClick={() => scrollToSection(s.id)}
                aria-label={s.label}
                className={cn(
                  "flex items-center gap-1.5 shrink-0 rounded-full px-3 py-1.5 text-xs font-medium transition-colors",
                  isActive
                    ? "bg-vaea-teal-500/10 text-vaea-teal-700"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon size={14} aria-hidden="true" />
                {s.label}
              </button>
            );
          })}
        </nav>
      </div>
    </>
  );
}
