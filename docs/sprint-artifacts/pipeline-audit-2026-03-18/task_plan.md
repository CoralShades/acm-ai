# Pipeline Audit & UX Fix — Task Plan
**Date:** 2026-03-18
**Branch:** ACMV3
**Goal:** Audit, plan, and create prompt packs for 4 problem areas

## Area 1: Extraction Pipeline Workflow & Execution
- [x] Map current 9-stage pipeline flow and identify fragile points
- [x] Document Bug Fix 12 N1-N9 unresolved issues
- [x] Identify provider routing failure modes (Ollama/Anthropic/OpenRouter)
- [ ] **SESSION:** Trace-driven pipeline audit (Langfuse + LangSmith)
- [ ] **SESSION:** Fix Bug Fix 12 N1-N9 issues
- [ ] **SESSION:** Pipeline resilience hardening (retry, fallback, idempotency)

## Area 2: Pipeline Agent Prompts Quality
- [x] Inventory all Jinja2 prompt templates in prompts/acm/
- [x] Document current ground truth baselines (Broadmeadows, Alexander)
- [ ] **SESSION:** Prompt evaluation framework setup (eval-audit skill)
- [ ] **SESSION:** Systematic prompt improvement with ground truth scoring
- [ ] **SESSION:** Ollama-specific prompt optimization (format=json compliance)

## Area 3: Multi-Consultant Format Adaptability
- [x] Document current consultant-specific hardcoding (COLUMN_ALIASES, ARA regex, SAMP patterns)
- [x] Gap analysis: what's missing for arbitrary PDF formats
- [ ] **SESSION:** Design dynamic schema inference architecture
- [ ] **SESSION:** Implement consultant format auto-detection
- [ ] **SESSION:** Template-free extraction with SF field mapping

## Area 4: Frontend/Backend Sync — Live Extraction UX
- [x] Audit SSE infrastructure (PipelineEventBus, endpoints, Zustand store)
- [x] Document broken/disconnected UI components
- [x] Identify job lifecycle management gaps (stop/restart/duplicate prevention)
- [ ] **SESSION:** Fix SSE streaming and extraction progress display
- [ ] **SESSION:** Add job lifecycle controls (stop, restart, duplicate guard)
- [ ] **SESSION:** Live extracted records view (ChatGPT-style tool use display)
- [ ] **SESSION:** Fix CopilotKit/AG-UI BUG-4 (HITL flow)

## Cross-Cutting
- [x] Sprint status analysis (E30+ focus)
- [x] Skill discovery and recommendation (15 skills identified)
- [ ] Generate prompt packs for each area
