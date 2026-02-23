"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { fadeUp, fadeIn, staggerContainer, staggerFast, slideInLeft } from "@/lib/animations";
import { epics, futureEpics, type Epic } from "@/lib/epic-data";

// ---------------------------------------------------------------------------
// Phase configuration
// ---------------------------------------------------------------------------

interface Phase {
  name: string;
  label: string;
  epicIds: string[];
  color: string;
  bgColor: string;
  borderColor: string;
  date: string;
  achievement: string;
}

const PHASES: Phase[] = [
  {
    name: "Phase 1",
    label: "Foundation",
    epicIds: ["E1", "E2", "E3", "E4", "E5"],
    color: "text-vaea-teal-500",
    bgColor: "bg-vaea-teal-500/10",
    borderColor: "border-vaea-teal-500/30",
    date: "Jan 2026",
    achievement: "Core 7-stage extraction pipeline with AG Grid spreadsheet, cell citations, AI chat, and Excel export.",
  },
  {
    name: "Phase 2",
    label: "Product",
    epicIds: ["E6", "E7", "E9", "E10", "E11", "E12"],
    color: "text-vaea-teal-300",
    bgColor: "bg-vaea-teal-300/10",
    borderColor: "border-vaea-teal-300/30",
    date: "Jan–Feb 2026",
    achievement: "Government branding, drag-and-drop upload wizard, document library, hybrid search, and config-driven field schema.",
  },
  {
    name: "Phase 3",
    label: "Polish",
    epicIds: ["E13", "E14", "E15", "E16", "E17", "E18", "E19", "E20"],
    color: "text-vaea-green-500",
    bgColor: "bg-vaea-green-500/10",
    borderColor: "border-vaea-green-500/30",
    date: "Feb 2026",
    achievement: "Knowledge graph visualisation, WCAG 2.1 AA accessibility, real-time SSE extraction monitor, live AI reasoning with AG-UI, 87% extraction accuracy, marketing site, and cross-site navigation.",
  },
];

// ---------------------------------------------------------------------------
// Milestones
// ---------------------------------------------------------------------------

interface Milestone {
  date: string;
  title: string;
  description: string;
}

const MILESTONES: Milestone[] = [
  {
    date: "Jan 2026",
    title: "Project Kickoff",
    description: "E1 extraction pipeline begins. 7-stage agentic workflow with MinerU + Docling PDF table extraction.",
  },
  {
    date: "Feb 2026",
    title: "Feature Complete",
    description: "121 / 131 stories delivered across 19 epics. 318 commits. BAR-compliant data pipeline production-ready.",
  },
  {
    date: "Feb 2026",
    title: "Marketing Site",
    description: "Public-facing marketing site, executive demo environment, and documentation hub launched.",
  },
  {
    date: "Q2 2026",
    title: "Knowledge Graph Intelligence",
    description: "Cross-document entity resolution, relationship inference, and portfolio-level analytics.",
  },
];

// ---------------------------------------------------------------------------
// Helper: get epics for a list of IDs
// ---------------------------------------------------------------------------

function getEpicsForIds(ids: string[]): Epic[] {
  return ids.map((id) => epics.find((e) => e.id === id)).filter(Boolean) as Epic[];
}

// ---------------------------------------------------------------------------
// TimelineNode
// ---------------------------------------------------------------------------

interface TimelineNodeProps {
  epic: Epic;
  index: number;
  isFuture?: boolean;
  isInProgress?: boolean;
}

