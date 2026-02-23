import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Executive Demo",
  description:
    "Interactive demo of ACM-AI's extraction pipeline, smart chat, BAR-compliant spreadsheet, and real-time project progress.",
};

export default function DemoLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
