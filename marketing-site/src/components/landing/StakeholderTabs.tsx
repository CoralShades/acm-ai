"use client";

import { useState } from "react";
import * as Tabs from "@radix-ui/react-tabs";
import { motion, AnimatePresence } from "framer-motion";
import { useInView } from "@/hooks/useInView";
import { audienceData } from "@/lib/epic-data";
import { fadeUp } from "@/lib/animations";
import { cn } from "@/lib/cn";

const tabKeys = ["Director", "CTO", "CEO", "Client"] as const;
type TabKey = typeof tabKeys[number];

const tabLabels: Record<TabKey, string> = {
  Director: "Asset Director",
  CTO: "CTO",
  CEO: "CEO",
  Client: "End User",
};

export function StakeholderTabs() {
  const [activeTab, setActiveTab] = useState<TabKey>("Director");
  const { ref, isInView } = useInView({ threshold: 0.1 });

  const data = audienceData[activeTab];

  return (
    <section className="bg-vaea-navy py-24">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        {/* Section header */}
        <div className="mx-auto mb-14 max-w-2xl text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-vaea-teal-300">
            Built for Every Stakeholder
          </p>
          <h2 className="font-[family-name:var(--font-dm-serif)] text-3xl text-white sm:text-4xl">
            What ACM-AI Means for You
          </h2>
          <p className="mt-4 text-base leading-relaxed text-white/50">
            Select your role to see how ACM-AI delivers value across the
            Victorian Government compliance chain.
          </p>
        </div>

        <motion.div
          ref={ref}
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          variants={fadeUp}
        >
          <Tabs.Root
            value={activeTab}
            onValueChange={(v) => setActiveTab(v as TabKey)}
          >
            {/* Tab triggers */}
            <Tabs.List className="mb-10 flex flex-wrap items-center justify-center gap-3">
              {tabKeys.map((key) => (
                <Tabs.Trigger
                  key={key}
                  value={key}
                  className={cn(
                    "rounded-full px-5 py-2 text-sm font-medium transition-all duration-200",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-vaea-teal-300 focus-visible:ring-offset-2 focus-visible:ring-offset-vaea-navy",
                    "data-[state=active]:bg-vaea-teal-500 data-[state=active]:text-white data-[state=active]:shadow-lg",
                    "data-[state=inactive]:border data-[state=inactive]:border-white/20 data-[state=inactive]:text-white/60",
                    "data-[state=inactive]:hover:border-white/40 data-[state=inactive]:hover:text-white/90"
                  )}
                >
                  {tabLabels[key]}
                </Tabs.Trigger>
              ))}
            </Tabs.List>

            {/* Tab content */}
            {tabKeys.map((key) => (
              <Tabs.Content key={key} value={key} forceMount asChild>
                <div hidden={key !== activeTab}>
                  <AnimatePresence mode="wait">
                    {key === activeTab && (
                      <motion.div
                        key={key}
                        initial={{ opacity: 0, y: 16 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -8 }}
                        transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
                        className="grid gap-6 lg:grid-cols-3"
                      >
                        {/* Left column: headline + cards */}
                        <div className="lg:col-span-2 flex flex-col gap-5">
                          <h3 className="font-[family-name:var(--font-dm-serif)] text-2xl text-white">
                            {data.headline}
                          </h3>

                          <div className="grid gap-3 sm:grid-cols-2">
                            {data.cards.map((card, i) => {
                              const [head, ...rest] = card.split(":");
                              const hasColon = card.includes(":");
                              return (
                                <div
                                  key={i}
                                  className={cn(
                                    "glass rounded-xl border border-white/10 p-4",
                                    "flex items-start gap-3 transition-colors duration-200 hover:bg-white/10"
                                  )}
                                >
                                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-vaea-teal-500/30">
                                    <svg
                                      className="h-3 w-3 text-vaea-teal-300"
                                      fill="none"
                                      viewBox="0 0 24 24"
                                      stroke="currentColor"
                                      strokeWidth={3}
                                    >
                                      <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        d="m4.5 12.75 6 6 9-13.5"
                                      />
                                    </svg>
                                  </span>
                                  <p className="text-sm leading-relaxed text-white/70">
                                    {hasColon ? (
                                      <>
                                        <span className="font-semibold text-white/90">
                                          {head}:
                                        </span>
                                        {rest.join(":")}
                                      </>
                                    ) : (
                                      card
                                    )}
                                  </p>
                                </div>
                              );
                            })}
                          </div>
                        </div>

                        {/* Right column: callout box */}
                        <div className="flex flex-col">
                          <div
                            className={cn(
                              "flex-1 rounded-2xl p-6",
                              "border border-vaea-coral/40 bg-vaea-coral/5",
                              "flex flex-col justify-between gap-6"
                            )}
                          >
                            <div>
                              <span className="mb-3 inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-widest text-vaea-coral">
                                <svg
                                  className="h-3 w-3"
                                  fill="currentColor"
                                  viewBox="0 0 20 20"
                                >
                                  <path
                                    fillRule="evenodd"
                                    d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Zm-7-4a1 1 0 1 1-2 0 1 1 0 0 1 2 0ZM9 9a.75.75 0 0 0 0 1.5h.253a.25.25 0 0 1 .244.304l-.459 2.066A1.75 1.75 0 0 0 10.747 15H11a.75.75 0 0 0 0-1.5h-.253a.25.25 0 0 1-.244-.304l.459-2.066A1.75 1.75 0 0 0 9.253 9H9Z"
                                    clipRule="evenodd"
                                  />
                                </svg>
                                Key Insight
                              </span>
                              <p className="font-[family-name:var(--font-dm-serif)] text-lg leading-snug text-white">
                                {data.callout}
                              </p>
                            </div>

                            {/* Role tag */}
                            <div className="flex items-center gap-2">
                              <span className="rounded-full bg-vaea-coral/20 px-3 py-1 text-xs font-semibold text-vaea-coral">
                                {tabLabels[key]}
                              </span>
                              <span className="text-xs text-white/30">perspective</span>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </Tabs.Content>
            ))}
          </Tabs.Root>
        </motion.div>
      </div>
    </section>
  );
}
