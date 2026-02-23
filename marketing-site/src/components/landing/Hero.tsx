"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ExternalLink, ChevronDown } from "lucide-react";
import { useTypewriter } from "@/hooks/useTypewriter";
import { useCounter } from "@/hooks/useCounter";
import { useInView } from "@/hooks/useInView";
import { fadeUp, staggerContainer } from "@/lib/animations";
import { cn } from "@/lib/cn";
import { APP_URL } from "@/lib/site-urls";

const particles = [
  { top: "12%", left: "8%", size: 6, delay: "0s", duration: "6s" },
  { top: "25%", left: "88%", size: 4, delay: "1.2s", duration: "8s" },
  { top: "60%", left: "5%", size: 5, delay: "2.1s", duration: "7s" },
  { top: "72%", left: "92%", size: 3, delay: "0.8s", duration: "9s" },
  { top: "40%", left: "78%", size: 7, delay: "1.8s", duration: "6.5s" },
  { top: "85%", left: "20%", size: 4, delay: "3s", duration: "8.5s" },
  { top: "18%", left: "55%", size: 3, delay: "2.5s", duration: "7.5s" },
  { top: "50%", left: "45%", size: 5, delay: "0.4s", duration: "10s" },
];

const wordContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.06, delayChildren: 0 } },
};

const wordVariant = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.25, 0.1, 0.25, 1] as [number, number, number, number],
    },
  },
};

const STATS = [
  { end: 87, label: "Extraction Accuracy", suffix: "%" },
  { end: 47, label: "BAR Columns", suffix: "" },
  { end: 131, label: "Stories Shipped", suffix: "" },
  { end: 18, label: "Seconds Per PDF", suffix: "s" },
];

const heroGridStyle: React.CSSProperties = {
  backgroundImage: [
    "linear-gradient(rgba(58, 143, 138, 0.08) 1px, transparent 1px)",
    "linear-gradient(90deg, rgba(58, 143, 138, 0.08) 1px, transparent 1px)",
  ].join(", "),
  backgroundSize: "40px 40px",
  animation: "gridDrift 20s linear infinite",
};

const magneticProps = {
  onMouseMove(e: React.MouseEvent<HTMLAnchorElement>) {
    const r = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - r.left - r.width / 2) * 0.15;
    const y = (e.clientY - r.top - r.height / 2) * 0.15;
    e.currentTarget.style.transform = `translate(${x}px, ${y}px)`;
  },
  onMouseLeave(e: React.MouseEvent<HTMLAnchorElement>) {
    e.currentTarget.style.transform = "translate(0, 0)";
  },
  style: { transition: "transform 0.2s ease" } as React.CSSProperties,
};

const SUBTITLE =
  "ACM-AI converts Victorian Government SAMP/BAR PDF registers into " +
  "submission-ready spreadsheets using a 7-stage AI extraction pipeline.";

interface StatItemProps {
  end: number;
  label: string;
  suffix: string;
  enabled: boolean;
}

function StatItem({ end, label, suffix, enabled }: StatItemProps) {
  const count = useCounter({ end, duration: 2000, enabled });
  return (
    <div className="flex flex-col items-center gap-1">
      <span
        style={{
          fontFamily: "var(--font-dm-serif)",
          fontSize: "56px",
          color: "var(--vaea-teal-300)",
          lineHeight: 1,
        }}
      >
        {count}
        {suffix}
      </span>
      <span
        style={{
          fontFamily: "var(--font-dm-sans)",
          fontSize: "13px",
          color: "var(--muted-foreground)",
        }}
      >
        {label}
      </span>
    </div>
  );
}

