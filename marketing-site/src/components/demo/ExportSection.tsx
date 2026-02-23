"use client";

import { motion } from "framer-motion";
import { FileText, Table, CheckCircle } from "lucide-react";
import { barColumns } from "@/lib/sprint-data";
import { fadeUp, staggerContainer } from "@/lib/animations";
import { useInView } from "@/hooks/useInView";

const csvFeatures = [
  "All 47 BAR columns included",
  "Column order matches BAR specification",
  "UTF-8 encoded",
  "Filter by building before export",
  "Named: [SiteName]_ACM_[Date].csv",
];

const excelFeatures = [
  "Exact BAR column headers from VAEA template",
  "Column order matches official BAR spec (47 columns)",
  "Risk status cells colour-coded",
  "Header row frozen, columns auto-sized",
  "Data validation dropdowns for enum fields",
  "Optional reference sheets (Building Types, Product Types)",
  "Template versioning — upload new template without code changes",
];

export function ExportSection() {
  const { ref, isInView } = useInView({ threshold: 0.1 });

  return (
    <div className="space-y-6" ref={ref}>
      {/* Header */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
      >
        <h2 className="text-xl font-bold text-vaea-navy">BAR-Compliant Export</h2>
        <p className="text-sm mt-1 text-foreground/50">
          Victorian Government submission-ready in one click
        </p>
      </motion.div>

      {/* Export cards */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="grid grid-cols-1 sm:grid-cols-2 gap-5"
      >
        {/* CSV Card */}
        <motion.div
          variants={fadeUp}
          className="rounded-xl p-6 border-2 border-vaea-teal-300/40 space-y-3 bg-card"
        >
          <div className="flex items-center gap-3">
            <FileText size={24} className="text-vaea-teal-300" />
            <h3 className="font-bold text-vaea-navy">CSV Export</h3>
          </div>
          <div className="space-y-1.5 text-sm text-foreground/60">
            {csvFeatures.map((f) => (
              <div key={f} className="flex items-center gap-2">
                <CheckCircle size={12} className="text-vaea-teal-300 shrink-0" />
                {f}
              </div>
            ))}
          </div>
          <motion.button
            whileHover={{ scale: 1.02, boxShadow: "0 4px 16px rgba(83,166,157,0.25)" }}
            whileTap={{ scale: 0.98 }}
            className="w-full py-2.5 rounded-lg text-white font-semibold text-sm bg-vaea-teal-300 hover:bg-vaea-teal-500 transition-colors"
          >
            Download CSV
          </motion.button>
        </motion.div>

        {/* BAR Excel Card */}
        <motion.div
          variants={fadeUp}
          className="rounded-xl p-6 border-2 border-vaea-coral/40 space-y-3 bg-card"
        >
          <div className="flex items-center gap-3">
            <Table size={24} className="text-vaea-coral" />
            <h3 className="font-bold text-vaea-navy">BAR Excel (.xlsx)</h3>
          </div>
          <div className="space-y-1.5 text-sm text-foreground/60">
            {excelFeatures.map((f) => (
              <div key={f} className="flex items-center gap-2">
                <CheckCircle size={12} className="text-vaea-coral shrink-0" />
                {f}
              </div>
            ))}
          </div>
          <motion.button
            whileHover={{ scale: 1.02, boxShadow: "0 4px 16px rgba(235,120,122,0.25)" }}
            whileTap={{ scale: 0.98 }}
            className="w-full py-2.5 rounded-lg text-white font-semibold text-sm bg-vaea-coral hover:bg-vaea-coral/90 transition-colors"
          >
            Export BAR Excel
          </motion.button>
        </motion.div>
      </motion.div>

      {/* BAR Columns Grid */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
      >
        <h3 className="text-sm font-bold mb-2 text-vaea-navy">The {barColumns.length} BAR Columns</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 text-xs max-h-52 overflow-y-auto rounded-xl p-4 border border-border bg-muted/20 text-foreground/60">
          {barColumns.map((col, i) => (
            <div key={i} className="py-0.5">
              <span className="font-[family-name:var(--font-jetbrains-mono)] mr-1.5 text-vaea-teal-300">
                {i + 1}.
              </span>
              {col}
            </div>
          ))}
        </div>
      </motion.div>

      {/* Site Config Callout */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="rounded-xl p-4 border-l-4 border-vaea-coral bg-vaea-coral/5"
      >
        <p className="text-sm text-vaea-navy">
          <strong>Site Configuration:</strong> Non-extractable fields (Department, Agency, Building
          Type, etc.) are configured via the Site Config form before export — ensuring 100% BAR
          field coverage.
        </p>
      </motion.div>
    </div>
  );
}
