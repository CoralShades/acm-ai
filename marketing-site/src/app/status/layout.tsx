import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Infrastructure Status",
  description:
    "Live infrastructure health dashboard — GitHub, Vercel, Railway service status and project metrics.",
};

export default function StatusLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