function TimelineNode({ epic, index, isFuture = false, isInProgress = false }: TimelineNodeProps) {
  const nodeColor = isFuture
    ? "bg-muted border-border text-muted-foreground"
    : isInProgress
      ? "bg-amber-500/20 border-amber-500 text-amber-600"
      : "bg-vaea-teal-500/20 border-vaea-teal-500 text-vaea-teal-700";

  const textColor = isFuture
    ? "text-muted-foreground"
    : isInProgress
      ? "text-amber-700 dark:text-amber-400"
      : "text-vaea-teal-700 dark:text-vaea-teal-300";

  return (
    <motion.div
      variants={fadeUp}
      custom={index}
      className="flex flex-col items-center gap-2 min-w-[100px]"
    >
      {/* Node circle */}
      <div
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2",
          nodeColor
        )}
      >
        {isFuture ? (
          <span className="h-2 w-2 rounded-full bg-muted-foreground" />
        ) : isInProgress ? (
          <svg className="h-4 w-4 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden>
            <circle cx="12" cy="12" r="9" />
            <path d="M12 7v5l3 3" />
          </svg>
        ) : (
          <svg className="h-4 w-4 text-vaea-teal-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden>
            <polyline points="20 6 9 17 4 12" />
          </svg>
        )}
      </div>

      {/* Label */}
      <div className="text-center">
        <p className={cn("font-[family-name:var(--font-jetbrains-mono)] text-xs font-semibold", textColor)}>
          {epic.id}
        </p>
        <p className="mt-0.5 max-w-[90px] text-center text-xs text-muted-foreground leading-snug">
          {epic.title.length > 22 ? epic.title.slice(0, 22) + "…" : epic.title}
        </p>
      </div>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// PhaseDetailCard
// ---------------------------------------------------------------------------

interface PhaseDetailCardProps {
  phase: Phase;
}

