"use client";

import { cn } from "@/lib/cn";

type StatusLevel = "operational" | "degraded" | "down" | "unknown";

interface LiveStatusWidgetProps {
  label: string;
  status: StatusLevel;
  detail?: string;
  className?: string;
}

const statusConfig: Record<StatusLevel, { color: string; dot: string; text: string }> = {
  operational: { color: "bg-emerald-500", dot: "bg-emerald-400", text: "Operational" },
  degraded: { color: "bg-amber-500", dot: "bg-amber-400", text: "Degraded" },
  down: { color: "bg-red-500", dot: "bg-red-400", text: "Down" },
  unknown: { color: "bg-gray-400", dot: "bg-gray-300", text: "Unknown" },
};

export function LiveStatusWidget({ label, status, detail, className }: LiveStatusWidgetProps) {
  const config = statusConfig[status];

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span className="relative flex h-2.5 w-2.5">
        {status === "operational" && (
          <span
            className={cn(
              "absolute inline-flex h-full w-full animate-ping rounded-full opacity-75",
              config.dot
            )}
          />
        )}
        <span className={cn("relative inline-flex h-2.5 w-2.5 rounded-full", config.color)} />
      </span>
      <span className="text-xs font-medium text-white/80">{label}</span>
      {detail && (
        <span className="text-xs text-white/40">{detail}</span>
      )}
    </div>
  );
}
