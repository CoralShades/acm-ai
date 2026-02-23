"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Play,
  Loader,
  CheckCircle,
  ArrowRight,
  Search,
  FileText,
  Zap,
  Database,
  BarChart3,
  Shield,
} from "lucide-react";
import { pipelineStages, logLines } from "@/lib/sprint-data";
import { fadeUp, staggerContainer } from "@/lib/animations";
import { useInView } from "@/hooks/useInView";
import { cn } from "@/lib/cn";

// Icon mapping for pipeline stages (ordered to match pipelineStages array)
const stageIcons = [Search, FileText, Zap, Database, BarChart3, Shield, CheckCircle];

const stageColors = [
  "#1e2235", // PRE-ANALYSIS: navy
  "#53A69D", // PREFLIGHT: teal
  "#EB787A", // ORCHESTRATION: coral
  "#53A69D", // EXTRACT: teal
  "#1e2235", // INTERPRET: navy
  "#EB787A", // VALIDATE: coral
  "#22c55e", // SAVE & INDEX: success
];

const dataFlow = [
  "PDF Upload",
  "MinerU / Docling",
  "ACM Parser",
  "SurrealDB",
  "AG Grid",
  "BAR Export",
];

export function PipelineSection() {
  const [running, setRunning] = useState(false);
  const [activeStage, setActiveStage] = useState(-2);
  const [logs, setLogs] = useState<string[]>([]);

  const { ref, isInView } = useInView({ threshold: 0.1 });

  function run() {
    setRunning(true);
    setActiveStage(-1);
    setLogs([]);

    pipelineStages.forEach((_, i) => {
      setTimeout(() => setActiveStage(i), i * 900);
      setTimeout(
        () =>
          setLogs((prev) => [
            ...prev,
            logLines[i] ?? logLines[logLines.length - 2],
          ]),
        i * 900 + 400
      );
    });

    setTimeout(() => {
      setLogs((prev) => [...prev, logLines[logLines.length - 1]]);
      setRunning(false);
    }, pipelineStages.length * 900 + 500);
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        ref={ref}
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="flex items-center justify-between"
      >
        <div>
          <h2 className="text-xl font-bold text-vaea-navy">7-Stage Extraction Pipeline</h2>
          <p className="text-sm mt-1 text-foreground/50">From raw PDF to structured compliance data</p>
        </div>
        <button
          onClick={run}
          disabled={running}
          className={cn(
            "flex items-center gap-2 px-5 py-2.5 rounded-lg text-white text-sm font-semibold transition-all duration-200",
            running
              ? "bg-vaea-navy/40 cursor-not-allowed"
              : "bg-vaea-coral hover:bg-vaea-coral/90 hover:shadow-md active:scale-95"
          )}
        >
          {running ? (
            <Loader size={16} className="animate-spin" />
          ) : (
            <Play size={16} />
          )}
          {running ? "Processing..." : "Run Demo"}
        </button>
      </motion.div>

      {/* Pipeline Stages */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="space-y-2"
      >
        {pipelineStages.map((stage, i) => {
          const Icon = stageIcons[i] ?? CheckCircle;
          const color = stageColors[i] ?? "#53A69D";
          const isActive = i <= activeStage;
          const isCurrent = i === activeStage && running;

          return (
            <motion.div
              key={stage.id}
              variants={fadeUp}
              className={cn(
                "flex items-start gap-3 p-3.5 rounded-xl border transition-all duration-500",
                isActive ? "border-opacity-40" : "border-border",
                isCurrent ? "shadow-sm" : ""
              )}
              style={{
                borderColor: isActive ? `${color}44` : undefined,
                backgroundColor: isCurrent
                  ? `${color}08`
                  : isActive
                  ? `${color}04`
                  : undefined,
              }}
            >
              <div
                className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0 transition-all duration-500"
                style={{ background: isActive ? color : "#e5e7eb" }}
              >
                <Icon
                  size={16}
                  style={{ color: isActive ? "white" : "#999" }}
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-[family-name:var(--font-jetbrains-mono)] px-1.5 py-0.5 rounded bg-vaea-navy/5 text-foreground/50">
                    Stage {stage.id}
                  </span>
                  <span className="font-semibold text-sm text-vaea-navy">{stage.name}</span>
                  {isCurrent && (
                    <span
                      className="w-2 h-2 rounded-full animate-pulse"
                      style={{ background: color }}
                    />
                  )}
                  {isActive && !isCurrent && (
                    <CheckCircle size={14} className="text-vaea-green-500" />
                  )}
                </div>
                <p className="text-xs mt-1 leading-relaxed text-foreground/50">{stage.desc}</p>
                <p
                  className="text-xs mt-1 font-[family-name:var(--font-jetbrains-mono)]"
                  style={{ color: `${color}aa` }}
                >
                  {stage.tools}
                </p>
              </div>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Data Flow */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
      >
        <h3 className="text-sm font-bold mb-3 text-vaea-navy">Data Flow</h3>
        <div className="flex items-center gap-1 overflow-x-auto pb-2">
          {dataFlow.map((step, i) => (
            <div key={i} className="flex items-center gap-1 shrink-0">
              <div
                className="px-3 py-2 rounded-lg text-xs font-semibold text-white whitespace-nowrap"
                style={{
                  background: i % 2 === 0 ? "#53A69D" : "#1e2235",
                }}
              >
                {step}
              </div>
              {i < dataFlow.length - 1 && (
                <ArrowRight size={14} className="text-vaea-coral" />
              )}
            </div>
          ))}
        </div>
      </motion.div>

      {/* Terminal Log */}
      {(logs.length > 0 || running) && (
        <motion.div
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="rounded-xl p-4 font-[family-name:var(--font-jetbrains-mono)] text-xs leading-relaxed overflow-auto max-h-48 terminal-scanline"
          style={{ background: "#0f1419", color: "#4ade80" }}
        >
          {logs.map((line, i) => (
            <div
              key={i}
              className="py-0.5"
              style={{
                color: line.startsWith("✅")
                  ? "#4ade80"
                  : line.includes("Validation")
                  ? "#f59e0b"
                  : "#8b949e",
              }}
            >
              {line}
            </div>
          ))}
          {running && (
            <span className="typing-cursor inline-block">&#9646;</span>
          )}
        </motion.div>
      )}
    </div>
  );
}
