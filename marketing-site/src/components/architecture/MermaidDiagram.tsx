"use client";

import { useEffect, useRef, useId } from "react";

interface MermaidDiagramProps {
  chart: string;
  className?: string;
}

let initialized = false;

export function MermaidDiagram({ chart, className }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rawId = useId();
  const safeId = "m" + rawId.replace(/[^a-zA-Z0-9]/g, "") + Date.now().toString(36);

  useEffect(() => {
    let cancelled = false;

    async function render() {
      const mermaid = (await import("mermaid")).default;

      if (!initialized) {
        mermaid.initialize({
          startOnLoad: false,
          theme: "neutral",
          themeVariables: {
            primaryColor: "#e0f2fe",
            primaryTextColor: "#0369a1",
            primaryBorderColor: "#7ed0cc",
            lineColor: "#868e96",
            secondaryColor: "#fce7f3",
            tertiaryColor: "#dcfce7",
            fontFamily: "DM Sans, system-ui, sans-serif",
            fontSize: "13px",
            nodeBorder: "#7ed0cc",
            clusterBkg: "#f0f9f8",
            clusterBorder: "#3a8f8a",
          },
          flowchart: {
            htmlLabels: true,
            curve: "basis",
            padding: 12,
          },
          sequence: {
            actorMargin: 30,
            messageMargin: 20,
            noteMargin: 8,
          },
        });
        initialized = true;
      }

      if (cancelled || !containerRef.current) return;

      try {
        const { svg } = await mermaid.render(safeId, chart);
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      } catch (e) {
        console.error("Mermaid render error:", e);
        if (containerRef.current) {
          containerRef.current.innerHTML =
            '<div class="text-sm text-muted-foreground p-4 italic">Diagram unavailable</div>';
        }
      }
    }

    render();
    return () => {
      cancelled = true;
    };
  }, [chart, safeId]);

  return (
    <div
      ref={containerRef}
      className={`flex justify-center overflow-x-auto min-h-[80px] ${className ?? ""}`}
    />
  );
}
