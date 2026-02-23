"use client";

import { useEffect, useState } from "react";

interface UseCounterOptions {
  end: number;
  duration?: number;
  start?: number;
  enabled?: boolean;
}

export function useCounter({
  end,
  duration = 2000,
  start = 0,
  enabled = true,
}: UseCounterOptions) {
  const [count, setCount] = useState(start);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    let startTime: number | null = null;
    let raf: number;

    const step = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.round(start + (end - start) * eased));

      if (progress < 1) {
        raf = requestAnimationFrame(step);
      }
    };

    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [end, duration, start, enabled]);

  return count;
}
