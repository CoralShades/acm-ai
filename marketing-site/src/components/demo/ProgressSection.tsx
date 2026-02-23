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
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { epics } from "@/lib/epic-data";
import { velocityData, projectStats } from "@/lib/sprint-data";
import { fadeUp, staggerContainer } from "@/lib/animations";
import { useInView } from "@/hooks/useInView";
import { cn } from "@/lib/cn";

// Build bar chart data from epics
const epicChartData = epics.map((e) => ({
  epic: e.id,
  stories: e.stories,
}));

const statCards = [
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
];

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
        <h2 className="text-xl font-bold text-vaea-navy">Project Delivery Dashboard</h2>
        <p className="text-sm mt-1 text-foreground/50">
          ACM-AI v1.0 — Feature Complete as of {projectStats.featureComplete}
        </p>
      </motion.div>

      {/* Stat Cards */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
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
              <div className="text-2xl font-bold tracking-tight text-foreground">{card.value}</div>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Stories per Epic Bar Chart */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="rounded-xl border border-border p-4 bg-card"
      >
        <h3 className="text-sm font-bold mb-3 text-vaea-navy">Stories per Epic</h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={epicChartData} margin={{ bottom: 60, left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="epic"
              angle={-40}
              textAnchor="end"
              fontSize={10}
              tick={{ fill: "#1e2235" + "88" }}
              interval={0}
            />
            <YAxis fontSize={10} tick={{ fill: "#1e2235" + "88" }} />
            <Tooltip
              contentStyle={{
                borderRadius: 8,
                border: "1px solid #eee",
                fontSize: 12,
              }}
            />
            <Bar dataKey="stories" fill="#53A69D" radius={[4, 4, 0, 0]} name="Stories" />
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Epic Table */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="rounded-xl border border-border overflow-hidden bg-card"
      >
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-vaea-navy/5">
              <th className="px-3 py-2 text-left font-bold text-vaea-navy">Epic</th>
              <th className="px-3 py-2 text-left font-bold text-vaea-navy">Title</th>
              <th className="px-3 py-2 text-center font-bold text-vaea-navy">Stories</th>
              <th className="px-3 py-2 text-center font-bold text-vaea-navy">Status</th>
              <th className="px-3 py-2 text-left font-bold text-vaea-navy">Key Achievement</th>
            </tr>
          </thead>
          <tbody>
            {epics.map((epic, i) => (
              <tr key={i} className="border-t border-border/50">
                <td className="px-3 py-2 font-[family-name:var(--font-jetbrains-mono)] font-semibold text-vaea-teal-300">
                  {epic.id}
                </td>
                <td className="px-3 py-2 text-vaea-navy">{epic.title}</td>
                <td className="px-3 py-2 text-center font-bold text-vaea-navy">{epic.stories}</td>
                <td className="px-3 py-2 text-center">
                  <StatusBadge status={epic.status} />
                </td>
                <td className="px-3 py-2 text-foreground/60">{epic.highlight}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </motion.div>

      {/* Sprint Velocity Line Chart */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="rounded-xl border border-border p-4 bg-card"
      >
        <h3 className="text-sm font-bold mb-3 text-vaea-navy">Sprint Velocity</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={velocityData} margin={{ left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="sprint" fontSize={10} tick={{ fill: "#1e2235" + "88" }} />
            <YAxis fontSize={10} tick={{ fill: "#1e2235" + "88" }} />
            <Tooltip
              contentStyle={{
                borderRadius: 8,
                border: "1px solid #eee",
                fontSize: 12,
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="done"
              stroke="#53A69D"
              strokeWidth={2.5}
              name="Completed"
              dot={{ fill: "#53A69D" }}
            />
            <Line
              type="monotone"
              dataKey="target"
              stroke="#EB787A"
              strokeWidth={1.5}
              strokeDasharray="6 3"
              name="Target"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  );
}
