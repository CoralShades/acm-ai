"use client";

import { motion } from "framer-motion";
import { Upload, Zap, Download } from "lucide-react";
import { useInView } from "@/hooks/useInView";
import { staggerContainer, fadeUp } from "@/lib/animations";
import { cn } from "@/lib/cn";

const steps = [
  {
    icon: Upload,
    title: "Upload PDF",
    description:
      "Drag and drop your existing asbestos register PDF — any format, any structure. The system handles digital and scanned documents alike via automatic PDF classification.",
    step: "01",
    color: "bg-vaea-teal-500",
  },
  {
    icon: Zap,
    title: "AI Extracts Data",
    description:
      "A 7-stage agentic pipeline powered by LangGraph, MinerU and Docling parses every table — including merged cells and multi-page registers — mapping 47 BAR fields with 96% accuracy.",
    step: "02",
    color: "bg-vaea-teal-300",
  },
  {
    icon: Download,
    title: "Export BAR Excel",
    description:
      "Download a government-ready BAR-compliant Excel workbook via openpyxl. Every row is traceable back to its source PDF page. Submit directly — no reformatting required.",
    step: "03",
    color: "bg-vaea-coral",
  },
];

export function HowItWorks() {
  const { ref, isInView } = useInView({ threshold: 0.15 });

  return (
    <section id="how-it-works" className="bg-background py-24">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        {/* Section header */}
        <div className="mx-auto mb-16 max-w-2xl text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-vaea-teal-500">
            How It Works
          </p>
          <h2 className="font-[family-name:var(--font-dm-serif)] text-3xl text-foreground sm:text-4xl">
            From PDF to Compliance in Three Steps
          </h2>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground">
            ACM-AI eliminates weeks of manual data entry. Upload your asbestos
            register and receive a submission-ready BAR workbook in under 30
            seconds.
          </p>
        </div>

        {/* Cards */}
        <motion.div
          ref={ref}
          variants={staggerContainer}
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          className="grid gap-8 md:grid-cols-3"
        >
          {steps.map((step) => {
            const Icon = step.icon;
            return (
              <motion.div
                key={step.step}
                variants={fadeUp}
                className={cn(
                  "relative rounded-2xl border border-border bg-card p-8",
                  "shadow-[var(--shadow-md)] transition-shadow duration-300",
                  "hover:shadow-[var(--shadow-lg)]"
                )}
              >
                {/* Step number */}
                <span
                  className={cn(
                    "absolute right-6 top-6",
                    "font-[family-name:var(--font-jetbrains-mono)]",
                    "text-xs font-bold tracking-widest text-muted-foreground/40"
                  )}
                >
                  {step.step}
                </span>

                {/* Icon circle */}
                <div
                  className={cn(
                    "mb-6 flex h-14 w-14 items-center justify-center rounded-full",
                    step.color
                  )}
                >
                  <Icon className="h-6 w-6 text-white" strokeWidth={2} />
                </div>

                {/* Title */}
                <h3 className="mb-3 font-[family-name:var(--font-dm-serif)] text-xl text-foreground">
                  {step.title}
                </h3>

                {/* Description */}
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {step.description}
                </p>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Connector line (desktop only) */}
        <div className="mt-4 hidden items-center justify-center md:flex">
          <p className="text-xs text-muted-foreground/60">
            Average end-to-end processing time:{" "}
            <span className="font-semibold text-vaea-teal-500">18 seconds</span>
          </p>
        </div>
      </div>
    </section>
  );
}
