"use client";

import useSWR from "swr";
import { LiveStatusWidget } from "@/components/LiveStatusWidget";
import { cn } from "@/lib/cn";

type StatusLevel = "operational" | "degraded" | "down" | "unknown";

interface ServiceStatus {
  status: StatusLevel;
  detail?: string;
}

const fetcher = (url: string) =>
  fetch(url)
    .then((r) => {
      if (!r.ok) throw new Error("fetch failed");
      return r.json();
    })
    .catch(() => ({ status: "unknown" } as ServiceStatus));

function SkeletonStatus() {
  return (
    <div className="flex items-center gap-2 animate-pulse">
      <span className="h-2.5 w-2.5 rounded-full bg-white/20" />
      <span className="h-3 w-16 rounded bg-white/10" />
    </div>
  );
}

function useLastChecked(isValidating: boolean) {
  if (isValidating) return "checking…";
  const now = new Date();
  return `${now.toLocaleTimeString("en-AU", { hour: "2-digit", minute: "2-digit" })}`;
}

export function LiveStatusStrip() {
  const { data: github, isLoading: ghLoading, isValidating: ghValidating } = useSWR<ServiceStatus>(
    "/api/github/stats",
    fetcher,
    { refreshInterval: 60_000, fallbackData: { status: "unknown" } }
  );

  const { data: vercel, isLoading: vcLoading, isValidating: vcValidating } = useSWR<ServiceStatus>(
    "/api/vercel/status",
    fetcher,
    { refreshInterval: 60_000, fallbackData: { status: "unknown" } }
  );

  const { data: railway, isLoading: rlLoading, isValidating: rlValidating } = useSWR<ServiceStatus>(
    "/api/railway/status",
    fetcher,
    { refreshInterval: 60_000, fallbackData: { status: "unknown" } }
  );

  const lastChecked = useLastChecked(ghValidating || vcValidating || rlValidating);

  return (
    <div
      className={cn(
        "w-full bg-vaea-navy border-y border-white/10",
        "py-3 px-6"
      )}
    >
      <div className="mx-auto flex max-w-7xl flex-col items-center gap-4 sm:flex-row sm:justify-between">
        {/* Label */}
        <span className="text-xs font-semibold uppercase tracking-widest text-white/30">
          Infrastructure Status
        </span>

        {/* Status widgets */}
        <div className="flex flex-wrap items-center justify-center gap-6">
          {ghLoading ? (
            <SkeletonStatus />
          ) : (
            <LiveStatusWidget
              label="GitHub"
              status={github?.status ?? "unknown"}
              detail={github?.detail}
            />
          )}

          <span className="h-3 w-px bg-white/10" aria-hidden />

          {vcLoading ? (
            <SkeletonStatus />
          ) : (
            <LiveStatusWidget
              label="Vercel"
              status={vercel?.status ?? "unknown"}
              detail={vercel?.detail}
            />
          )}

          <span className="h-3 w-px bg-white/10" aria-hidden />

          {rlLoading ? (
            <SkeletonStatus />
          ) : (
            <LiveStatusWidget
              label="Railway"
              status={railway?.status ?? "unknown"}
              detail={railway?.detail}
            />
          )}
        </div>

        {/* Last checked */}
        <span className="text-xs text-white/25">
          Last checked: {lastChecked}
        </span>
      </div>
    </div>
  );
}
