"use client";

import { motion } from "framer-motion";
import { useInView } from "@/hooks/useInView";
import { pipelineStages } from "@/lib/sprint-data";
import { slideInLeft, staggerContainer } from "@/lib/animations";
import { cn } from "@/lib/cn";

// Color coding: teal for data stages, coral for AI stages, navy-light for infra
const stageColorMap: Record<string, { accent: string; badge: string; border: string }> = {
  "-1": { accent: "text-vaea-teal-300", badge: "bg-vaea-teal-700/30 text-vaea-teal-100", border: "border-vaea-teal-700/40" },
  "0":  { accent: "text-vaea-teal-100", badge: "bg-vaea-navy-light/80 text-white/70", border: "border-white/10" },
  "0.5": { accent: "text-vaea-coral", badge: "bg-vaea-coral/10 text-vaea-coral", border: "border-vaea-coral/30" },
  "1":  { accent: "text-vaea-teal-300", badge: "bg-vaea-teal-700/30 text-vaea-teal-100", border: "border-vaea-teal-700/40" },
  "2":  { accent: "text-vaea-coral", badge: "bg-vaea-coral/10 text-vaea-coral", border: "border-vaea-coral/30" },
  "2.5": { accent: "text-vaea-coral", badge: "bg-vaea-coral/10 text-vaea-coral", border: "border-vaea-coral/30" },
  "3":  { accent: "text-vaea-teal-300", badge: "bg-vaea-teal-700/30 text-vaea-teal-100", border: "border-vaea-teal-700/40" },
};

function getColor(id: number) {
  return stageColorMap[String(id)] ?? stageColorMap["0"];
}

function stageLabel(id: number): string {
  if (id === -1) return "PRE";
  if (id === 0.5) return "0.5";
  if (id === 2.5) return "2.5";
  return String(id);
}

export function PipelinePreview() {
  const { ref, isInView } = useInView({ threshold: 0.1 });

  return (
    <section className="bg-vaea-navy py-24 overflow-hidden">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        {/* Section header */}
        <div className="mx-auto mb-14 max-w-2xl text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-vaea-teal-300">
            Under the Hood
          </p>
          <h2 className="font-[family-name:var(--font-dm-serif)] text-3xl text-white sm:text-4xl">
            7-Stage Extraction Pipeline
          </h2>
          <p className="mt-4 text-base leading-relaxed text-white/50">
            Every PDF is routed through a precision agentic workflow. Each stage
            handles a distinct aspect of the extraction — no black-box guessing.
          </p>
        </div>

        {/* Horizontal scroll wrapper (mobile), full grid (desktop) */}
        <div
          ref={ref}
          className="overflow-x-auto pb-4 scrollbar-thin"
        >
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate={isInView ? "visible" : "hidden"}
            className="flex gap-3 md:grid md:grid-cols-7 md:gap-3 min-w-max md:min-w-0"
          >
            {pipelineStages.map((stage, index) => {
              const colors = getColor(stage.id);
              return (
                <motion.div
                  key={stage.id}
                  variants={slideInLeft}
                  className="relative flex-shrink-0 w-44 md:w-auto"
                >
                  {/* Connector arrow between cards (except last) */}
                  {index < pipelineStages.length - 1 && (
                    <div className="absolute right-0 top-1/2 z-10 hidden translate-x-full -translate-y-1/2 md:block">
                      <svg
                        width="24"
                        height="16"
                        viewBox="0 0 24 16"
                        fill="none"
                        className="text-vaea-teal-700"
                      >
                        <path
                          d="M0 8H20M20 8L14 2M20 8L14 14"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </div>
                  )}

                  {/* Card */}
                  <div
                    className={cn(
                      "glass rounded-xl p-4 h-full flex flex-col gap-3",
                      "border transition-all duration-300",
                      "hover:bg-white/10",
                      colors.border
                    )}
                  >
                    {/* Stage badge */}
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          "font-[family-name:var(--font-jetbrains-mono)]",
                          "inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs font-bold",
                          colors.badge
                        )}
                      >
                        {stageLabel(stage.id)}
                      </span>
                      <span
                        className={cn(
                          "font-[family-name:var(--font-jetbrains-mono)]",
                          "text-xs font-bold tracking-widest truncate",
                          colors.accent
                        )}
                      >
                        {stage.name}
                      </span>
                    </div>

                    {/* Description */}
                    <p className="text-xs leading-relaxed text-white/60 flex-1">
                      {stage.desc}
                    </p>

                    {/* Tools */}
                    <p className="text-xs text-white/30 font-[family-name:var(--font-jetbrains-mono)] leading-snug border-t border-white/10 pt-2">
                      {stage.tools}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        </div>

        {/* Legend */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-6">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-vaea-teal-300" />
            <span className="text-xs text-white/50">Data stages</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-vaea-coral" />
            <span className="text-xs text-white/50">AI / LLM stages</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-white/30" />
            <span className="text-xs text-white/50">Infrastructure</span>
          </div>
        </div>
      </div>
    </section>
  );
}
