"use client";

import { DemoSidebar } from "@/components/demo/DemoSidebar";
import { OverviewSection } from "@/components/demo/OverviewSection";
import { PipelineSection } from "@/components/demo/PipelineSection";
import { SpreadsheetSection } from "@/components/demo/SpreadsheetSection";
import { ChatSection } from "@/components/demo/ChatSection";
import { ExportSection } from "@/components/demo/ExportSection";
import { ProgressSection } from "@/components/demo/ProgressSection";
import { ArchitectureSection } from "@/components/demo/ArchitectureSection";
import { StakeholdersSection } from "@/components/demo/StakeholdersSection";

const sectionDividerClass =
  "border-t border-border/40 pt-12 mt-12 first:border-0 first:pt-0 first:mt-0";

export default function DemoPage() {
  return (
    <div className="flex min-h-screen bg-background">
      {/* Sticky sidebar — expandable on hover, hidden on mobile (tab bar shown instead) */}
      <DemoSidebar />

      {/* Main content — offset by collapsed sidebar width on desktop */}
      <main className="flex-1 lg:ml-14 overflow-y-auto">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">

          <section id="overview" className={sectionDividerClass}>
            <OverviewSection />
          </section>

          <section id="pipeline" className={sectionDividerClass}>
            <PipelineSection />
          </section>

          <section id="spreadsheet" className={sectionDividerClass}>
            <SpreadsheetSection />
          </section>

          <section id="chat" className={sectionDividerClass}>
            <ChatSection />
          </section>

          <section id="export" className={sectionDividerClass}>
            <ExportSection />
          </section>

          <section id="progress" className={sectionDividerClass}>
            <ProgressSection />
          </section>

          <section id="architecture" className={sectionDividerClass}>
            <ArchitectureSection />
          </section>

          <section id="stakeholders" className={sectionDividerClass}>
            <StakeholdersSection />
          </section>

          {/* Bottom spacer */}
          <div className="h-24" />
        </div>
      </main>
    </div>
  );
}
