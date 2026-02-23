"use client";

import { motion } from "framer-motion";
import { Table, AlertTriangle, ArrowRight } from "lucide-react";
import { useTypewriter } from "@/hooks/useTypewriter";
import { fadeUp } from "@/lib/animations";
import { useInView } from "@/hooks/useInView";
import { cn } from "@/lib/cn";

const highRiskItems = [
  {
    item: "Pipe Lagging",
    room: "Plant Room (Roof)",
    cond: "Poor | Friable | Positive",
    ref: "a1b2",
    rec: "Remove Immediately",
  },
  {
    item: "Ceiling Tiles",
    room: "Ward 4B",
    cond: "Damaged | Non-friable | Suspected",
    ref: "c3d4",
    rec: "Priority Assessment",
  },
  {
    item: "Boiler Insulation",
    room: "Basement Mechanical",
    cond: "Deteriorating | Friable | Positive",
    ref: "e5f6",
    rec: "Remove Immediately",
  },
];

const typewriterText =
  "Friable ACM can be crumbled by hand pressure, releasing fibres into the air. This makes it significantly more hazardous than non-friable ACM, which has fibres bound in a matrix. Under the Victorian BAR taxonomy: Friable uses codes T1–T6 (e.g. T3 = Friable Insulation), Non-friable uses T1–T8 (e.g. T1 = Cement, T3 = Vinyl). Friable items require specialist licensed removal contractors.";

const howItWorks = [
  "User Message",
  "Supervisor Agent (LangGraph ReAct)",
  "ACM Tools (if toggle ON)",
  "SurrealDB query",
  "Citation generation",
  "SSE streamed response",
];

const toolBadges = [
  "query_by_building",
  "query_by_risk",
  "building_search",
  "compliance_check",
];

export function ChatSection() {
  const { ref, isInView } = useInView({ threshold: 0.1 });

  const { displayed, isComplete } = useTypewriter({
    text: typewriterText,
    speed: 18,
    delay: 800,
    enabled: isInView,
  });

  return (
    <div className="space-y-4" ref={ref}>
      {/* Header */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
      >
        <h2 className="text-xl font-bold text-vaea-navy">Smart Chat — AI-Powered ACM Queries</h2>
        <p className="text-sm mt-1 text-foreground/50">
          Natural language queries against structured register data
        </p>
      </motion.div>

      {/* Chat Window */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="rounded-xl border border-border overflow-hidden bg-card"
      >
        {/* Chat header bar */}
        <div className="px-4 py-2.5 flex items-center justify-between border-b border-border bg-vaea-navy/4">
          <span className="text-sm font-semibold text-vaea-navy">Smart Chat</span>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-vaea-teal-300/15 text-vaea-teal-300">
            <Table size={11} /> ACM Data ON
          </span>
        </div>

        <div className="p-4 space-y-4 max-h-[420px] overflow-y-auto bg-muted/20">
          {/* Message 1: user */}
          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate={isInView ? "visible" : "hidden"}
            className="flex justify-end"
          >
            <div className="px-4 py-2.5 rounded-2xl rounded-tr-md text-sm max-w-md bg-vaea-teal-300 text-white">
              Show me all high-risk asbestos items in Building B003
            </div>
          </motion.div>

          {/* Message 2: AI structured */}
          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate={isInView ? "visible" : "hidden"}
            className="flex justify-start"
          >
            <div className="px-4 py-3 rounded-2xl rounded-tl-md text-sm max-w-lg border border-border bg-card text-vaea-navy">
              <p className="font-semibold mb-2">
                I found 3 high-risk ACM items in Building B003 (Royal Melbourne Hospital):
              </p>
              {highRiskItems.map((it, i) => (
                <div
                  key={i}
                  className="mb-2 pl-3 border-l-2 border-red-500"
                >
                  <p className="font-semibold text-xs">
                    {i + 1}. {it.item} — {it.room}
                  </p>
                  <p className="text-xs mt-0.5 text-foreground/60">{it.cond}</p>
                  <p className="text-xs font-[family-name:var(--font-jetbrains-mono)] mt-0.5 text-vaea-teal-300">
                    [acm:acm_record:{it.ref}:risk_status] →{" "}
                    <span className="text-red-600 font-bold">HIGH RISK</span>
                  </p>
                </div>
              ))}
              <div className="flex items-center gap-1 mt-2 px-2 py-1 rounded text-xs font-semibold bg-red-50 text-red-600">
                <AlertTriangle size={12} /> Immediate attention required. All 3 items exceed
                acceptable risk threshold.
              </div>
            </div>
          </motion.div>

          {/* Message 3: user */}
          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate={isInView ? "visible" : "hidden"}
            className="flex justify-end"
          >
            <div className="px-4 py-2.5 rounded-2xl rounded-tr-md text-sm max-w-md bg-vaea-teal-300 text-white">
              What does &ldquo;friable&rdquo; mean and why is it more dangerous?
            </div>
          </motion.div>

          {/* Message 4: AI typewriter */}
          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate={isInView ? "visible" : "hidden"}
            className="flex justify-start"
          >
            <div className="px-4 py-3 rounded-2xl rounded-tl-md text-sm max-w-lg border border-border bg-card text-vaea-navy leading-relaxed">
              {isInView ? (
                <>
                  {displayed}
                  {!isComplete && (
                    <span className="inline-block w-2 h-4 ml-1 bg-vaea-teal-300 typing-cursor align-middle" />
                  )}
                </>
              ) : (
                <span className="text-foreground/30">...</span>
              )}
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* How It Works */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="rounded-xl p-4 border border-border bg-card"
      >
        <h4 className="text-xs font-bold mb-2 text-vaea-navy uppercase tracking-wide">
          How It Works
        </h4>
        <div className="flex items-center gap-1 text-xs flex-wrap">
          {howItWorks.map((step, i) => (
            <div key={i} className="flex items-center gap-1">
              <span
                className={cn(
                  "px-2 py-1 rounded font-medium text-vaea-navy",
                  i === 1 ? "bg-vaea-coral/12" : "bg-vaea-teal-300/8"
                )}
              >
                {step}
              </span>
              {i < howItWorks.length - 1 && (
                <ArrowRight size={10} className="text-vaea-coral shrink-0" />
              )}
            </div>
          ))}
        </div>
        <div className="flex gap-2 mt-3 flex-wrap">
          {toolBadges.map((badge) => (
            <span
              key={badge}
              className="px-2.5 py-1 rounded-full text-xs font-semibold bg-vaea-teal-300/10 text-vaea-teal-300 font-[family-name:var(--font-jetbrains-mono)]"
            >
              {badge}
            </span>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
