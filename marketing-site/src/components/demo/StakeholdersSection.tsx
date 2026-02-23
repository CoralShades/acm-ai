"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle } from "lucide-react";
import { audienceData } from "@/lib/epic-data";
import { fadeUp, fadeIn } from "@/lib/animations";
import { useInView } from "@/hooks/useInView";
import { cn } from "@/lib/cn";

type Tab = keyof typeof audienceData;
const tabs = Object.keys(audienceData) as Tab[];

export function StakeholdersSection() {
  const [activeTab, setActiveTab] = useState<Tab>("Director");
  const { ref, isInView } = useInView({ threshold: 0.1 });
  const data = audienceData[activeTab];

  return (
    <div className="space-y-5" ref={ref}>
      {/* Header */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
      >
        <h2 className="text-xl font-bold text-vaea-navy">Value by Audience</h2>
        <p className="text-sm mt-1 text-foreground/50">
          How ACM-AI delivers value to every stakeholder
        </p>
      </motion.div>

      {/* Tab Bar */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        className="flex gap-1 p-1 rounded-xl bg-vaea-navy/6"
      >
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              "flex-1 py-2 rounded-lg text-sm font-semibold transition-all duration-200",
              activeTab === tab
                ? "bg-vaea-teal-300 text-white shadow-sm"
                : "text-vaea-navy/60 hover:text-vaea-navy hover:bg-white/50"
            )}
          >
            {tab}
          </button>
        ))}
      </motion.div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          variants={fadeIn}
          initial="hidden"
          animate="visible"
          exit={{ opacity: 0, transition: { duration: 0.15 } }}
          className="rounded-xl p-6 border border-border bg-card"
        >
          <h3 className="text-lg font-bold mb-4 text-vaea-navy">{data.headline}</h3>

          <div className="space-y-2">
            {data.cards.map((card, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.07, duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
                className="flex items-start gap-3 p-3 rounded-lg bg-vaea-teal-300/5"
              >
                <CheckCircle
                  size={16}
                  className="mt-0.5 shrink-0 text-vaea-teal-300"
                />
                <span className="text-sm text-vaea-navy">{card}</span>
              </motion.div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: data.cards.length * 0.07 + 0.1, duration: 0.3 }}
            className="mt-4 p-4 rounded-xl border-l-4 border-vaea-coral bg-vaea-coral/5"
          >
            <p className="text-sm font-semibold text-vaea-coral">{data.callout}</p>
          </motion.div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
