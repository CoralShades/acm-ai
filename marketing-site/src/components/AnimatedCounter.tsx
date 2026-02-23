"use client";

import { motion } from "framer-motion";
import { useInView } from "@/hooks/useInView";
import { useCounter } from "@/hooks/useCounter";

interface AnimatedCounterProps {
  end: number;
  suffix?: string;
  prefix?: string;
  label: string;
  duration?: number;
  className?: string;
}

export function AnimatedCounter({
  end,
  suffix = "",
  prefix = "",
  label,
  duration = 2000,
  className,
}: AnimatedCounterProps) {
  const { ref, isInView } = useInView({ threshold: 0.3 });
  const count = useCounter({ end, duration, enabled: isInView });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 16 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5 }}
      className={className}
    >
      <div className="font-[family-name:var(--font-dm-serif)] text-5xl tracking-tight text-foreground md:text-6xl">
        {prefix}
        {count}
        {suffix}
      </div>
      <div className="mt-2 text-sm font-medium text-muted-foreground">
        {label}
      </div>
    </motion.div>
  );
}
