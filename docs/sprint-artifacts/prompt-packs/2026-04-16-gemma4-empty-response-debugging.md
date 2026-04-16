# Session: Systematic debugging of gemma4:31b empty response root cause on LOCAL RTX 4090

## Skills to Load

/superpowers:systematic-debugging — Iron Law: NO FIXES until root cause confirmed
/planning-with-files — persistent markdown plan for session continuity (task_plan.md, findings.md, progress.md already exist)
/superpowers:verification-before-completion — verify work before claiming done

---

## Prerequisites

Before starting this session, verify:

- SurrealDB running: `docker ps | grep acm-ai-db` (should show healthy on port 8000)
- Ollama Docker running: `docker ps | grep acm-ai-ollama`
- gemma4:31b available: `docker exec acm-ai-ollama ollama list | grep gemma4:31b` (pull if missing: `docker exec acm-ai-ollama ollama pull gemma4:31b`)
- Ollama port mapped: verify Ollama API reachable at `curl http://localhost:11434/api/tags` (if not, restart container with port mapping: check docker-compose.yml for `11434:11434`)
- Langfuse stack running: `docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d` then verify `curl http://localhost:3000/api/public/health`
- If Langfuse is first start: visit http://localhost:3000, create account, get API keys, update `.env` with `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL=http://localhost:3000`
- LangSmith configured: verify `.env` has `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` set
- Branch: `git checkout main` (all fixes merged at commit 44d93b33)
- Planning files exist: `task_plan.md`, `findings.md`, `progress.md` in repo root

---

## Project Glossary

| Term | Definition |
|------|-----------|
| gemma4:31b | Google Gemma 4 31B parameter model (Q4_K_M quantization). Primary extraction model. Produces 0 tokens for ~50% of rows on Alexander document. |
| Per-row extraction | ACM pipeline mode where each table row is sent individually to the LLM for structured JSON extraction. Mode: `ACM_ITEM_EXTRACTION_MODE=per_row` |
| GBNF grammar | Grammar-Based Nondeterministic Finite automaton — Ollama's internal grammar format compiled from JSON schema. Controls token generation. |
| Empty response | When Ollama returns HTTP 200 but the model generates 0 content tokens. Prompt is processed (~22-28s) but no output produced. |
| RawTableRow | Dataclass containing a single row's cell data, column mappings, current_level, and extraction_notes. Input to `extract_single_row()`. |
| ChatOllama | LangChain's Ollama chat model wrapper. `format` param accepts `"json"`, `dict` (JSON schema), or `None`. Frozen Pydantic model. |
| RC-10c | Current fix: minimal JSON schema (625 chars) passed to Ollama `format` param. Reduces failures on Broadmeadows (29%→18%) but catastrophic on Alexander (~87%). |
| ExtractionState | LangGraph TypedDict carrying all pipeline data between nodes. |
| Docling tables | Structured table objects from Docling's DoclingDocument parser; primary extraction input. |
| Skill | Markdown instruction set for Claude Code activated via `/skill-name`. |
| Subagent | Claude Code session spawned via Task tool for parallel work. |
| Plan mode | Session reads/writes `task_plan.md` to maintain state across sessions. |
| Context7 MCP | MCP server for fetching live library docs. Use for Ollama, LangChain, Pydantic. |

---

## Current State

- **Branch:** main (commit 44d93b33 — all RC-1 through RC-10f fixes merged)
- **RunPod status:** Production/UAT on `deploy/runpod-5090` branch — DO NOT TOUCH
- **Broadmeadows:** 36/31 records (over-extraction via duplicates, 18% per-row failure)
- **Alexander:** ~50% per-row failure rate — temperature tuning exhausted (0, 0.3, 0.7 all identical)
- **Root cause status:** UNKNOWN — systematic debugging Phase 1 (evidence gathering) started but not completed
- **Evidence gathered so far:**
  - Ollama logs show prompt truncation warnings (53K→32K) for large documents
  - `OLLAMA_NUM_PARALLEL=2` on RunPod (concurrent request handling)
  - Same rows fail consistently regardless of temperature or grammar mode
  - HTTP 200 returned even for 0-token responses
  - 22-28s processing time even for empty responses (prompt processing on 31B)
