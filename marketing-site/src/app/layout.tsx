import 'fumadocs-ui/style.css';
import type { Metadata } from "next";
import { DM_Sans, DM_Serif_Display, JetBrains_Mono } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { Navigation } from "@/components/Navigation";
import { Footer } from "@/components/Footer";
import "./globals.css";

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
  display: "swap",
});

const dmSerif = DM_Serif_Display({
  variable: "--font-dm-serif",
  weight: "400",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "ACM-AI | Asbestos Compliance Intelligence",
    template: "%s | ACM-AI",
  },
  description:
    "AI-powered asbestos compliance management for Victorian Government. Transform PDF registers into BAR-compliant data with 96% accuracy.",
  keywords: [
    "asbestos",
    "compliance",
    "BAR",
    "Victorian Government",
    "VAEA",
    "AI",
    "document intelligence",
  ],
  openGraph: {
    title: "ACM-AI | Asbestos Compliance Intelligence",
    description:
      "Transform PDF asbestos registers into Victorian Government BAR-compliant data with AI.",
    type: "website",
    locale: "en_AU",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${dmSans.variable} ${dmSerif.variable} ${jetbrainsMono.variable} antialiased`}
      >
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
          <Navigation />
          <main>{children}</main>
          <Footer />
        </ThemeProvider>
      </body>
    </html>
  );
}
