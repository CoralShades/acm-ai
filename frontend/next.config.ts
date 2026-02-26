import type { NextConfig } from "next";
import path from "path";

const isDev = process.env.NODE_ENV === 'development';

const nextConfig: NextConfig = {
  // Externalize CopilotKit runtime dependencies to avoid webpack bundling issues
  serverExternalPackages: [
    "@copilotkit/runtime",
    "graphql",
    "graphql-scalars",
  ],

  // Enable standalone output for Docker deployment (skip for Vercel and dev)
  ...(!isDev && !process.env.VERCEL ? { output: "standalone" } : {}),

  // Set workspace root to parent directory to resolve multiple lockfile warning
  // Only apply for Docker standalone builds (skip for Vercel and dev)
  ...(!isDev && !process.env.VERCEL ? { outputFileTracingRoot: path.join(__dirname, '../') } : {}),

  // API Rewrites: Proxy /api/* requests to FastAPI backend
  async rewrites() {
    const internalApiUrl = process.env.INTERNAL_API_URL || 'http://localhost:5055'
    console.log(`[Next.js Rewrites] Proxying /api/* to ${internalApiUrl}/api/*`)

    return [
      {
        source: '/api/:path*',
        destination: `${internalApiUrl}/api/:path*`,
      },
    ]
  },

  webpack: (config) => {
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      'pdfjs-dist/build/pdf.mjs$': 'pdfjs-dist/legacy/build/pdf.mjs',
      'pdfjs-dist/build/pdf.worker.min.mjs$': 'pdfjs-dist/legacy/build/pdf.worker.min.mjs',
    }

    return config
  },
};

export default nextConfig;
