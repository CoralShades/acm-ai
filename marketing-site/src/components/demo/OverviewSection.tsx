"use client";

import { motion } from "framer-motion";
import {
  Upload,
  Table,
  Download,
  CheckCircle,
  Shield,
  Award,
  Database,
  TrendingUp,
} from "lucide-react";
import { projectStats } from "@/lib/sprint-data";
import { fadeUp, staggerContainer } from "@/lib/animations";
import { useInView } from "@/hooks/useInView";
import { cn } from "@/lib/cn";

const statCards = [
  {
    icon: CheckCircle,
    label: "Stories Delivered",
    value: `${projectStats.storiesDelivered}`,
    colorClass: "text-vaea-teal-300",
    bgClass: "bg-vaea-teal-300/10",
  },
  {
    icon: Award,
    label: "Epics Complete",
    value: `${projectStats.epicsComplete}`,
    colorClass: "text-vaea-coral",
    bgClass: "bg-vaea-coral/10",
  },
  {
    icon: Database,
    label: "Commits",
    value: `${projectStats.commits}`,
    colorClass: "text-vaea-navy",
    bgClass: "bg-vaea-navy/10",
  },
  {
    icon: TrendingUp,
    label: "Completion Rate",
    value: `${projectStats.completionRate}%`,
    colorClass: "text-vaea-green-500",
    bgClass: "bg-vaea-green-500/10",
  },
];

const whatCards = [
  {
    icon: Upload,
    title: "Upload PDF",
    desc: "AI extracts asbestos data from any register format — Prensa, Greencap, or custom.",
  },
  {
    icon: Table,
    title: "Interactive Spreadsheet",
    desc: "View all 47 BAR columns in AG Grid with risk colour-coding, sorting, and filtering.",
  },
  {
    icon: Download,
    title: "Export BAR Excel",
    desc: "One-click BAR-compliant Excel export — ready for Victorian Government submission.",
  },
];

const complianceFacts = [
  "Targets Victorian Government BAR (Building Asbestos Register) format",
  "47-column schema matching the official VAEA template",
  "Department → Agency → Site → Building → Room → ACM Item hierarchy",
  "Supports Friable and Non-friable ACM taxonomy (T1–T8)",
  "Config-driven field schema — no code changes for new BAR fields",
  "Every data point traced back to source PDF page and cell",
];

export function OverviewSection() {
  const { ref: heroRef, isInView: heroInView } = useInView({ threshold: 0.1 });
  const { ref: statsRef, isInView: statsInView } = useInView({ threshold: 0.1 });
  const { ref: whatRef, isInView: whatInView } = useInView({ threshold: 0.1 });
  const { ref: factsRef, isInView: factsInView } = useInView({ threshold: 0.1 });

  return (
    <div className="space-y-8">
      {/* Hero Banner */}
      <motion.div
        ref={heroRef}
        variants={fadeUp}
        initial="hidden"
        animate={heroInView ? "visible" : "hidden"}
        className="text-center py-12 rounded-2xl relative overflow-hidden bg-gradient-to-br from-vaea-navy to-vaea-teal-700"
      >
        {/* Dot grid overlay */}
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: "radial-gradient(circle at 20% 50%, white 1px, transparent 1px)",
            backgroundSize: "30px 30px",
          }}
        />
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold mb-4 bg-white/15 text-white">
            <Shield size={14} /> VICTORIAN GOVERNMENT COMPLIANCE
          </div>
          <h1 className="text-4xl font-bold text-white mb-3 tracking-tight font-[family-name:var(--font-dm-serif)]">
            ACM-AI
          </h1>
          <p className="text-lg text-white/80 max-w-2xl mx-auto leading-relaxed">
            Asbestos Compliance Intelligence — Transforming PDF Asbestos Registers into Victorian
            Government BAR-compliant data with AI
          </p>
        </div>
      </motion.div>

      {/* Stat Cards */}
      <motion.div
        ref={statsRef}
        variants={staggerContainer}
        initial="hidden"
        animate={statsInView ? "visible" : "hidden"}
        className="grid grid-cols-2 sm:grid-cols-4 gap-4"
      >
        {statCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={i}
              variants={fadeUp}
              className="rounded-xl p-5 shadow-sm border border-border bg-card"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", card.bgClass)}>
                  <Icon size={20} className={card.colorClass} />
                </div>
                <span className="text-sm font-medium text-foreground/60">{card.label}</span>
              </div>
              <div className="text-3xl font-bold tracking-tight text-foreground">{card.value}</div>
            </motion.div>
          );
        })}
      </motion.div>

      {/* What ACM-AI Does */}
      <motion.div
        ref={whatRef}
        variants={fadeUp}
        initial="hidden"
        animate={whatInView ? "visible" : "hidden"}
      >
        <h2 className="text-xl font-bold mb-4 text-vaea-navy">What ACM-AI Does</h2>
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate={whatInView ? "visible" : "hidden"}
          className="grid grid-cols-1 sm:grid-cols-3 gap-5"
        >
          {whatCards.map((card, i) => {
            const Icon = card.icon;
            return (
              <motion.div
                key={i}
                variants={fadeUp}
                className="rounded-xl p-6 border border-border shadow-sm bg-card"
              >
                <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 bg-vaea-teal-300/10">
                  <Icon size={24} className="text-vaea-teal-300" />
                </div>
                <h3 className="font-bold mb-2 text-vaea-navy">{card.title}</h3>
                <p className="text-sm leading-relaxed text-foreground/60">{card.desc}</p>
              </motion.div>
            );
          })}
        </motion.div>
      </motion.div>

      {/* Key Compliance Facts */}
      <motion.div
        ref={factsRef}
        variants={fadeUp}
        initial="hidden"
        animate={factsInView ? "visible" : "hidden"}
        className="rounded-xl p-6 border-l-4 border-vaea-teal-300 bg-vaea-teal-300/5"
      >
        <h3 className="font-bold mb-3 text-vaea-teal-300">Key Compliance Facts</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm text-foreground/70">
          {complianceFacts.map((fact, i) => (
            <div key={i} className="flex items-start gap-2">
              <CheckCircle size={14} className="mt-0.5 shrink-0 text-vaea-teal-300" />
              {fact}
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
