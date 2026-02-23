import type { NextConfig } from "next";
import { createMDX } from 'fumadocs-mdx/next';

const withMDX = createMDX();

const nextConfig: NextConfig = {
  // Remote image patterns for Lottie CDN and other assets
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "assets*.lottiefiles.com" },
      { protocol: "https", hostname: "lottie.host" },
    ],
  },

  // Metadata defaults
  ...(process.env.VERCEL
    ? {}
    : { output: undefined }),
};

export default withMDX(nextConfig);
