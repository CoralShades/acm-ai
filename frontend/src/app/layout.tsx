import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";
import { ConnectionGuard } from "@/components/common/ConnectionGuard";
import { themeScript } from "@/lib/theme-script";
import { BRANDING } from "@/config/branding";

// Font CSS variables are defined in globals.css via @font-face or system font fallbacks.
// Google Fonts are loaded via a <link> tag at runtime to avoid build-time network dependency.

export const metadata: Metadata = {
  title: {
    default: BRANDING.name,
    template: `%s | ${BRANDING.name}`,
  },
  description: BRANDING.description,
  keywords: [...BRANDING.keywords],
  icons: {
    icon: [
      { url: '/acm-icon.svg', type: 'image/svg+xml' },
    ],
    apple: '/acm-icon.svg',
  },
  manifest: '/manifest.json',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        {/* Load Inter + JetBrains Mono at runtime (avoids next/font/google build-time network fetch) */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        {/* eslint-disable-next-line @next/next/no-page-custom-font */}
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&family=JetBrains+Mono:wght@100..800&display=swap"
        />
      </head>
      <body className="font-sans antialiased">
        <a href="#main-content" className="skip-to-content">
          Skip to main content
        </a>
        <ErrorBoundary>
          <ThemeProvider>
            <QueryProvider>
              <ConnectionGuard>
                {children}
                <Toaster />
              </ConnectionGuard>
            </QueryProvider>
          </ThemeProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