- **Evidence NOT gathered (the 4 steps for this session):**
  - 1a: Actual content of failing vs succeeding rows — NEVER EXAMINED
  - 1c: Raw Ollama API test bypassing LangChain — NOT DONE
  - 1d: Ollama GBNF + gemma4 known issues research — NOT DONE
- **Local Ollama:** Has 14 models but may not have gemma4:31b yet (pull was initiated)
- **Langfuse:** NOT running locally — docker-compose.observability.yml exists but hasn't been started

---

## Key Files

**Read (reference — understand the extraction pipeline):**
- `/mnt/d/ailocal/acm-ai/open_notebook/extractors/row_extractor.py` — per-row LLM extraction, `extract_single_row()` at line 130, `build_kv_prompt()` at line 45
- `/mnt/d/ailocal/acm-ai/open_notebook/graphs/acm_extraction.py` — main LangGraph graph, `extract_items_node` at line 1084
- `/mnt/d/ailocal/acm-ai/open_notebook/extractors/row_segmenter.py` — deterministic row parser
- `/mnt/d/ailocal/acm-ai/prompts/acm/row_extraction.jinja` — system prompt template (34 lines, 16 JSON fields)
- `/mnt/d/ailocal/acm-ai/open_notebook/graphs/utils.py` — `_apply_ollama_extraction_settings()`, `_inject_response_format()`

**Read (planning state):**
- `/mnt/d/ailocal/acm-ai/task_plan.md` — phase tracker with Phase 3b (systematic debugging)
- `/mnt/d/ailocal/acm-ai/findings.md` — all root causes RC-1 through RC-11
- `/mnt/d/ailocal/acm-ai/progress.md` — run comparison table, session logs

**Read (observability setup):**
- `/mnt/d/ailocal/acm-ai/docker-compose.observability.yml` — Langfuse v3 stack (Postgres + ClickHouse + Redis + MinIO + Web + Worker)
- `/mnt/d/ailocal/acm-ai/.env` — Langfuse keys, LangSmith keys, extraction settings

**Modify (only after root cause confirmed):**
- `/mnt/d/ailocal/acm-ai/open_notebook/extractors/row_extractor.py` — fix location TBD
- `/mnt/d/ailocal/acm-ai/open_notebook/graphs/acm_extraction.py` — fix location TBD

---

## Plan

Read `task_plan.md` before starting. Update it as you work.

### Task Plan Reference
- task_plan.md: `/mnt/d/ailocal/acm-ai/task_plan.md`
- findings.md: `/mnt/d/ailocal/acm-ai/findings.md`
- progress.md: `/mnt/d/ailocal/acm-ai/progress.md`

### Execution Steps

**Step 0: Local Environment Setup** (do first, before any investigation)
1. Start Langfuse: `docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d`
2. Verify Langfuse health: `curl http://localhost:3000/api/public/health`
3. If first start: create account at http://localhost:3000, get keys, update `.env`
4. Verify gemma4:31b is available: `docker exec acm-ai-ollama ollama list | grep gemma4:31b`
5. If missing: `docker exec acm-ai-ollama ollama pull gemma4:31b` (wait for completion)
6. Verify Ollama API accessible: `curl http://localhost:11434/api/tags`
7. Start API: `uv run run_api.py` (PowerShell on Windows, NOT WSL)
8. Start worker: `uv run run_worker.py --import-modules commands` (PowerShell)
9. Verify API health: `curl http://localhost:5055/health`

**Step 1a: Compare failing vs succeeding row content**
- Run Alexander extraction locally with Langfuse tracing enabled
- After extraction, query SurrealDB for the extraction records with confidence levels
- From Langfuse traces, extract the EXACT prompt content for 3 failing rows and 3 succeeding rows
- Compare: row length, cell count, special characters, content complexity, column names
- Document pattern in findings.md

