# ACM-AI Project Documentation

> **Project:** ACM-AI — Intelligent Asbestos Compliance Management
> **Status:** Active Development (v4.0)
> **Last Updated:** 2026-03-31
> **Epics:** 37 | **Stories:** 319 (289 done, 91%)

## Overview

**ACM-AI** is an intelligent Asbestos Containing Material (ACM) compliance management system powered by AI. It transforms ARA (Asbestos Register Assessment) and BAR (Building Asbestos Register) documents into structured, queryable data with Salesforce schema alignment, multi-provider extraction, and AI-powered chat.

## Documentation Structure

| Document | Description | Version | Last Updated |
|----------|-------------|---------|--------------|
| [System Analysis](./01-system-analysis.md) | Current architecture, tech stack, gap analysis | v4.0 | 2026-03-31 |
| [Product Brief](./02-product-brief.md) | Product vision, goals, user personas | v4.0 | 2026-03-31 |
| [PRD](./03-prd.md) | Detailed functional & non-functional requirements | v4.0 | 2026-03-31 |
| [Architecture](./04-architecture.md) | Technical architecture, data model, API design | v4.0 | 2026-03-31 |
| [Epics & Stories](./05-epics-and-stories.md) | All 37 epics, 319 stories with acceptance criteria | v4.0 | 2026-03-31 |
| [Extended Plan](./06-extended-plan.md) | Implementation timeline, milestones, delivery status | v4.0 | 2026-03-31 |

## Key Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| AI Framework | LangGraph + LangChain | Agent workflows, tool calling, state management |
| Chat Architecture | Unified LangGraph Agent (15 tools) | Replaced supervisor+CRUD dual-agent (2026-03-22) |
| Spreadsheet | AG Grid (Community) | Enterprise-grade, virtual scrolling, column grouping |
| Extraction Pipeline | Per-row LLM (V3.5) | 9 fields per call, num_ctx=2048, Ollama-compatible |
| Table Extraction | Docling Direct API (primary) | 100% accuracy on Broadmeadows benchmark |
| Schema Alignment | Salesforce Building__c + Item__c | Government compliance, Data Loader export |
| Multi-Format | Schema Inference + Format Profiles | Auto-detect consultant formats (3+ validated) |
| AI Providers | Ollama (local) → Anthropic → OpenRouter | Local-first, cloud fallback for truncation |
| Database | SurrealDB | Document + vector + graph in single DB |
| Observability | Langfuse (self-hosted) + LangSmith | Cost tracking, trace analysis, prompt iteration |
| Streaming | PipelineEventBus + SSE | Real-time extraction progress |
| Chat Persistence | AsyncSqliteSaver | Durable sessions across server restarts |

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, React 19, Radix UI, Tailwind CSS 4, AG Grid, Zustand, React Query |
| Backend | Python 3.11+, FastAPI, LangChain/LangGraph, Docling, MinerU 2.x |
| Database | SurrealDB (document + vector + graph) |
| AI | Ollama (local), Anthropic Claude, OpenRouter, CopilotKit + AG-UI |
| Observability | Langfuse (self-hosted), LangSmith (dev), LangGraph API (local) |
| Infrastructure | Docker Compose, uv (Python), npm (frontend) |

## Delivery Milestones

| Date | Milestone | Epic(s) |
|------|-----------|---------|
| 2025-12-07 | Project kickoff, initial planning | — |
| 2026-02-22 | Core MVP complete | E1-E17 |
| 2026-02-27 | MinerU extraction (90.3% accuracy) | E23 |
| 2026-02-28 | Docling Direct API (100% Broadmeadows) | E26 |
| 2026-03-05 | V3 complete (SF alignment, multi-provider) | E30-E35 |
| 2026-03-10 | V3.5 Per-Row Extraction (163 new tests) | E37 |
| 2026-03-18 | Multi-Consultant Format (3+ formats) | MCS |
| 2026-03-22 | Unified Chat (14 legacy files deleted) | UC |
| 2026-03-31 | Chat pipeline stabilized | Bug fixes |

## Quick Links

- **Sprint Status:** [docs/sprint-artifacts/sprint-status.yaml](../../docs/sprint-artifacts/sprint-status.yaml)
- **Architecture Docs:** [docs/architecture/](../../docs/architecture/)
- **Development Guide:** [docs/development/](../../docs/development/)
- **CLAUDE.md:** [CLAUDE.md](../../CLAUDE.md)

## Current Status (2026-03-31)

| Metric | Value |
|--------|-------|
| Epics Complete | 35/37 (E29 partial, E36 in-progress) |
| Stories Done | 289/319 (91%) |
| Stories In Progress | 1 (MCS11 E2E verification) |
| Stories Backlog | 3 (E36-S5, S6, S7) |
| Stories Archived | 16 |
| Backend Tests | 2477+ passing |
| Extraction Accuracy | 100% Broadmeadows (31/31), 84% Alexander (36/43) |
