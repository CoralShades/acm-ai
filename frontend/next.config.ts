import type { NextConfig } from "next";
import path from "path";

const isDev = process.env.NODE_ENV === 'development';

const nextConfig: NextConfig = {
  // pdfjs-dist ESM needs loose externals resolution (react-pdf upgrade guide)
  experimental: {
    esmExternals: 'loose',
  },

  // Turbopack: set root to frontend dir to silence multiple-lockfile warning
  // (used when running `npm run dev:turbo` on systems where Turbopack works)
  turbopack: {
    root: __dirname,
  },

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

  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      // pdfjs-dist v5 ESM crashes with eval-* devtool (Next.js dev default).
      // cheap-module-source-map is the fastest non-eval option.
      config.devtool = 'cheap-module-source-map'
    }

    return config
  },
};

export default nextConfig;
