"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, ChevronDown, ChevronUp } from "lucide-react";
import { PROJECT_TRUTH } from "@/lib/project-truth";
import { cn } from "@/lib/cn";

const { extraction } = PROJECT_TRUTH;

export function ExtractionAccuracyWidget({ className }: { className?: string }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={cn(
        "rounded-2xl border border-amber-500/30 bg-amber-500/5 p-6 space-y-4",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10">
            <AlertTriangle size={20} className="text-amber-500" aria-hidden="true" />
          </div>
          <div>
            <p className="font-semibold text-foreground">Extraction Accuracy</p>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-semibold text-amber-600 border border-amber-500/20">
              Active Work
            </span>
          </div>
        </div>
        <span className="font-[family-name:var(--font-dm-serif)] text-3xl text-amber-600 leading-none">
          {extraction.currentAccuracy}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="space-y-2">
        <div className="h-3 w-full overflow-hidden rounded-full bg-amber-500/10">
          <motion.div
            className="h-full rounded-full bg-amber-500"
            initial={{ width: 0 }}
            animate={{ width: `${extraction.currentAccuracy}%` }}
            transition={{ duration: 1.2, ease: "easeOut" }}
          />
        </div>
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            {extraction.testRecordsPassing}/{extraction.testRecordsTotal} test records
            passing
          </span>
          <span>Target: {extraction.targetAccuracy}%</span>
        </div>
      </div>

      {/* Collapsible known issues */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center gap-2 text-xs font-medium text-amber-600 hover:text-amber-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2 rounded"
        aria-expanded={expanded}
        aria-label={expanded ? "Hide known issues" : "Show known issues"}
      >
        {expanded ? (
          <ChevronUp size={14} aria-hidden="true" />
        ) : (
          <ChevronDown size={14} aria-hidden="true" />
        )}
        {extraction.activeIssueCount} known missing records
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.ul
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="space-y-1.5 overflow-hidden"
          >
            {extraction.knownIssues.map((issue, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-xs text-muted-foreground"
              >
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                {issue}
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}
