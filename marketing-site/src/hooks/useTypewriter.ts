"use client";

import { useEffect, useState } from "react";

interface UseTypewriterOptions {
  text: string;
  speed?: number;
  delay?: number;
  enabled?: boolean;
}

export function useTypewriter({
  text,
  speed = 30,
  delay = 0,
  enabled = true,
}: UseTypewriterOptions) {
  const [displayed, setDisplayed] = useState("");
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (!enabled) {
      setDisplayed("");
      setIsComplete(false);
      return;
    }

    setDisplayed("");
    setIsComplete(false);

    const timeout = setTimeout(() => {
      let i = 0;
      const interval = setInterval(() => {
        if (i < text.length) {
          setDisplayed(text.slice(0, i + 1));
          i++;
        } else {
          setIsComplete(true);
          clearInterval(interval);
        }
      }, speed);

      return () => clearInterval(interval);
    }, delay);

    return () => clearTimeout(timeout);
  }, [text, speed, delay, enabled]);

  return { displayed, isComplete };
}
