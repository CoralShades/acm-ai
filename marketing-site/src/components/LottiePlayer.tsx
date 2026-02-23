"use client";

import dynamic from "next/dynamic";

const Lottie = dynamic(() => import("lottie-react"), { ssr: false });

interface LottiePlayerProps {
  animationData?: object;
  fallback?: React.ReactNode;
  className?: string;
  loop?: boolean;
  autoplay?: boolean;
}

export function LottiePlayer({
  animationData,
  fallback,
  className,
  loop = true,
  autoplay = true,
}: LottiePlayerProps) {
  if (!animationData) {
    return <>{fallback}</> || null;
  }

  return (
    <Lottie
      animationData={animationData}
      loop={loop}
      autoplay={autoplay}
      className={className}
    />
  );
}