**Step 1c: Test raw Ollama API bypassing LangChain**
- Take a known-failing row's prompt content from Step 1a
- Send it directly to Ollama via curl:
  ```bash
  curl http://localhost:11434/api/chat -d '{
    "model": "gemma4:31b",
    "messages": [{"role": "system", "content": "<system prompt>"}, {"role": "user", "content": "<row content>"}],
    "format": <minimal_schema>,
    "stream": false,
    "options": {"temperature": 0, "num_ctx": 2048}
  }'
  ```
- Test with: (a) format=schema + temp=0, (b) format="json" + temp=0, (c) no format + temp=0, (d) no format + temp=0.3
- If raw API succeeds where LangChain fails → LangChain is the issue
- If raw API also fails → model/grammar is the issue
- Document in findings.md

**Step 1d: Research Ollama GBNF + gemma4 known issues**
- Use context7 MCP: `resolve-library-id` for "ollama" → `query-docs` for "grammar format json schema empty response"
- Search Ollama GitHub issues for "gemma4 empty response", "0 tokens", "grammar deadlock"
- Search for known gemma4 + structured output incompatibilities
- Document in findings.md

**Step 2: Synthesize evidence and form hypothesis**
- After all 3 evidence steps: read findings.md
- Identify the common pattern across failing rows
- Form a SINGLE testable hypothesis: "X causes Y because Z"
- Write hypothesis in task_plan.md Phase 3b

**Step 3: Test minimal fix**
- ONLY after hypothesis is formed
- Make the SMALLEST possible code change
- Test against 3 known-failing rows
- If it works: run full Alexander extraction
- If not: return to Step 2 with new hypothesis

---

## Agent Strategy

Strategy: SOLO
Run all steps sequentially in a single Claude Code session.
No subagents needed — this is a debugging investigation requiring context continuity.

**CRITICAL CONSTRAINT:** Follow the Systematic Debugging Iron Law:
- Phase 1 (evidence gathering) MUST complete before ANY fix is proposed
- If you catch yourself wanting to "just try" something — STOP, return to evidence gathering
- The goal of this session is UNDERSTANDING, not fixing

---

## Context7 Directives

Run these at session start to load current library documentation:

1. resolve-library-id for "ollama" → query-docs for "format json schema grammar structured output"
2. resolve-library-id for "langchain" → query-docs for "ChatOllama format temperature structured output"
3. resolve-library-id for "pydantic" → query-docs for "model_json_schema json schema generation"

---

## Verification Checklist

Before marking Phase 1 complete:

- [ ] Step 1a complete: At least 3 failing + 3 succeeding rows compared, pattern documented in findings.md
- [ ] Step 1c complete: Raw Ollama API tested with 4 format/temperature combinations, results documented
- [ ] Step 1d complete: Ollama + gemma4 known issues researched via context7, results documented
- [ ] Hypothesis formed: Single testable hypothesis written in task_plan.md
- [ ] No premature fixes: Zero code changes made before hypothesis confirmation
- [ ] Planning files updated: task_plan.md, progress.md, findings.md all reflect current state
- [ ] `uv run ruff check .` — Python lint (0 errors, only if code was modified)
- [ ] `uv run pytest tests/ -x` — Backend tests (all pass, only if code was modified)

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| READ | 8 | row_extractor.py, acm_extraction.py, row_segmenter.py, row_extraction.jinja, utils.py, task_plan.md, findings.md, progress.md |
| MODIFY | 3 | task_plan.md, findings.md, progress.md (planning updates only) |
| NEW | 0 | — |
| CODE MODIFY | 0 | — (no code changes until Phase 3) |

---

## Commit Template

When Phase 1 evidence gathering is complete (no code changes, only docs):

```
docs(audit): systematic debugging Phase 1 — gemma4:31b empty response evidence

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

When Phase 3 fix is applied:

```
fix(extraction): <root cause description> — gemma4:31b per-row empty response

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```
