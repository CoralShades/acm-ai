"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { AnimatedCounter } from "@/components/AnimatedCounter";
import { projectStats } from "@/lib/sprint-data";
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

export function Hero() {
  return (
    <section
      className={cn(
        "relative min-h-screen overflow-hidden",
        "bg-vaea-navy flex flex-col justify-center"
      )}
    >
      {/* Grid overlay */}
      <div className="hero-grid absolute inset-0 pointer-events-none" />

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

          {/* Main headline */}
          <motion.h1
            variants={fadeUp}
            className={cn(
              "font-[family-name:var(--font-dm-serif)]",
              "text-4xl leading-tight text-white sm:text-5xl md:text-6xl lg:text-7xl",
              "max-w-4xl tracking-tight"
            )}
          >
            Asbestos Compliance{" "}
            <span className="text-vaea-teal-100">Intelligence</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            variants={fadeUp}
            className="mt-6 max-w-2xl text-lg leading-relaxed text-white/60 sm:text-xl"
          >
            Transform PDF registers into BAR-compliant data.{" "}
            <span className="font-semibold text-white/90">96% accuracy.</span>{" "}
            <span className="font-semibold text-vaea-teal-100">18 seconds.</span>
          </motion.p>

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
            >
              Open App
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
                  d="M14.25 9v6m-4.5 0V9M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
                />
              </svg>
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

          {/* Counter row */}
          <motion.div
            variants={fadeUp}
            className={cn(
              "mt-20 w-full rounded-2xl glass border border-white/10 px-6 py-8",
              "grid grid-cols-2 gap-8 sm:grid-cols-4"
            )}
          >
            <div className="flex flex-col items-center">
              <AnimatedCounter
                end={projectStats.storiesDelivered}
                label="Stories Delivered"
                className="text-center"
              />
            </div>
            <div className="flex flex-col items-center">
              <AnimatedCounter
                end={projectStats.epicsComplete}
                label="Epics Complete"
                className="text-center"
              />
            </div>
            <div className="flex flex-col items-center">
              <AnimatedCounter
                end={projectStats.commits}
                label="Commits"
                className="text-center"
              />
            </div>
            <div className="flex flex-col items-center">
              <AnimatedCounter
                end={projectStats.completionRate}
                suffix="%"
                label="Feature Complete"
                className="text-center"
              />
            </div>
          </motion.div>
        </motion.div>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-vaea-navy to-transparent pointer-events-none" />
    </section>
  );
}
