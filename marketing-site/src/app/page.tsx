import { Hero } from "@/components/landing/Hero";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { PipelinePreview } from "@/components/landing/PipelinePreview";
import { StatsCounter } from "@/components/landing/StatsCounter";
import { StakeholderTabs } from "@/components/landing/StakeholderTabs";
import { LiveStatusStrip } from "@/components/landing/LiveStatusStrip";

export default function Home() {
  return (
    <>
      {/* 1. Hero — full-bleed navy with particle grid */}
      <Hero />

      {/* 2. Live Status Strip — infrastructure health */}
      <LiveStatusStrip />

      {/* 3. How It Works — 3-step card layout */}
      <HowItWorks />

      {/* 4. Pipeline Preview — 7-stage horizontal timeline */}
      <PipelinePreview />

      {/* 5. Stats Counter — 6 animated metric cards */}
      <StatsCounter />

      {/* 6. Stakeholder Tabs — audience-specific value props */}
      <StakeholderTabs />
    </>
  );
}
