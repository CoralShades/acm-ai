# ACM-AI Marketing Site

Public-facing marketing site, executive demo platform, documentation hub, and live infrastructure dashboard for the ACM-AI asbestos compliance intelligence system.

## Quick Start

```bash
cd marketing-site
npm install
npm run dev          # http://localhost:3000
```

For live infrastructure widgets, copy `.env.local.example` to `.env.local` and add API tokens (optional — site works without them using static fallbacks).

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Landing | Hero, How It Works, Pipeline Preview, Stats, Stakeholders, Live Status |
| `/demo` | Executive Demo | 8 interactive sections ported from demo artifact + sidebar nav |
| `/docs` | Documentation | Fumadocs MDX platform — PRD, Architecture, Epics, Guides |
| `/status` | Infrastructure | Live GitHub/Vercel/Railway health + project metrics |
| `/roadmap` | Product Roadmap | Phase timeline, milestones, future epics |

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | 16.1.6 |
| Docs | Fumadocs (fumadocs-ui + fumadocs-mdx) | 16.x / 14.x |
| Animation | Framer Motion | 12.x |
| Charts | Recharts | 3.x |
| UI | Radix UI (Tabs, Dialog, Tooltip) | latest |
| Icons | Lucide React | 0.575+ |
| Live data | SWR (60s refresh) | 2.x |
| GitHub API | @octokit/rest | 22.x |
| Styling | Tailwind CSS 4 | 4.x |
| Fonts | DM Serif Display, DM Sans, JetBrains Mono | Google Fonts |

## Relationship to Main App

This is a **separate Next.js application** inside the monorepo:

```
acm-ai-production/
  frontend/          ← Main ACM-AI application (port 8502)
  marketing-site/    ← This marketing site (port 3000, deploys to Vercel)
  api/               ← FastAPI backend (port 5055)
  ...
```

The marketing site does NOT share dependencies or build processes with the main app. It reads project documentation from `docs/` and `_bmad-output/` at build time for MDX content, but has no runtime dependency on the backend.

## Documentation

Detailed guides are in this directory:

- **[Managing Content](./managing-content.md)** — Update landing page data, demo sections, stats
- **[Adding Pages](./adding-pages.md)** — Create new routes, components, sections
- **[Fumadocs Guide](./fumadocs-guide.md)** — Add/edit MDX documentation pages
- **[API Connections](./api-connections.md)** — Configure live status widgets
- **[Deployment](./deployment.md)** — Vercel deployment, env vars, CI/CD
- **[Design System](./design-system.md)** — VAEA tokens, fonts, animations, component patterns

## Commands

```bash
npm run dev          # Development server with Turbopack
npm run build        # Production build (verifies compilation)
npm run lint         # ESLint
npm run start        # Serve production build locally
```
