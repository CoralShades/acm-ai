"use client";

import { motion } from "framer-motion";
import useSWR from "swr";
import { cn } from "@/lib/cn";
import { fadeUp, fadeIn, staggerContainer, staggerFast } from "@/lib/animations";
import { velocityData, projectStats } from "@/lib/sprint-data";
import { epics } from "@/lib/epic-data";
import { AnimatedCounter } from "@/components/AnimatedCounter";
import { LiveStatusWidget } from "@/components/LiveStatusWidget";
import { ExtractionAccuracyWidget } from "@/components/ExtractionAccuracyWidget";
import { useInView } from "@/hooks/useInView";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type StatusLevel = "operational" | "degraded" | "down" | "unknown";

interface GitHubStats {
  status: StatusLevel;
  commits: number;
  openPRs: number;
  lastCommitMessage: string;
  lastCommitDate: string;
  workflowStatus: string;
  updatedAt: string;
}

interface VercelStatus {
  status: StatusLevel;
  lastDeployment: string | null;
  deploymentUrl: string | null;
  buildTime: number | null;
  updatedAt: string;
}

interface RailwayStatus {
  status: StatusLevel;
  lastDeploy: string | null;
  uptime: string | null;
  updatedAt: string;
}

// ---------------------------------------------------------------------------
// Fetcher
// ---------------------------------------------------------------------------

const fetcher = (url: string) => fetch(url).then((r) => r.json());

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatRelativeDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