function PhaseDetailCard({ phase }: PhaseDetailCardProps) {
  const phaseEpics = getEpicsForIds(phase.epicIds);

  return (
    <motion.div
      variants={fadeUp}
      className={cn(
        "rounded-2xl border p-6 space-y-4",
        phase.bgColor,
        phase.borderColor
      )}
    >
      <div>
        <p className={cn("font-[family-name:var(--font-jetbrains-mono)] text-xs font-semibold uppercase tracking-widest", phase.color)}>
          {phase.name}
        </p>
        <h3 className="mt-1 font-[family-name:var(--font-dm-serif)] text-2xl text-foreground">
          {phase.label}
        </h3>
        <p className="mt-1 text-xs text-muted-foreground">{phase.date}</p>
      </div>

      <p className="text-sm text-muted-foreground leading-relaxed">{phase.achievement}</p>

      <div className="space-y-1.5">
        {phaseEpics.map((epic) => (
          <div key={epic.id} className="flex items-center gap-2">
            <svg
              className={cn("h-3.5 w-3.5 shrink-0", phase.color)}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              aria-hidden
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span className="text-xs text-foreground">{epic.title}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// MilestoneRow (alternating left/right)
// ---------------------------------------------------------------------------

interface MilestoneRowProps {
  milestone: Milestone;
  index: number;
}

function MilestoneRow({ milestone, index }: MilestoneRowProps) {
  const isLeft = index % 2 === 0;

  return (
    <div className="relative flex items-start gap-0">
      {/* Left content */}
      <div className={cn("w-1/2 pr-8", !isLeft && "invisible")}>
        {isLeft && (
          <motion.div
            variants={slideInLeft}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="rounded-xl border border-border bg-card p-5 text-right"
          >
            <p className="font-[family-name:var(--font-jetbrains-mono)] text-xs font-semibold text-vaea-teal-500">
              {milestone.date}
            </p>
            <p className="mt-1 font-semibold text-foreground">{milestone.title}</p>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              {milestone.description}
            </p>
          </motion.div>
        )}
      </div>

      {/* Center dot + line */}
      <div className="relative flex flex-col items-center">
        <div className="z-10 flex h-5 w-5 items-center justify-center rounded-full border-2 border-vaea-teal-500 bg-background">
          <span className="h-2 w-2 rounded-full bg-vaea-teal-500" />
        </div>
      </div>

      {/* Right content */}
      <div className={cn("w-1/2 pl-8", isLeft && "invisible")}>
        {!isLeft && (
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="rounded-xl border border-border bg-card p-5"
          >
            <p className="font-[family-name:var(--font-jetbrains-mono)] text-xs font-semibold text-vaea-teal-500">
              {milestone.date}
            </p>
            <p className="mt-1 font-semibold text-foreground">{milestone.title}</p>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              {milestone.description}
            </p>
          </motion.div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// FutureEpicCard
// ---------------------------------------------------------------------------

interface FutureEpicCardProps {
  epic: (typeof futureEpics)[number];
  priority: number;
}

function FutureEpicCard({ epic, priority }: FutureEpicCardProps) {
  const isInProgress = epic.status === "in-progress";
  const statusLabel = isInProgress ? "In Progress" : "Planned";
  const statusClass = isInProgress
    ? "bg-amber-500/10 text-amber-600 border border-amber-500/30"
    : "bg-muted text-muted-foreground border border-border";

  const priorityColors = ["bg-red-500", "bg-amber-500", "bg-blue-500"];

  return (
    <motion.div
      variants={fadeUp}
      className="rounded-2xl border border-border bg-card p-6 space-y-4"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-[family-name:var(--font-jetbrains-mono)] text-xs font-semibold text-muted-foreground">
            {epic.id}
          </p>
          <h4 className="mt-1 font-semibold text-foreground">{epic.title}</h4>
        </div>
        <span className={cn("shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium", statusClass)}>
          {statusLabel}
        </span>
      </div>

      <p className="text-sm text-muted-foreground leading-relaxed">{epic.description}</p>

      {/* Priority indicator */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">Priority</span>
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className={cn(
                "h-1.5 w-4 rounded-full",
                i < 4 - priority ? priorityColors[2 - i] : "bg-muted"
              )}
            />
          ))}
        </div>
        <span className="text-xs text-muted-foreground">
          {priority === 1 ? "High" : priority === 2 ? "Medium" : "Low"}
        </span>
      </div>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function RoadmapPage() {
  // All timeline epics: completed + future
  const completedEpics = epics;
  const phase1Epics = getEpicsForIds(PHASES[0].epicIds);
  const phase2Epics = getEpicsForIds(PHASES[1].epicIds);
  const phase3Epics = getEpicsForIds(PHASES[2].epicIds);

  // Remaining completed epics not in a named phase (none in this case, but safe)
  const namedIds = new Set(PHASES.flatMap((p) => p.epicIds));
  const ungrouped = completedEpics.filter((e) => !namedIds.has(e.id));

  return (
    <div className="min-h-screen bg-background">
      {/* ── A. Page Header ── */}
      <section className="border-b border-border bg-card">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            className="max-w-3xl"
          >
            <p className="mb-3 font-[family-name:var(--font-jetbrains-mono)] text-xs font-medium uppercase tracking-widest text-vaea-teal-500">
              Product Roadmap
            </p>
            <h1 className="font-[family-name:var(--font-dm-serif)] text-5xl tracking-tight text-foreground">
              From first commit to feature-complete — and beyond
            </h1>
            <p className="mt-4 text-lg text-muted-foreground">
              19 epics delivered in under 8 weeks of autonomous development. More innovation ahead.
            </p>

            {/* Quick stats strip */}
            <div className="mt-8 flex flex-wrap gap-6">
              {[
                { value: "19", label: "Epics complete" },
                { value: "121", label: "Stories delivered" },
                { value: "318", label: "Commits" },
                { value: "3", label: "Planned next" },
              ].map((stat) => (
                <div key={stat.label}>
                  <p className="font-[family-name:var(--font-dm-serif)] text-3xl text-foreground">
                    {stat.value}
                  </p>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      <div className="mx-auto max-w-7xl space-y-20 px-4 py-16 sm:px-6 lg:px-8">

        {/* ── B. Horizontal Scrollable Timeline ── */}
        <section>
          <motion.h2
            variants={fadeIn}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="mb-8 text-xl font-semibold text-foreground"
          >
            Epic Timeline
          </motion.h2>

          <div className="relative overflow-x-auto pb-4">
            {/* Horizontal connecting line */}
            <div className="absolute top-5 left-0 right-0 h-0.5 bg-border" style={{ zIndex: 0 }} />

            <motion.div
              variants={staggerFast}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-80px" }}
              className="relative flex gap-6 min-w-max px-4"
              style={{ zIndex: 1 }}
            >
              {/* Phase 1 group */}
              <div className="flex flex-col items-start gap-4">
                <span className="rounded-full bg-vaea-teal-500/10 px-3 py-1 text-xs font-semibold text-vaea-teal-500 border border-vaea-teal-500/20">
                  Phase 1 — Foundation
                </span>
                <div className="flex gap-6">
                  {phase1Epics.map((epic, i) => (
                    <TimelineNode key={epic.id} epic={epic} index={i} />
                  ))}
                </div>
              </div>

              {/* Connector */}
              <div className="flex items-center mt-6">
                <svg className="h-4 w-8 text-border" viewBox="0 0 32 16" fill="none" aria-hidden>
                  <path d="M0 8h32" stroke="currentColor" strokeWidth="2" />
                  <path d="M24 4l8 4-8 4" stroke="currentColor" strokeWidth="2" fill="none" />
                </svg>
              </div>

              {/* Phase 2 group */}
              <div className="flex flex-col items-start gap-4">
                <span className="rounded-full bg-vaea-teal-300/10 px-3 py-1 text-xs font-semibold text-vaea-teal-300 border border-vaea-teal-300/20">
                  Phase 2 — Product
                </span>
                <div className="flex gap-6">
                  {phase2Epics.map((epic, i) => (
                    <TimelineNode key={epic.id} epic={epic} index={i} />
                  ))}
                </div>
              </div>

              {/* Connector */}
              <div className="flex items-center mt-6">
                <svg className="h-4 w-8 text-border" viewBox="0 0 32 16" fill="none" aria-hidden>
                  <path d="M0 8h32" stroke="currentColor" strokeWidth="2" />
                  <path d="M24 4l8 4-8 4" stroke="currentColor" strokeWidth="2" fill="none" />
                </svg>
              </div>

              {/* Phase 3 group */}
              <div className="flex flex-col items-start gap-4">
                <span className="rounded-full bg-vaea-green-500/10 px-3 py-1 text-xs font-semibold text-vaea-green-500 border border-vaea-green-500/20">
                  Phase 3 — Polish
                </span>
                <div className="flex gap-6">
                  {phase3Epics.map((epic, i) => (
                    <TimelineNode key={epic.id} epic={epic} index={i} />
                  ))}
                </div>
              </div>

              {/* Ungrouped completed epics (none expected) */}
              {ungrouped.length > 0 && (
                <div className="flex gap-6 mt-10">
                  {ungrouped.map((epic, i) => (
                    <TimelineNode key={epic.id} epic={epic} index={i} />
                  ))}
                </div>
              )}

              {/* Connector to future */}
              <div className="flex items-center mt-6">
                <svg className="h-4 w-8 text-border" viewBox="0 0 32 16" fill="none" aria-hidden>
                  <path d="M0 8h32" stroke="currentColor" strokeWidth="2" strokeDasharray="4 3" />
                  <path d="M24 4l8 4-8 4" stroke="currentColor" strokeWidth="2" fill="none" />
                </svg>
              </div>

              {/* Future epics */}
              <div className="flex flex-col items-start gap-4">
                <span className="rounded-full bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-600 border border-amber-500/20">
                  What&apos;s Next
                </span>
                <div className="flex gap-6">
                  {futureEpics.map((epic, i) => {
                    const isInProgress = epic.status === "in-progress";
                    // Adapt futureEpic shape to match Epic for TimelineNode
                    const adapted: Epic = {
                      id: epic.id,
                      code: epic.id,
                      title: epic.title,
                      stories: 0,
                      status: epic.status,
                      highlight: epic.description,
                      category: "infra",
                    };
                    return (
                      <TimelineNode
                        key={epic.id}
                        epic={adapted}
                        index={i}
                        isFuture={!isInProgress}
                        isInProgress={isInProgress}
                      />
                    );
                  })}
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* ── C. Phase Detail Cards ── */}
        <section>
          <motion.h2
            variants={fadeIn}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="mb-8 text-xl font-semibold text-foreground"
          >
            Phase Summary
          </motion.h2>
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
          >
            {PHASES.map((phase) => (
              <PhaseDetailCard key={phase.name} phase={phase} />
            ))}

            {/* What's Next card */}
            <motion.div
              variants={fadeUp}
              className="rounded-2xl border border-amber-500/30 bg-amber-500/5 p-6 space-y-4"
            >
              <div>
                <p className="font-[family-name:var(--font-jetbrains-mono)] text-xs font-semibold uppercase tracking-widest text-amber-600">
                  What&apos;s Next
                </p>
                <h3 className="mt-1 font-[family-name:var(--font-dm-serif)] text-2xl text-foreground">
                  Future Epics
                </h3>
                <p className="mt-1 text-xs text-muted-foreground">Q2 2026 onwards</p>
              </div>

              <p className="text-sm text-muted-foreground leading-relaxed">
                Three epics planned to extend ACM-AI from a data extraction platform to a full compliance intelligence system.
              </p>

              <div className="space-y-2">
                {futureEpics.map((epic) => (
                  <div key={epic.id} className="flex items-start gap-2">
                    <span
                      className={cn(
                        "mt-0.5 h-3.5 w-3.5 shrink-0 rounded-full border",
                        epic.status === "in-progress"
                          ? "border-amber-500 bg-amber-500/20"
                          : "border-muted-foreground bg-muted"
                      )}
                    />
                    <div>
                      <p className="text-xs font-semibold text-foreground">{epic.id}: {epic.title}</p>
                      <p className="text-xs text-muted-foreground">{epic.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </motion.div>
        </section>

        {/* ── D. Key Milestones (alternating left/right) ── */}
        <section>
          <motion.h2
            variants={fadeIn}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="mb-10 text-xl font-semibold text-foreground"
          >
            Key Milestones
          </motion.h2>

          {/* Vertical timeline container */}
          <div className="relative mx-auto max-w-4xl">
            {/* Center vertical line */}
            <div className="absolute left-1/2 top-0 bottom-0 w-0.5 -translate-x-1/2 bg-border" />

            <div className="space-y-10">
              {MILESTONES.map((milestone, index) => (
                <MilestoneRow key={index} milestone={milestone} index={index} />
              ))}
            </div>
          </div>
        </section>

        {/* ── E. What's Next Priority Cards ── */}
        <section>
          <motion.div
            variants={fadeIn}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="mb-8 flex items-end justify-between gap-4"
          >
            <h2 className="text-xl font-semibold text-foreground">
              What&apos;s Next
            </h2>
            <p className="text-sm text-muted-foreground">
              3 epics in the pipeline for Q2 2026
            </p>
          </motion.div>

          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="grid gap-6 sm:grid-cols-3"
          >
            {futureEpics.map((epic, index) => (
              <FutureEpicCard
                key={epic.id}
                epic={epic}
                priority={index + 1}
              />
            ))}
          </motion.div>

          {/* Bottom CTA */}
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="mt-12 rounded-2xl border border-border bg-card p-8 text-center"
          >
            <p className="font-[family-name:var(--font-jetbrains-mono)] text-xs font-semibold uppercase tracking-widest text-vaea-teal-500 mb-3">
              Feature Complete — Feb 2026
            </p>
            <h3 className="font-[family-name:var(--font-dm-serif)] text-3xl text-foreground">
              Built in weeks. Ready for production.
            </h3>
            <p className="mt-3 text-muted-foreground max-w-xl mx-auto">
              ACM-AI went from concept to a feature-complete compliance intelligence platform in under 8 weeks of autonomous AI development.
              121 stories. 19 epics. 318 commits. Zero manual data entry.
            </p>
          </motion.div>
        </section>

      </div>
    </div>
  );
}
