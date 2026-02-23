import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Product Roadmap",
  description:
    "ACM-AI development roadmap — completed epics, current milestones, and future extraction quality improvements.",
};

export default function RoadmapLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
