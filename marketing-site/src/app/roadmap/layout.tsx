import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Product Roadmap",
  description:
    "ACM-AI development roadmap — 19 completed epics, extraction quality milestones, and future plans.",
  keywords: ["ACM-AI", "roadmap", "epics", "milestones", "Victorian Government"],
  openGraph: {
    title: "ACM-AI Product Roadmap",
    description:
      "From first commit to feature-complete — 19 epics delivered in autonomous AI development.",
    type: "website",
    locale: "en_AU",
  },
};

export default function RoadmapLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
