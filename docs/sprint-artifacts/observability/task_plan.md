# Observability Setup — Task Plan

## Status: PLANNING

---

## Phase 1: Immediate Fixes (No Observability Required)

- [ ] #96 — Fix `source.name` → `source.title` in backfill endpoint (one-line)
- [ ] #97 — Add `_apply_ollama_extraction_settings()` to correction LLM call (one-line)
- [ ] #91 — Fix `asyncio.run()` → `await` in sync upload path
- [ ] #92 — Persist model defaults to SurrealDB settings table

## Phase 2: Enable Observability Stack

- [x] Add Langfuse self-hosted to `docker-compose.observability.yml` (Postgres + Langfuse server)
- [ ] Set `LANGFUSE_ENABLED=true` + self-hosted URL in `.env` (user action — needs API keys)
- [ ] Set `LANGCHAIN_TRACING_V2=true` + LangSmith API key in `.env` (user action — dev only)
- [x] Register `supervisor` graph in `langgraph.json`
- [x] Wire Langfuse callbacks into: `chat.py`, `source_chat.py`, `transformations.py`, `sources.py`, `search.py`, `notes.py`
- [x] Add `langgraph-cli[inmem]` to dev dependencies
- [x] Update `.env.example` with observability documentation

## Phase 3: Use Observability to Fix Complex Issues

- [ ] #100 — room_name misalignment → LangSmith playground to iterate extraction prompt
- [ ] #99 — progress stuck running → Studio to find missing finalize path
- [ ] #94 — Anthropic Direct gap → Studio to debug provider selection
- [ ] #93 — Ollama hardening → LangSmith to test across models
- [ ] #84 — SF picklist mismatches → Studio (loop debug) + LangSmith (correction prompt) + Langfuse (regression)
- [ ] v3-continuation-sf-validation → All three tools for validate→correct loop fix
- [ ] PR#55 C1-C4 → Studio for state inspection of Qwen path bugs

## Phase 4: Production Readiness

- [ ] Disable LangSmith in production `.env`
- [ ] Verify Langfuse self-hosted captures all extraction traces
- [ ] Set up Langfuse scoring for extraction quality (SF compliance, record recall)
- [ ] Configure Langfuse cost alerts per provider
- [ ] Document observability runbook in `docs/development/`
