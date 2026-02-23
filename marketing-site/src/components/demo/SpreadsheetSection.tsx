"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, FileText, Eye } from "lucide-react";
import { gridRows } from "@/lib/sprint-data";
import { fadeUp, staggerFast } from "@/lib/animations";
import { useInView } from "@/hooks/useInView";
import { cn } from "@/lib/cn";

const presetViews = [
  "Essential View",
  "Full BAR View",
  "Assessment Focus",
  "Removal Tracking",
];

function riskBorderClass(risk: string) {
  if (risk === "High") return "border-l-4 border-l-red-500 bg-red-50";
  if (risk === "Medium") return "border-l-4 border-l-orange-400 bg-orange-50/50";
  return "border-l-4 border-l-green-500 bg-green-50/30";
}

function RiskBadge({ risk }: { risk: string }) {
  const colorMap: Record<string, string> = {
    High: "text-red-600 bg-red-100",
    Medium: "text-orange-500 bg-orange-100",
    Low: "text-green-600 bg-green-100",
  };
  return (
    <span className={cn("px-2 py-0.5 rounded text-xs font-bold", colorMap[risk] ?? "")}>
      {risk}
    </span>
  );
}

const colHeaders = [
  "Dept",
  "Agency",
  "Site",
  "Bldg Type",
  "Code",
  "Type",
  "Level",
  "Room",
  "I/E",
  "Product",
  "Friable?",
  "Condition",
  "Risk",
  "Result",
  "Rec.",
];

