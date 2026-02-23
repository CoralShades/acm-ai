# E19-S1: ACM-AI Marketing Site + Documentation Platform

## Story Info
- **Epic**: E19 — Marketing & Stakeholder Presentation
- **Status**: done
- **Priority**: P1
- **Size**: XL (Extra Large)
- **Created**: 2026-02-23
- **Dependencies**: None (standalone sub-project)
- **Blocks**: None

## Description

Build a public-facing marketing site, executive demo platform, documentation hub, and live infrastructure dashboard for ACM-AI. Deployed as a separate Next.js application inside the monorepo at `marketing-site/`, targeting Vercel deployment. The product is feature-complete (92%, 112/122 stories) and needs a polished presentation layer for stakeholder evaluation and adoption.

## Acceptance Criteria

- [x] Next.js 16 App Router project scaffolded at `marketing-site/`
- [x] VAEA design tokens ported from main frontend (teal, coral, navy, gold)
- [x] Google Fonts: DM Serif Display, DM Sans, JetBrains Mono
- [x] Landing page with 6 sections: Hero, HowItWorks, PipelinePreview, StatsCounter, StakeholderTabs, LiveStatusStrip
- [x] Demo page with 8 sections ported from `acm-ai-demo-webartifact.jsx`: Overview, Pipeline, Spreadsheet, Chat, Export, Progress, Architecture, Stakeholders
- [x] DemoSidebar with keyboard shortcuts (1-8) and IntersectionObserver active tracking
- [x] Typewriter streaming effect in Chat section
- [x] Framer Motion scroll-triggered animations throughout
- [x] 3 API routes: GitHub stats (Octokit), Vercel status, Railway status — all with graceful fallbacks
- [x] Fumadocs documentation platform with 11 MDX pages (PRD, Architecture, Epics, Guides)
- [x] Infrastructure Status dashboard page with SWR live data
- [x] Product Roadmap timeline page with phase cards
- [x] SEO: robots.txt, sitemap.xml, vercel.json, per-page metadata
- [x] `npm run build` passes with zero errors (21 routes)
- [x] `npm run lint` passes with zero errors

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `marketing-site/` (entire directory) | CREATE | ~60 files — full Next.js marketing site |
| `marketing-site/src/app/page.tsx` | CREATE | Landing page composition |
| `marketing-site/src/app/demo/page.tsx` | CREATE | Executive demo with 8 interactive sections |
| `marketing-site/src/app/status/page.tsx` | CREATE | Live infrastructure dashboard |
| `marketing-site/src/app/roadmap/page.tsx` | CREATE | Product roadmap timeline |
| `marketing-site/src/app/docs/` | CREATE | Fumadocs documentation platform |
| `marketing-site/src/app/api/` | CREATE | 3 API route handlers |
| `marketing-site/src/components/landing/` | CREATE | 6 landing section components |
| `marketing-site/src/components/demo/` | CREATE | 9 demo section components + sidebar |
| `marketing-site/src/content/docs/` | CREATE | 11 MDX documentation files |
| `marketing-site/src/hooks/` | CREATE | useInView, useCounter, useTypewriter |
| `marketing-site/src/lib/` | CREATE | animations, cn, source, sprint-data, epic-data |
| `marketing-site/vercel.json` | CREATE | Deployment config with security headers |
| `marketing-site/public/robots.txt` | CREATE | Search engine directives |
| `marketing-site/public/sitemap.xml` | CREATE | 15-page sitemap |

## Dev Agent Record
- **Completed**: 2026-02-23
- **Build**: PASS (Next.js 16.1.6, Turbopack, 2.7s compile, 21 routes)
- **Lint**: PASS (0 errors, 0 warnings)
- **Files verified**: All 60 source files confirmed present
- **Implementation approach**: 4-phase parallel agent execution
  - Phase 1: Foundation (scaffold, deps, tokens, utilities, layout)
  - Phase 2: 3 parallel agents (landing, demo, API routes)
  - Phase 3: 2 parallel agents (Fumadocs docs, status/roadmap pages)
  - Phase 4: QA (build, lint, SEO artifacts, metadata)

## Technical Notes

- Next.js 16.1.6 installed (plan said 15, but latest is 16 — backward compatible)
- Tailwind CSS 4 uses `@theme inline` in CSS instead of `tailwind.config.ts`
- Fumadocs v16 generates `.source/` directory at project root — needs `@/.source` tsconfig alias
- `toFumadocsSource()` required to preserve DocData types through the loader
- Fumadocs components require `RootProvider` from `fumadocs-ui/provider/next`
- All API routes return static fallback data when env tokens not configured
- `.source/**` added to ESLint globalIgnores (generated files)
