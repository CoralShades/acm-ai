"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { techStack } from "@/lib/sprint-data";
import { fadeUp } from "@/lib/animations";
import { useInView } from "@/hooks/useInView";
import { cn } from "@/lib/cn";

interface ArchBoxProps {
  label: string;
  sub?: string;
  variant?: "teal" | "navy" | "coral";
  width?: string;
}

function ArchBox({ label, sub, variant = "teal", width }: ArchBoxProps) {
  const styles = {
    teal: "bg-vaea-teal-300/10 border-vaea-teal-300/30 text-vaea-teal-300",
    navy: "bg-vaea-navy/10 border-vaea-navy/30 text-vaea-navy",
    coral: "bg-vaea-coral/10 border-vaea-coral/30 text-vaea-coral",
  };

  return (
    <div
      className={cn(
        "px-3 py-2 rounded-lg text-center border",
        styles[variant]
      )}
      style={width ? { minWidth: width } : undefined}
    >
      <div className="text-xs font-bold">{label}</div>
      {sub && <div className="text-xs mt-0.5 text-foreground/50">{sub}</div>}
    </div>
  );
}

const dataModelEntities = [
  "source",
  "acm_record",
  "acm_table_section",
  "site_config",
  "bar_template",
  "field_schema",
  "school",
  "building",
  "room",
];

const chatArchFlow: [string, "teal" | "navy" | "coral" | "green"][] = [
  ["User", "navy"],
  ["CopilotKit (AG-UI)", "teal"],
  ["SSE /api/agui/chat", "coral"],
  ["LangGraph Supervisor", "navy"],
  ["ACM Tools / Search Tools", "teal"],
  ["SurrealDB", "coral"],
  ["Streamed Response", "teal"],
];

export function ArchitectureSection() {
  const { ref, isInView } = useInView({ threshold: 0.05 });

  return (
    <div className="space-y-6" ref={ref}>
      {/* Header */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
      >
        <h2 className="text-xl font-bold text-vaea-navy">Technical Architecture</h2>
        <p className="text-sm mt-1 text-foreground/50">
          FastAPI + SurrealDB + LangGraph + Next.js
        </p>
      </motion.div>

      {/* System Architecture */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="rounded-xl border border-border p-5 space-y-3 bg-card"
      >
        <h3 className="text-sm font-bold text-vaea-navy">System Architecture</h3>
        <div className="flex flex-col items-center gap-2">
          <ArchBox label="Browser Client" sub=":8502" variant="navy" width="200px" />
          <ArrowRight size={14} className="rotate-90 text-vaea-coral" />
          <ArchBox label="Next.js Frontend" sub="/api/* proxy" variant="teal" width="200px" />
          <ArrowRight size={14} className="rotate-90 text-vaea-coral" />
          <ArchBox label="FastAPI Backend" sub="REST + SSE :5055" variant="coral" width="200px" />
          <ArrowRight size={14} className="rotate-90 text-vaea-coral" />
          <div className="flex gap-3 flex-wrap justify-center">
            <ArchBox label="SurrealDB" sub="Doc + Vector + Graph :8000" variant="teal" />
            <ArchBox label="Background Worker" sub="surreal-commands" variant="navy" />
            <ArchBox label="MinerU / Docling" sub="PDF extraction" variant="coral" />
          </div>
        </div>
      </motion.div>

      {/* Chat Architecture */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="rounded-xl border border-border p-5 space-y-3 bg-card"
      >
        <h3 className="text-sm font-bold text-vaea-navy">Chat Architecture</h3>
        <div className="flex items-center gap-1 flex-wrap text-xs">
          {chatArchFlow.map(([label, color], i) => {
            const variantMap: Record<string, string> = {
              teal: "bg-vaea-teal-300/12 text-vaea-teal-300",
              navy: "bg-vaea-navy/12 text-vaea-navy",
              coral: "bg-vaea-coral/12 text-vaea-coral",
              green: "bg-vaea-green-500/12 text-vaea-green-500",
            };
            return (
              <div key={i} className="flex items-center gap-1">
                <span
                  className={cn(
                    "px-2 py-1 rounded font-semibold",
                    variantMap[color] ?? variantMap.teal
                  )}
                >
                  {label}
                </span>
                {i < chatArchFlow.length - 1 && (
                  <ArrowRight size={10} className="text-vaea-coral shrink-0" />
                )}
              </div>
            );
          })}
        </div>
      </motion.div>

      {/* Data Model */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="rounded-xl border border-border p-5 space-y-3 bg-card"
      >
        <h3 className="text-sm font-bold text-vaea-navy">Data Model</h3>
        <div className="flex gap-2 flex-wrap">
          {dataModelEntities.map((entity) => (
            <div
              key={entity}
              className="px-3 py-2 rounded-lg border border-vaea-teal-300/40 text-xs font-[family-name:var(--font-jetbrains-mono)] font-semibold text-vaea-teal-300 bg-vaea-teal-300/5"
            >
              {entity}
            </div>
          ))}
        </div>
        <div className="text-xs text-foreground/50">
          Graph relations: school→building→room→acm_record→source (SurrealDB RELATE)
        </div>
      </motion.div>

      {/* Tech Stack Table */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="rounded-xl border border-border overflow-hidden bg-card"
      >
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-vaea-navy/5">
              <th className="px-3 py-2 text-left font-bold text-vaea-navy">Layer</th>
              <th className="px-3 py-2 text-left font-bold text-vaea-navy">Technology</th>
              <th className="px-3 py-2 text-left font-bold text-vaea-navy">Purpose</th>
            </tr>
          </thead>
          <tbody>
            {techStack.map((row, i) => (
              <tr key={i} className="border-t border-border/50">
                <td className="px-3 py-2 font-semibold text-vaea-teal-300">{row.layer}</td>
                <td className="px-3 py-2 font-[family-name:var(--font-jetbrains-mono)] text-vaea-navy">
                  {row.tech}
                </td>
                <td className="px-3 py-2 text-foreground/60">{row.purpose}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </motion.div>
    </div>
  );
}
