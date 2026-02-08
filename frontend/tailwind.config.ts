import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      animation: {
        shimmer: 'shimmer 2s linear infinite',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      // VAEA color shortcuts for convenience
      colors: {
        vaea: {
          teal: {
            100: '#9AD9D9',
            300: '#53A69D',
            500: '#01A09C',
            700: '#2A5951',
            900: '#01706D',
          },
          green: {
            200: '#A9D9AC',
            500: '#95D60C',
          },
          coral: '#EB787A',
          gold: '#D4A843',
        },
      },
      // Font family mapped from CSS variables (Inter + JetBrains Mono)
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains)", "ui-monospace", "monospace"],
        data: ["var(--font-jetbrains)", "ui-monospace", "monospace"],
      },
      // Font Size tokens with line-height
      fontSize: {
        xs: ["var(--text-xs)", { lineHeight: "var(--leading-normal)" }],
        sm: ["var(--text-sm)", { lineHeight: "var(--leading-normal)" }],
        base: ["var(--text-base)", { lineHeight: "var(--leading-normal)" }],
        lg: ["var(--text-lg)", { lineHeight: "var(--leading-relaxed)" }],
        xl: ["var(--text-xl)", { lineHeight: "var(--leading-tight)" }],
        "2xl": ["var(--text-2xl)", { lineHeight: "var(--leading-tight)" }],
        "3xl": ["var(--text-3xl)", { lineHeight: "var(--leading-tight)" }],
        "4xl": ["var(--text-4xl)", { lineHeight: "var(--leading-tight)" }],
      },
      // Spacing tokens
      spacing: {
        "space-0": "var(--space-0)",
        "space-1": "var(--space-1)",
        "space-2": "var(--space-2)",
        "space-3": "var(--space-3)",
        "space-4": "var(--space-4)",
        "space-5": "var(--space-5)",
        "space-6": "var(--space-6)",
        "space-8": "var(--space-8)",
        "space-10": "var(--space-10)",
        "space-12": "var(--space-12)",
        "space-16": "var(--space-16)",
        "space-20": "var(--space-20)",
        "space-24": "var(--space-24)",
      },
      // Border Radius tokens
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
      },
      // Box Shadow tokens
      boxShadow: {
        xs: "var(--shadow-xs)",
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
        xl: "var(--shadow-xl)",
      },
      // Transition Duration tokens
      transitionDuration: {
        fast: "var(--duration-fast)",
        normal: "var(--duration-normal)",
        slow: "var(--duration-slow)",
      },
      // Z-Index tokens
      zIndex: {
        dropdown: "var(--z-dropdown)",
        sticky: "var(--z-sticky)",
        modal: "var(--z-modal)",
        popover: "var(--z-popover)",
        toast: "var(--z-toast)",
      },
      // Typography prose customization
      typography: {
        DEFAULT: {
          css: {
            "--tw-prose-body": "var(--foreground)",
            "--tw-prose-headings": "var(--foreground)",
            "--tw-prose-links": "var(--primary)",
            "--tw-prose-code": "var(--foreground)",
            maxWidth: "none",
          },
        },
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;