export function SpreadsheetSection() {
  const [clicked, setClicked] = useState<number | null>(null);
  const [preset, setPreset] = useState("Essential View");
  const { ref, isInView } = useInView({ threshold: 0.05 });

  return (
    <div className="space-y-4" ref={ref}>
      {/* Header */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
      >
        <h2 className="text-xl font-bold text-vaea-navy">AG Grid — Victorian BAR Spreadsheet</h2>
        <p className="text-sm mt-1 text-foreground/50">
          47-column interactive register with risk colour-coding
        </p>
      </motion.div>

      {/* Toolbar */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="flex items-center gap-2 p-2 rounded-lg border border-border bg-muted/40"
      >
        <div className="flex items-center gap-1 px-3 py-1.5 rounded border border-border bg-card text-xs flex-1">
          <Search size={12} className="text-foreground/30" />
          <span className="text-foreground/30">Search records...</span>
        </div>
        <div className="px-3 py-1.5 rounded border border-border bg-card text-xs text-foreground/70">
          Filter: All Buildings ▼
        </div>
        <div className="px-3 py-1.5 rounded border border-border bg-card text-xs text-foreground/70">
          Columns ▼
        </div>
        <button className="px-3 py-1.5 rounded text-xs text-white font-semibold bg-vaea-teal-300 hover:bg-vaea-teal-500 transition-colors">
          Export CSV
        </button>
        <button className="px-3 py-1.5 rounded text-xs text-white font-semibold bg-vaea-coral hover:bg-vaea-coral/90 transition-colors">
          Export BAR Excel
        </button>
      </motion.div>

      {/* Grid + Citation Panel */}
      <div className="relative flex gap-3">
        <motion.div
          variants={fadeUp}
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          className={cn(
            "overflow-x-auto rounded-xl border border-border transition-all duration-300",
            clicked !== null ? "flex-1" : "w-full"
          )}
        >
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-vaea-navy/5">
                <th
                  colSpan={3}
                  className="px-2 py-1.5 text-left font-bold border-b border-r border-border text-vaea-teal-300"
                >
                  Organisation
                </th>
                <th
                  colSpan={3}
                  className="px-2 py-1.5 text-left font-bold border-b border-r border-border text-vaea-teal-300"
                >
                  Building
                </th>
                <th
                  colSpan={3}
                  className="px-2 py-1.5 text-left font-bold border-b border-r border-border text-vaea-teal-300"
                >
                  Location
                </th>
                <th
                  colSpan={3}
                  className="px-2 py-1.5 text-left font-bold border-b border-r border-border text-vaea-teal-300"
                >
                  ACM Item
                </th>
                <th
                  colSpan={3}
                  className="px-2 py-1.5 text-left font-bold border-b border-border text-vaea-coral"
                >
                  Assessment
                </th>
              </tr>
              <tr className="bg-muted/30">
                {colHeaders.map((h, i) => (
                  <th
                    key={i}
                    className="px-2 py-1.5 text-left font-semibold border-b border-border whitespace-nowrap text-foreground/50"
                    style={{ fontSize: "10px" }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <motion.tbody
              variants={staggerFast}
              initial="hidden"
              animate={isInView ? "visible" : "hidden"}
            >
              {gridRows.map((row, i) => (
                <motion.tr
                  key={i}
                  variants={fadeUp}
                  onClick={() => setClicked(i === clicked ? null : i)}
                  className={cn(
                    "cursor-pointer transition-colors hover:brightness-95",
                    clicked === i ? "ring-1 ring-inset ring-vaea-teal-300/50" : "",
                    riskBorderClass(row.risk)
                  )}
                >
                  {[
                    row.dept,
                    row.agency,
                    row.site,
                    row.btype,
                    row.bcode,
                    row.btype,
                    row.level,
                    row.room,
                    row.io,
                    row.product,
                    row.friable,
                    row.cond,
                  ].map((v, j) => (
                    <td
                      key={j}
                      className="px-2 py-2 border-b border-border/50 whitespace-nowrap text-foreground"
                      style={{
                        fontWeight: row.risk === "High" && j >= 9 ? 600 : 400,
                      }}
                    >
                      {v}
                    </td>
                  ))}
                  <td className="px-2 py-2 border-b border-border/50">
                    <RiskBadge risk={row.risk} />
                  </td>
                  <td className="px-2 py-2 border-b border-border/50 whitespace-nowrap text-foreground">
                    {row.result}
                  </td>
                  <td className="px-2 py-2 border-b border-border/50 whitespace-nowrap text-foreground">
                    {row.rec}
                  </td>
                </motion.tr>
              ))}
            </motion.tbody>
          </table>
        </motion.div>

        {/* Citation Panel */}
        <AnimatePresence>
          {clicked !== null && (
            <motion.div
              key="citation"
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 40 }}
              transition={{ duration: 0.25, ease: [0.25, 0.1, 0.25, 1] }}
              className="w-72 shrink-0 rounded-xl border border-border p-4 space-y-3 shadow-lg bg-card"
            >
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-sm text-vaea-navy">Citation</h4>
                <button
                  onClick={() => setClicked(null)}
                  className="text-foreground/40 text-xs hover:text-foreground transition-colors"
                >
                  ✕
                </button>
              </div>
              <div className="space-y-2 text-xs text-foreground/70">
                <div className="flex items-center gap-2">
                  <FileText size={13} className="text-vaea-teal-300" />
                  <span className="font-semibold">Source:</span>
                  {gridRows[clicked].site}_ACM_Register.pdf
                </div>
                <div className="flex items-center gap-2">
                  <Eye size={13} className="text-vaea-teal-300" />
                  <span className="font-semibold">Location:</span>
                  Page {gridRows[clicked].page}, Table {gridRows[clicked].table}, Row{" "}
                  {gridRows[clicked].row}
                </div>
                <div className="font-[family-name:var(--font-jetbrains-mono)] text-xs px-2 py-1 rounded bg-vaea-teal-300/8 text-vaea-teal-300 break-all">
                  acm:acm_record:risk_status
                </div>
                {/* PDF Preview mockup */}
                <div className="rounded-lg h-24 flex items-center justify-center border border-border bg-muted/30">
                  <div className="w-16 h-20 rounded border-2 border-border relative bg-card">
                    <div className="absolute w-10 h-2 rounded top-3 left-1 bg-amber-200 border border-amber-400" />
                    <div className="text-center text-foreground/20 mt-8" style={{ fontSize: "6px" }}>
                      PDF Preview
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Preset Views */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="flex items-center gap-2 flex-wrap"
      >
        {presetViews.map((p) => (
          <button
            key={p}
            onClick={() => setPreset(p)}
            className={cn(
              "px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border",
              preset === p
                ? "bg-vaea-teal-300 text-white border-vaea-teal-300"
                : "bg-card text-vaea-navy border-border hover:border-vaea-teal-300/50"
            )}
          >
            {p}
          </button>
        ))}
      </motion.div>
    </div>
  );
}
