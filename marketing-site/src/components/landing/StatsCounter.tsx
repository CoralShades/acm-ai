"use client";

import { motion } from "framer-motion";
import { useInView } from "@/hooks/useInView";
import { AnimatedCounter } from "@/components/AnimatedCounter";
import { staggerContainer, fadeUp } from "@/lib/animations";
import { cn } from "@/lib/cn";

const stats = [
  {
    end: 112,
    suffix: "",
    label: "Stories Delivered",
    sublabel: "Across 12 active sprints",
  },
  {
    end: 16,
    suffix: "",
    label: "Epics Complete",
    sublabel: "Full feature coverage",
  },
  {
    end: 281,
    suffix: "",
    label: "Commits",
    sublabel: "Autonomous development velocity",
  },
  {
    end: 47,
    suffix: "",
    label: "BAR Columns",
    sublabel: "Full Victorian Government schema",
  },
  {
    end: 96,
    suffix: "%",
    label: "Extraction Accuracy",
    sublabel: "Against manual ground truth",
  },
  {
    end: 18,
    suffix: "s",
    label: "Processing Time",
    sublabel: "End-to-end per document",
  },
];

export function StatsCounter() {
  const { ref, isInView } = useInView({ threshold: 0.1 });

  return (
    <section className="bg-background py-24">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        {/* Section header */}
        <div className="mx-auto mb-16 max-w-2xl text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-vaea-teal-500">
            By the Numbers
          </p>
          <h2 className="font-[family-name:var(--font-dm-serif)] text-3xl text-foreground sm:text-4xl">
            Built for Enterprise Scale
          </h2>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground">
            Every metric reflects real delivery — no aspirational targets. ACM-AI
            is feature-complete and ready for Victorian Government deployment.
          </p>
        </div>

        {/* Stats grid */}
        <motion.div
          ref={ref}
          variants={staggerContainer}
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          className="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-6"
        >
          {stats.map((stat, i) => (
            <motion.div
              key={i}
              variants={fadeUp}
              className={cn(
                "flex flex-col items-center justify-between rounded-2xl border border-border bg-card p-6 text-center",
                "shadow-[var(--shadow-sm)] transition-shadow duration-300 hover:shadow-[var(--shadow-md)]",
                "group"
              )}
            >
              {/* Number */}
              <AnimatedCounter
                end={stat.end}
                suffix={stat.suffix}
                label={stat.label}
                duration={1800}
                className="w-full"
              />

              {/* Sublabel */}
              <p className="mt-3 text-xs text-muted-foreground/60 leading-snug">
                {stat.sublabel}
              </p>

              {/* Accent underline */}
              <div
                className={cn(
                  "mt-4 h-0.5 w-8 rounded-full bg-vaea-teal-300 transition-all duration-300",
                  "group-hover:w-12 group-hover:bg-vaea-teal-500"
                )}
              />
            </motion.div>
          ))}
        </motion.div>

        {/* Feature-complete callout */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.6, duration: 0.5 }}
          className={cn(
            "mt-12 flex flex-col items-center justify-between gap-4 rounded-2xl",
            "border border-vaea-teal-700/40 bg-vaea-teal-900/10 px-8 py-5",
            "sm:flex-row"
          )}
        >
          <div className="flex items-center gap-3">
            <span className="relative flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-vaea-teal-300 opacity-60" />
              <span className="relative inline-flex h-3 w-3 rounded-full bg-vaea-teal-300" />
            </span>
            <span className="text-sm font-semibold text-foreground">
              Feature Complete
            </span>
            <span className="text-sm text-muted-foreground">
              — All 16 epics delivered as of 22 Feb 2026
            </span>
          </div>
          <span
            className={cn(
              "rounded-full border border-vaea-teal-700/50 bg-vaea-teal-900/20",
              "px-4 py-1.5 text-xs font-semibold tracking-wide text-vaea-teal-300 uppercase"
            )}
          >
            Production Ready
          </span>
        </motion.div>
      </div>
    </section>
  );
}
