import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Solution Architecture",
  description:
    "ACM-AI Solution Architecture v2.0 — the complete technical design of the AI-powered asbestos compliance platform: pipeline stages, infrastructure, data model, and accuracy journey.",
  keywords: [
    "ACM-AI",
    "architecture",
    "LangGraph",
    "pipeline",
    "SurrealDB",
    "Victorian Government",
    "asbestos compliance",
  ],
  openGraph: {
    title: "ACM-AI Solution Architecture v2.0",
    description:
      "Complete technical architecture: 7-stage AI extraction pipeline, hybrid PDF processing, 100% benchmark accuracy.",
    type: "website",
    locale: "en_AU",
  },
};

export default function ArchitectureLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