function CardSkeleton() {
  return (
    <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 animate-pulse rounded-xl bg-muted" />
        <div className="space-y-2 flex-1">
          <div className="h-4 w-24 animate-pulse rounded bg-muted" />
          <div className="h-3 w-16 animate-pulse rounded bg-muted" />
        </div>
      </div>
      <div className="space-y-2">
        <div className="h-3 w-full animate-pulse rounded bg-muted" />
        <div className="h-3 w-3/4 animate-pulse rounded bg-muted" />
        <div className="h-3 w-1/2 animate-pulse rounded bg-muted" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// CircularRing
// ---------------------------------------------------------------------------

interface CircularRingProps {
  percent: number;
  label: string;
  color: string;
  enabled: boolean;
}

function CircularRing({ percent, label, color, enabled }: CircularRingProps) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const displayPercent = enabled ? percent : 0;
  const offset = circumference - (displayPercent / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative h-32 w-32">
        <svg className="h-32 w-32 -rotate-90" viewBox="0 0 120 120">
          {/* Track */}
          <circle
            cx="60"
            cy="60"
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            className="text-muted"
          />
          {/* Fill */}
          <circle
            cx="60"
            cy="60"
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className={cn("transition-all duration-1000 ease-out", color)}
            style={{ transitionDelay: enabled ? "200ms" : "0ms" }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-[family-name:var(--font-dm-serif)] text-2xl text-foreground leading-none">
            {displayPercent}
          </span>
          <span className="text-xs text-muted-foreground">%</span>
        </div>
      </div>
      <p className="text-sm font-medium text-muted-foreground text-center">{label}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SprintSparkline
// ---------------------------------------------------------------------------

function SprintSparkline() {
  const { ref, isInView } = useInView({ threshold: 0.3 });

  const values = velocityData.map((d) => d.done);
  const targets = velocityData.map((d) => d.target);
  const maxVal = Math.max(...values, ...targets);
  const minVal = 0;
  const range = maxVal - minVal || 1;

  const width = 600;
  const height = 120;
  const padX = 20;
  const padY = 10;
  const innerW = width - padX * 2;
  const innerH = height - padY * 2;

  const toX = (i: number) => padX + (i / (values.length - 1)) * innerW;
  const toY = (v: number) => padY + (1 - (v - minVal) / range) * innerH;

  const donePoints = values.map((v, i) => `${toX(i)},${toY(v)}`).join(" ");
  const targetPoints = targets.map((v, i) => `${toX(i)},${toY(v)}`).join(" ");

  return (
    <div ref={ref} className="w-full overflow-x-auto">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full max-w-full h-auto"
        aria-label="Sprint velocity sparkline"
      >
        {/* Grid lines */}
        {[4, 8, 12].map((tick) => (
          <line
            key={tick}
            x1={padX}
            y1={toY(tick)}
            x2={width - padX}
            y2={toY(tick)}
            stroke="currentColor"
            strokeWidth="0.5"
            strokeDasharray="4 4"
            className="text-border"
          />
        ))}

        {/* Target line */}
        <polyline
          points={targetPoints}
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeDasharray="6 4"
          className="text-muted-foreground"
        />

        {/* Done line */}
        <polyline
          points={isInView ? donePoints : `${toX(0)},${toY(values[0])} ${toX(0)},${toY(values[0])}`}
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-vaea-teal-500 transition-all duration-1000"
        />

        {/* Data dots */}
        {isInView &&
          values.map((v, i) => (
            <circle
              key={i}
              cx={toX(i)}
              cy={toY(v)}
              r="4"
              fill="currentColor"
              className="text-vaea-teal-500"
            />
          ))}

        {/* Sprint labels */}
        {velocityData.map((d, i) => (
          <text
            key={i}
            x={toX(i)}
            y={height}
            textAnchor="middle"
            fontSize="9"
            fill="currentColor"
            className="text-muted-foreground"
          >
            {d.sprint}
          </text>
        ))}
      </svg>

      <div className="mt-2 flex items-center gap-6 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-0.5 w-4 bg-vaea-teal-500 rounded" />
          Actual velocity
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-0.5 w-4 border-t border-dashed border-muted-foreground" />
          Target
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// GitHub Card
// ---------------------------------------------------------------------------

function GitHubCard() {
  const { data, isLoading } = useSWR<GitHubStats>("/api/github/stats", fetcher, {
    refreshInterval: 60000,
  });

  if (isLoading) return <CardSkeleton />;

  const workflowColor =
    data?.workflowStatus === "success"
      ? "text-emerald-500"
      : data?.workflowStatus === "failure"
        ? "text-red-500"
        : "text-amber-500";

  return (
    <div className="rounded-2xl border border-border bg-card p-6 space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-vaea-navy text-white">
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
              <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
            </svg>
          </div>
          <div>
            <p className="font-semibold text-foreground">GitHub</p>
            <LiveStatusWidget label={data?.status ?? "unknown"} status={data?.status ?? "unknown"} />
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Commits</span>
          <span className="font-[family-name:var(--font-jetbrains-mono)] font-semibold text-foreground">
            {data?.commits ?? projectStats.commits}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Open PRs</span>
          <span className="font-[family-name:var(--font-jetbrains-mono)] text-foreground">
            {data?.openPRs ?? "—"}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Last commit</span>
          <span className="font-[family-name:var(--font-jetbrains-mono)] text-foreground text-xs">
            {formatRelativeDate(data?.lastCommitDate)}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">CI status</span>
          <span className={cn("font-[family-name:var(--font-jetbrains-mono)] text-xs uppercase", workflowColor)}>
            {data?.workflowStatus ?? "—"}
          </span>
        </div>
      </div>

      {/* Last commit message */}
      {data?.lastCommitMessage && (
        <p className="rounded-lg bg-muted px-3 py-2 font-[family-name:var(--font-jetbrains-mono)] text-xs text-muted-foreground truncate">
          {data.lastCommitMessage}
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Vercel Card
// ---------------------------------------------------------------------------

function VercelCard() {
  const { data, isLoading } = useSWR<VercelStatus>("/api/vercel/status", fetcher, {
    refreshInterval: 60000,
  });

  if (isLoading) return <CardSkeleton />;

  return (
    <div className="rounded-2xl border border-border bg-card p-6 space-y-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-black text-white">
            <svg className="h-5 w-5" viewBox="0 0 512 512" fill="currentColor" aria-hidden>
              <path d="M256 48L496 464H16L256 48Z" />
            </svg>
          </div>
          <div>
            <p className="font-semibold text-foreground">Vercel</p>
            <LiveStatusWidget label={data?.status ?? "unknown"} status={data?.status ?? "unknown"} />
          </div>
        </div>
      </div>

      <div className="space-y-2.5">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Last deploy</span>
          <span className="font-[family-name:var(--font-jetbrains-mono)] text-foreground text-xs">
            {formatRelativeDate(data?.lastDeployment)}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Build time</span>
          <span className="font-[family-name:var(--font-jetbrains-mono)] text-foreground">
            {data?.buildTime != null ? `${data.buildTime}s` : "—"}
          </span>
        </div>
        {data?.deploymentUrl && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">URL</span>
            <a
              href={data.deploymentUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="font-[family-name:var(--font-jetbrains-mono)] text-xs text-vaea-teal-500 hover:underline truncate max-w-[160px]"
            >
              {data.deploymentUrl.replace("https://", "")}
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Railway Card
// ---------------------------------------------------------------------------

function RailwayCard() {
  const { data, isLoading } = useSWR<RailwayStatus>("/api/railway/status", fetcher, {
    refreshInterval: 60000,
  });

  if (isLoading) return <CardSkeleton />;

  return (
    <div className="rounded-2xl border border-border bg-card p-6 space-y-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#8a2be2] text-white">
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
              <path d="M12 2C6.477 2 2 6.477 2 12c0 4.236 2.636 7.855 6.356 9.312-.088-.791-.167-2.005.035-2.868.181-.78 1.172-4.97 1.172-4.97s-.299-.598-.299-1.482c0-1.388.806-2.428 1.808-2.428.852 0 1.266.64 1.266 1.408 0 .858-.545 2.14-.828 3.33-.236.995.499 1.806 1.476 1.806 1.772 0 3.137-1.868 3.137-4.565 0-2.387-1.716-4.055-4.164-4.055-2.838 0-4.502 2.128-4.502 4.33 0 .857.33 1.776.742 2.277a.3.3 0 0 1 .069.284c-.076.312-.244.996-.277 1.134-.044.183-.146.222-.336.134C5.73 16.74 4.5 14.81 4.5 12c0-3.866 2.847-6.866 7.08-6.866 3.598 0 6.4 2.566 6.4 5.993 0 3.58-2.26 6.454-5.39 6.454-1.053 0-2.044-.548-2.382-1.193l-.648 2.418c-.234.902-.869 2.032-1.295 2.72.977.302 2.012.466 3.085.466C17.523 22 22 17.523 22 12S17.523 2 12 2z" />
            </svg>
          </div>
          <div>
            <p className="font-semibold text-foreground">Railway</p>
            <LiveStatusWidget label={data?.status ?? "unknown"} status={data?.status ?? "unknown"} />
          </div>
        </div>
      </div>

      <div className="space-y-2.5">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Last deploy</span>
          <span className="font-[family-name:var(--font-jetbrains-mono)] text-foreground text-xs">
            {formatRelativeDate(data?.lastDeploy)}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Uptime</span>
          <span className="font-[family-name:var(--font-jetbrains-mono)] text-foreground">
            {data?.uptime ?? "—"}
          </span>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function StatusPage() {
  const { ref: healthRef, isInView: healthInView } = useInView({ threshold: 0.2 });
  const { ref: epicRef, isInView: epicInView } = useInView({ threshold: 0.1 });

  const testSuites = [
    { label: "Total Tests", pass: 642, total: 813, pct: 79 },
    { label: "Active Tests", pass: 642, total: 642, pct: 100 },
    { label: "Pre-existing Failures", pass: 0, total: 171, pct: 0 },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* ── Page Header ── */}
      <section className="border-b border-border bg-card">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            className="max-w-2xl"
          >
            <p className="mb-3 font-[family-name:var(--font-jetbrains-mono)] text-xs font-medium uppercase tracking-widest text-vaea-teal-500">
              Infrastructure
            </p>
            <h1 className="font-[family-name:var(--font-dm-serif)] text-5xl tracking-tight text-foreground">
              System Status
            </h1>
            <p className="mt-4 text-lg text-muted-foreground">
              Live infrastructure health for ACM-AI — refreshed every 60 seconds.
            </p>
          </motion.div>
        </div>
      </section>

      <div className="mx-auto max-w-7xl space-y-16 px-4 py-16 sm:px-6 lg:px-8">

        {/* ── B. Infrastructure Status Grid ── */}
        <section>
          <motion.h2
            variants={fadeIn}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="mb-6 text-xl font-semibold text-foreground"
          >
            Infrastructure
          </motion.h2>
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
          >
            <motion.div variants={fadeUp}><GitHubCard /></motion.div>
            <motion.div variants={fadeUp}><VercelCard /></motion.div>
            <motion.div variants={fadeUp}><RailwayCard /></motion.div>
          </motion.div>
        </section>

        {/* ── C. Project Health Metrics ── */}
        <section ref={healthRef}>
          <motion.h2
            variants={fadeIn}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="mb-8 text-xl font-semibold text-foreground"
          >
            Project Health
          </motion.h2>

          <div className="rounded-2xl border border-border bg-card p-8">
            <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
              <CircularRing
                percent={projectStats.completionRate}
                label="Story completion"
                color="text-vaea-teal-500"
                enabled={healthInView}
              />
              <CircularRing
                percent={95}
                label="Epic completion"
                color="text-vaea-teal-300"
                enabled={healthInView}
              />
              <CircularRing
                percent={79}
                label="Test pass rate (642/813)"
                color="text-vaea-green-500"
                enabled={healthInView}
              />
            </div>

            {/* Summary counters */}
            <div className="mt-10 grid grid-cols-2 gap-6 border-t border-border pt-8 sm:grid-cols-4">
              <AnimatedCounter end={projectStats.storiesDelivered} suffix="" label="Stories delivered" />
              <AnimatedCounter end={projectStats.totalStories} suffix="" label="Total stories" />
              <AnimatedCounter end={projectStats.commits} suffix="" label="Commits" />
              <AnimatedCounter end={projectStats.extractionAccuracy} suffix="%" label="Extraction accuracy" />
            </div>
          </div>

          {/* Extraction Accuracy Widget */}
          <ExtractionAccuracyWidget className="mt-8" />
        </section>

        {/* ── D. Epic Progress Bars ── */}
        <section ref={epicRef}>
          <motion.h2
            variants={fadeIn}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="mb-6 text-xl font-semibold text-foreground"
          >
            Epic Progress
          </motion.h2>

          <motion.div
            variants={staggerFast}
            initial="hidden"
            animate={epicInView ? "visible" : "hidden"}
            className="space-y-3"
          >
            {epics.map((epic) => (
              <motion.div
                key={epic.id}
                variants={fadeUp}
                className="rounded-xl border border-border bg-card px-5 py-4"
              >
                <div className="mb-2 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="font-[family-name:var(--font-jetbrains-mono)] text-xs font-semibold text-vaea-teal-500 shrink-0">
                      {epic.id}
                    </span>
                    <span className="truncate text-sm font-medium text-foreground">
                      {epic.title}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-xs text-muted-foreground">
                      {epic.stories} {epic.stories === 1 ? "story" : "stories"}
                    </span>
                    <span className="font-[family-name:var(--font-jetbrains-mono)] text-xs font-semibold text-emerald-500">
                      100%
                    </span>
                  </div>
                </div>
                {/* Progress bar */}
                <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full bg-vaea-teal-500 transition-all duration-700",
                      epicInView ? "w-full" : "w-0"
                    )}
                    style={{ transitionDelay: `${epics.indexOf(epic) * 40}ms` }}
                  />
                </div>
              </motion.div>
            ))}
          </motion.div>
        </section>

        {/* ── E. Sprint Velocity Sparkline ── */}
        <section>
          <motion.h2
            variants={fadeIn}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="mb-6 text-xl font-semibold text-foreground"
          >
            Sprint Velocity
          </motion.h2>
          <div className="rounded-2xl border border-border bg-card p-6">
            <SprintSparkline />
            <p className="mt-3 text-xs text-muted-foreground">
              Stories completed per sprint across 12 sprints. S10 peak: 14 stories delivered.
            </p>
          </div>
        </section>

        {/* ── F. Test Suite Summary ── */}
        <section>
          <motion.h2
            variants={fadeIn}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="mb-2 text-xl font-semibold text-foreground"
          >
            Test Suite
          </motion.h2>
          <p className="mb-6 text-sm text-muted-foreground">
            642 passing / 813 total — 171 pre-existing import failures from upstream dependencies
          </p>
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="grid gap-6 sm:grid-cols-3"
          >
            {testSuites.map((suite) => (
              <motion.div
                key={suite.label}
                variants={fadeUp}
                className="rounded-2xl border border-border bg-card p-6"
              >
                <div className="mb-4 flex items-center justify-between">
                  <p className="font-medium text-foreground">{suite.label}</p>
                  <span
                    className={cn(
                      "rounded-full px-2 py-0.5 font-[family-name:var(--font-jetbrains-mono)] text-xs font-semibold",
                      suite.pct >= 90
                        ? "bg-emerald-500/10 text-emerald-600"
                        : "bg-amber-500/10 text-amber-600"
                    )}
                  >
                    {suite.pct}%
                  </span>
                </div>

                {/* Bar */}
                <div className="mb-3 h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-vaea-teal-500"
                    style={{ width: `${suite.pct}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{suite.pass} passing</span>
                  <span>{suite.total - suite.pass} failing</span>
                </div>

                <p className="mt-2 font-[family-name:var(--font-jetbrains-mono)] text-xs text-muted-foreground">
                  {suite.pass} / {suite.total}
                </p>
              </motion.div>
            ))}
          </motion.div>
        </section>

      </div>
    </div>
  );
}
