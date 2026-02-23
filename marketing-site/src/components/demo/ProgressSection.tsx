"use client";

import { motion } from "framer-motion";
import {
  CheckCircle,
  Award,
  Database,
  Shield,
} from "lucide-react";
import {
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from "recharts";
import { epics } from "@/lib/epic-data";
import { velocityData, projectStats } from "@/lib/sprint-data";
import { PROJECT_TRUTH } from "@/lib/project-truth";
import { fadeUp, staggerContainer } from "@/lib/animations";
import { useInView } from "@/hooks/useInView";
import { cn } from "@/lib/cn";

// Build bar chart data from epics (exclude E8 archived)
const epicChartData = epics
  .filter((e) => e.status === "done")
  .map((e) => ({
    epic: e.id,
    stories: e.stories,
  }));

const avgVelocity =
  Math.round(
    (epicChartData.reduce((sum, e) => sum + e.stories, 0) / epicChartData.length) * 10
  ) / 10;

const radarData = [
  { subject: "Extraction", completion: 100 },
  { subject: "Grid/UX", completion: 100 },
  { subject: "Export", completion: 100 },
  { subject: "Chat", completion: 100 },
  { subject: "Infrastructure", completion: 95 },
  { subject: "Testing", completion: 87 },
];

// ---------------------------------------------------------------------------
// RingMetric
// ---------------------------------------------------------------------------

interface RingMetricProps {
  value: number;
  max: number;
  label: string;
  color: string;
  enabled: boolean;
}

function RingMetric({ value, max, label, color, enabled }: RingMetricProps) {
  const pct = Math.round((value / max) * 100);
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const displayPct = enabled ? pct : 0;
  const offset = circumference - (displayPct / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative h-24 w-24">
        <svg className="h-24 w-24 -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="6"
            className="text-muted"
          />
          <motion.circle
            cx="50"
            cy="50"
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="6"
            strokeDasharray={circumference}
            strokeLinecap="round"
            className={color}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.2, ease: "easeOut", delay: 0.2 }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-[family-name:var(--font-dm-serif)] text-lg text-foreground leading-none">
            {displayPct}%
          </span>
        </div>
      </div>
      <div className="text-center">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        <p className="text-xs text-muted-foreground/60">
          {value}/{max}
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Custom Recharts Tooltip
// ---------------------------------------------------------------------------

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number; name: string; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-md">
      <p className="text-xs font-semibold text-foreground mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="text-xs text-muted-foreground">
          <span style={{ color: p.color }}>●</span> {p.name}: {p.value}
        </p>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// StatusBadge
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: string }) {
  if (status === "done") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-700">
        DONE
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-vaea-navy/10 text-vaea-navy">
      ARCHIVED
    </span>
  );
}

// ---------------------------------------------------------------------------
// ProgressSection
// ---------------------------------------------------------------------------

