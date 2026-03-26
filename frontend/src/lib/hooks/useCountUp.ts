'use client'
import { useState, useEffect } from 'react'

function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3)
}

export function useCountUp(target: number, duration = 600): number {
  const [current, setCurrent] = useState(0)
  useEffect(() => {
    if (target === 0) { setCurrent(0); return }
    const start = performance.now()
    let raf: number
    const step = (now: number) => {
      const progress = Math.min((now - start) / duration, 1)
      setCurrent(Math.round(target * easeOutCubic(progress)))
      if (progress < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [target, duration])
  return current
}