export function Hero() {
  const { displayed, isComplete } = useTypewriter({
    text: SUBTITLE,
    speed: 30,
    delay: 1200,
    enabled: true,
  });

  const { ref: statsRef, isInView } = useInView({ threshold: 0.3, once: true });
  const [countersEnabled, setCountersEnabled] = useState([
    false,
    false,
    false,
    false,
  ]);

  useEffect(() => {
    if (!isInView) return;
    STATS.forEach((_, i) => {
      setTimeout(() => {
        setCountersEnabled((prev) => {
          const n = [...prev];
          n[i] = true;
          return n;
        });
      }, i * 150);
    });
  }, [isInView]);

  return (
    <section
      className={cn(
        "relative min-h-screen overflow-hidden",
        "bg-vaea-navy-light flex flex-col justify-center"
      )}
      style={heroGridStyle}
    >
      {/* Radial gradient glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 70% 50% at 50% 40%, rgba(83,166,157,0.12) 0%, transparent 70%)",
        }}
      />

      {/* Particle dots */}
      {particles.map((p, i) => (
        <span
          key={i}
          className="absolute rounded-full bg-vaea-teal-300 opacity-30 pointer-events-none"
          style={{
            top: p.top,
            left: p.left,
            width: p.size,
            height: p.size,
            animation: `float-particle ${p.duration} ease-in-out ${p.delay} infinite`,
          }}
        />
      ))}

      {/* Content */}
      <div className="relative z-10 mx-auto w-full max-w-7xl px-6 pt-32 pb-20 lg:px-8">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="flex flex-col items-center text-center"
        >
          {/* Eyebrow badge */}
          <motion.div variants={fadeUp} className="mb-6">
            <span
              className={cn(
                "inline-flex items-center gap-2 rounded-full px-4 py-1.5",
                "border border-vaea-teal-700 bg-vaea-teal-900/20",
                "text-xs font-medium tracking-widest uppercase text-vaea-teal-100"
              )}
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-vaea-teal-300 opacity-60" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-vaea-teal-300" />
              </span>
              Victorian Government · Asbestos Compliance
            </span>
          </motion.div>

          {/* Main headline — word-by-word stagger */}
          <motion.h1
            variants={wordContainer}
            initial="hidden"
            animate="visible"
            className="font-[family-name:var(--font-dm-serif)] text-[40px] lg:text-[72px] leading-[1.1] tracking-tight"
          >
            {/* Line 1 — white */}
            <span className="block">
              {["Asbestos", "Compliance,"].map((word, i) => (
                <motion.span
                  key={i}
                  variants={wordVariant}
                  style={{
                    display: "inline-block",
                    marginRight: "0.25em",
                    color: "white",
                  }}
                >
                  {word}
                </motion.span>
              ))}
            </span>
            {/* Line 2 — teal */}
            <span className="block">
              {["Reinvented", "with", "AI"].map((word, i) => (
                <motion.span
                  key={i}
                  variants={wordVariant}
                  style={{
                    display: "inline-block",
                    marginRight: "0.25em",
                    color: "#3a8f8a",
                  }}
                >
                  {word}
                </motion.span>
              ))}
            </span>
          </motion.h1>

          {/* Typewriter subtitle */}
          <p className="mt-6 font-[family-name:var(--font-dm-sans)] text-lg text-white/60 max-w-2xl">
            {displayed}
            {!isComplete && (
              <span className="typing-cursor" aria-hidden="true">
                |
              </span>
            )}
          </p>

          {/* CTA buttons */}
          <motion.div
            variants={fadeUp}
            className="mt-10 flex flex-col items-center gap-4 sm:flex-row"
          >
            <Link
              href={APP_URL}
              target="_blank"
              rel="noopener noreferrer"
              className={cn(
                "inline-flex items-center gap-2 rounded-lg px-8 py-3.5",
                "bg-vaea-coral text-white font-semibold text-sm tracking-wide",
                "shadow-lg shadow-vaea-coral/25 transition-all duration-200",
                "hover:brightness-110 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-vaea-coral/30",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-vaea-coral focus-visible:ring-offset-2 focus-visible:ring-offset-vaea-navy"
              )}
              {...magneticProps}
            >
              Open App
              <ExternalLink size={16} />
            </Link>

            <Link
              href="/docs"
              className={cn(
                "inline-flex items-center gap-2 rounded-lg px-8 py-3.5",
                "glass text-white/90 font-semibold text-sm tracking-wide",
                "border border-white/20 transition-all duration-200",
                "hover:bg-white/10 hover:-translate-y-0.5",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40 focus-visible:ring-offset-2 focus-visible:ring-offset-vaea-navy"
              )}
              {...magneticProps}
            >
              Read Docs
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25"
                />
              </svg>
            </Link>
          </motion.div>

          {/* Counter row — product metrics with staggered animation */}
          <div
            ref={statsRef}
            className={cn(
              "mt-20 w-full rounded-2xl glass border border-white/10 px-6 py-8",
              "grid grid-cols-2 gap-8 sm:grid-cols-4"
            )}
          >
            {STATS.map((stat, i) => (
              <StatItem
                key={stat.label}
                end={stat.end}
                label={stat.label}
                suffix={stat.suffix}
                enabled={countersEnabled[i]}
              />
            ))}
          </div>
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <button
        onClick={() =>
          document
            .getElementById("how-it-works")
            ?.scrollIntoView({ behavior: "smooth" })
        }
        aria-label="Scroll to How It Works"
        className="absolute bottom-8 left-1/2 -translate-x-1/2 p-2 rounded-full text-white/40 hover:text-white/80 transition-opacity duration-200"
        style={{ animation: "bounceY 1.5s ease-in-out infinite" }}
      >
        <ChevronDown size={24} />
      </button>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-vaea-navy-light to-transparent pointer-events-none" />
    </section>
  );
}