export function ProgressSection() {
  const { ref, isInView } = useInView({ threshold: 0.05 });

  return (
    <div className="space-y-6" ref={ref}>
      {/* Header */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
      >
        <h2 className="text-xl font-bold text-vaea-navy">
          Project Delivery Dashboard
        </h2>
        <p className="text-sm mt-1 text-foreground/50">
          ACM-AI v1.0 — Feature Complete as of {projectStats.featureComplete}
        </p>
      </motion.div>

      {/* Ring Metrics */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="grid grid-cols-2 sm:grid-cols-4 gap-6 rounded-xl border border-border p-6 bg-card"
      >
        <motion.div variants={fadeUp}>
          <RingMetric
            value={PROJECT_TRUTH.stories.done}
            max={PROJECT_TRUTH.stories.total}
            label="Stories"
            color="text-vaea-teal-500"
            enabled={isInView}
          />
        </motion.div>
        <motion.div variants={fadeUp}>
          <RingMetric
            value={PROJECT_TRUTH.epics.done}
            max={PROJECT_TRUTH.epics.total}
            label="Epics"
            color="text-vaea-coral"
            enabled={isInView}
          />
        </motion.div>
        <motion.div variants={fadeUp}>
          <RingMetric
            value={PROJECT_TRUTH.extraction.testRecordsPassing}
            max={PROJECT_TRUTH.extraction.testRecordsTotal}
            label="E2E Accuracy"
            color="text-amber-500"
            enabled={isInView}
          />
        </motion.div>
        <motion.div variants={fadeUp}>
          <div className="flex flex-col items-center gap-2">
            <div className="relative flex h-24 w-24 flex-col items-center justify-center">
              <Database
                size={20}
                className="text-vaea-navy mb-1"
                aria-hidden="true"
              />
              <span className="font-[family-name:var(--font-dm-serif)] text-2xl text-foreground">
                {PROJECT_TRUTH.git.totalCommits}
              </span>
            </div>
            <p className="text-xs font-medium text-muted-foreground">
              Git Commits
            </p>
          </div>
        </motion.div>
      </motion.div>

      {/* Stat Cards */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="grid grid-cols-2 sm:grid-cols-4 gap-4"
      >
        {[
          {
            icon: CheckCircle,
            label: "Stories Done",
            value: `${projectStats.storiesDelivered} / ${projectStats.totalStories}`,
            colorClass: "text-vaea-teal-300",
            bgClass: "bg-vaea-teal-300/10",
          },
          {
            icon: Award,
            label: "Epics Complete",
            value: `${projectStats.epicsComplete} / ${projectStats.totalEpics}`,
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
            icon: Shield,
            label: "Change Proposals",
            value: `${projectStats.changeProposals} Navigated`,
            colorClass: "text-vaea-green-500",
            bgClass: "bg-vaea-green-500/10",
          },
        ].map((card, i) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={i}
              variants={fadeUp}
              className="rounded-xl p-5 shadow-sm border border-border bg-card"
            >
              <div className="flex items-center gap-3 mb-2">
                <div
                  className={cn(
                    "w-10 h-10 rounded-lg flex items-center justify-center",
                    card.bgClass
                  )}
                >
                  <Icon
                    size={20}
                    className={card.colorClass}
                    aria-hidden="true"
                  />
                </div>
                <span className="text-sm font-medium text-foreground/60">
                  {card.label}
                </span>
              </div>
              <div className="text-2xl font-bold tracking-tight text-foreground">
                {card.value}
              </div>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Stories per Epic Bar Chart with Gradient */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="rounded-xl border border-border p-4 bg-card"
      >
        <h3 className="text-sm font-bold mb-3 text-vaea-navy">
          Stories per Epic
        </h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={epicChartData} margin={{ bottom: 60, left: -10 }}>
            <defs>
              <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3a8f8a" />
                <stop offset="100%" stopColor="#d4614a" />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="epic"
              angle={-35}
              textAnchor="end"
              fontSize={11}
              tick={{ fill: "#1e223588" }}
              interval={0}
            />
            <YAxis fontSize={10} tick={{ fill: "#1e223588" }} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine
              y={avgVelocity}
              stroke="#d4614a"
              strokeDasharray="4 3"
              strokeWidth={1.5}
              label={{
                value: `Avg: ${avgVelocity}`,
                position: "right",
                fontSize: 10,
                fill: "#d4614a",
              }}
            />
            <Bar
              dataKey="stories"
              fill="url(#barGradient)"
              radius={[6, 6, 0, 0]}
              name="Stories"
            />
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Epic Table with animated progress bars */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="rounded-xl border border-border overflow-hidden bg-card"
      >
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-vaea-navy/5">
              <th className="px-3 py-2 text-left font-bold text-vaea-navy">
                Epic
              </th>
              <th className="px-3 py-2 text-left font-bold text-vaea-navy">
                Title
              </th>
              <th className="px-3 py-2 text-center font-bold text-vaea-navy">
                Stories
              </th>
              <th className="px-3 py-2 text-center font-bold text-vaea-navy">
                Progress
              </th>
              <th className="px-3 py-2 text-center font-bold text-vaea-navy">
                Status
              </th>
              <th className="px-3 py-2 text-left font-bold text-vaea-navy">
                Key Achievement
              </th>
            </tr>
          </thead>
          <tbody>
            {epics.map((epic, i) => (
              <tr key={i} className="border-t border-border/50">
                <td className="px-3 py-2 font-[family-name:var(--font-jetbrains-mono)] font-semibold text-vaea-teal-300">
                  {epic.id}
                </td>
                <td className="px-3 py-2 text-vaea-navy">{epic.title}</td>
                <td className="px-3 py-2 text-center font-bold text-vaea-navy">
                  {epic.stories}
                </td>
                <td className="px-3 py-2">
                  <div className="h-1.5 w-full max-w-[80px] mx-auto rounded-full bg-muted overflow-hidden">
                    <motion.div
                      className="h-full rounded-full bg-vaea-teal-500"
                      initial={{ width: 0 }}
                      animate={{ width: isInView ? "100%" : 0 }}
                      transition={{ duration: 0.6, delay: i * 0.05 }}
                    />
                  </div>
                </td>
                <td className="px-3 py-2 text-center">
                  <StatusBadge status={epic.status} />
                </td>
                <td className="px-3 py-2 text-foreground/60">
                  {epic.highlight}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </motion.div>

      {/* Sprint Velocity Area Chart */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="rounded-xl border border-border p-4 bg-card"
      >
        <h3 className="text-sm font-bold mb-3 text-vaea-navy">
          Sprint Velocity
        </h3>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={velocityData} margin={{ left: -10 }}>
            <defs>
              <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3a8f8a" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#3a8f8a" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="sprint"
              fontSize={10}
              tick={{ fill: "#1e223588" }}
            />
            <YAxis fontSize={10} tick={{ fill: "#1e223588" }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Area
              type="monotone"
              dataKey="done"
              stroke="#3a8f8a"
              strokeWidth={2.5}
              fill="url(#areaGradient)"
              name="Completed"
              dot={{ fill: "#3a8f8a", r: 4 }}
              activeDot={{ r: 6, stroke: "#3a8f8a", strokeWidth: 2 }}
            />
            <Area
              type="monotone"
              dataKey="target"
              stroke="#d4614a"
              strokeWidth={1.5}
              strokeDasharray="6 3"
              fill="none"
              name="Target"
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Feature Coverage Radar Chart */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="rounded-xl border border-border p-4 bg-card"
      >
        <h3 className="text-sm font-bold mb-3 text-vaea-navy">
          Feature Coverage
        </h3>
        <ResponsiveContainer width="100%" height={280}>
          <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis
              dataKey="subject"
              fontSize={11}
              tick={{ fill: "#1e223588" }}
            />
            <PolarRadiusAxis
              angle={30}
              domain={[0, 100]}
              fontSize={9}
              tick={{ fill: "#1e223555" }}
            />
            <Radar
              name="Completion"
              dataKey="completion"
              stroke="#3a8f8a"
              fill="#3a8f8a"
              fillOpacity={0.25}
              strokeWidth={2}
            />
          </RadarChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  );
}
