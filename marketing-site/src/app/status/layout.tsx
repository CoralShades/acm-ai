import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Infrastructure Status",
  description:
    "Live infrastructure health dashboard — GitHub, Vercel, Railway service status and project metrics.",
  keywords: ["ACM-AI", "status", "infrastructure", "health", "Victorian Government"],
  openGraph: {
    title: "ACM-AI Infrastructure Status",
    description:
      "Live infrastructure health dashboard for ACM-AI compliance platform.",
    type: "website",
    locale: "en_AU",
  },
};

export default function StatusLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
