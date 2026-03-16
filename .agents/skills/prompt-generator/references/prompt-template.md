# Prompt Template

Master template for generated Claude Code session prompts. All `{{ variable }}` placeholders are populated by the prompt-generator skill (Phase 4c). Do not edit placeholders — they are replaced at generation time.

---

```
# Session: {{ session_title }}

## Skills to Load

{{ skill_directives }}

---

## Prerequisites

Before starting this session, verify:

{{ prerequisites }}

---

## Project Glossary

Key terms for this session. Refer to these definitions when interpreting code or instructions.

{{ glossary_table }}

---

## Current State

{{ current_state }}

---

## Key Files

Files this session will read or modify. Verify all paths exist before starting.

{{ key_files_list }}

---

{{ plan_or_steps }}

---

## Agent Strategy

{{ strategy_config }}

---

{{ context7_section }}

---

## Verification Checklist

Run these commands in order before marking the session complete. All must pass.

{{ verification_items }}

---

## Files Summary

{{ files_summary }}

---

## Commit Template

When work is complete, use this commit message structure:

{{ commit_message }}
```

---

## Section Descriptions

### 1. `{{ session_title }}`

One sentence describing the session goal. Format: `[Verb] [object] [constraint/context]`

Examples:
- `Fix building sidebar crash when source has 0 records`
- `Add MinerU v2 extraction provider with DoclingAdapter fallback`
- `Refactor pre-extraction stages to reduce LLM calls from 3 to 1`

### 2. `{{ skill_directives }}`

One skill per line with a `/` prefix. Include only skills selected by the prompt-router.

Format:
```
/planning-with-files — persistent markdown plan for session continuity
/langgraph-fundamentals — LangGraph graph/node/state patterns
/systematic-debugging — structured diagnosis before proposing fixes
/verification-before-completion — verify work before claiming done
```

### 3. `{{ prerequisites }}`

Bulleted list of what must be true before the session can start.

Format:
```
- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`
- Branch: `git checkout ACMV3` (or create feature branch)
- File exists: `D:/ailocal/acm-ai/open_notebook/extractors/providers/base.py`
```

### 4. `{{ glossary_table }}`

Markdown table of 5–15 key terms relevant to this session's domain.

Format:
```
| Term | Definition |
|------|-----------|
| Building__c | Salesforce object representing a building in the SAMP register |
| ExtractionState | TypedDict flowing through the LangGraph extraction pipeline |
| ... | ... |
```

### 5. `{{ current_state }}`

Bullet points describing the current relevant state of the codebase.

Format:
```
- Branch: ACMV3 (last commit: fix(extraction): Source.name→title in BuildingRecord ID gen)
- Sprint: V3-8, 6 stories remaining (E35-S3..S8)
- Last known issue: building sidebar returns 0 records when source has no processed documents
- Relevant recent change: E35-S2 completed — model defaults now persist to SurrealDB
```

### 6. `{{ key_files_list }}`

Absolute paths grouped by role. Include brief inline comment for each.

Format:
```
**Read (reference):**
- `D:/ailocal/acm-ai/open_notebook/graphs/acm_extraction.py` — main extraction graph
- `D:/ailocal/acm-ai/open_notebook/domain/acm.py` — ACMRecord domain model

**Modify:**
- `D:/ailocal/acm-ai/open_notebook/extractors/providers/base.py` — add new method
- `D:/ailocal/acm-ai/api/routers/acm.py` — add new endpoint

**Create:**
- `D:/ailocal/acm-ai/open_notebook/extractors/providers/mineru_v2.py` — new provider
```

### 7. `{{ plan_or_steps }}`

**If `plan_mode=true`** — use plan format:
```
## Plan

Read `docs/sprint-artifacts/task_plan.md` before starting. Update it as you work.

### Task Plan Reference
- task_plan.md: D:/ailocal/acm-ai/docs/sprint-artifacts/task_plan.md
- findings.md: D:/ailocal/acm-ai/docs/sprint-artifacts/findings.md
- progress.md: D:/ailocal/acm-ai/docs/sprint-artifacts/progress.md
```

**If `plan_mode=false`** — use steps format:
```
## What to Change

1. **[Step name]** — [file]: [what to do]
2. **[Step name]** — [file]: [what to do]
3. Verify: run verification checklist below
```

### 8. `{{ strategy_config }}`

Agent strategy block. Varies by strategy type.

**Solo agent:**
```
Strategy: SOLO
Run all steps in sequence in a single Claude Code session.
No subagents or tmux panes required.
```

**Subagent dispatch:**
```
Strategy: SUBAGENT-DISPATCH
Use the Task tool to dispatch independent work items in parallel.

Subagents:
- backend-task: [description of backend work]
- frontend-task: [description of frontend work]
- verifier: Run verification checklist after both complete

Spawn backend-task and frontend-task in parallel. Wait for both before spawning verifier.
```

**Tmux team:**
```
Strategy: TMUX-TEAM
Use tmux to run 3 panes in parallel.

Pane layout:
  Pane 0 (orchestrator): Reads plan, delegates, synthesizes results
  Pane 1 (backend-dev):  Implements backend changes
  Pane 2 (verifier):     Runs tests and build after each step

Commands:
  tmux new-session -d -s acm-session
  tmux split-window -h
  tmux split-window -v
```

### 9. `{{ context7_section }}`

Context7 directives for fetching live library docs. Omit this section entirely if `context7_directives` is empty.

Format:
```
## Context7 Directives

Run these at session start to load current library documentation:

1. resolve-library-id for "langchain" → query-docs for "graph state streaming callbacks"
2. resolve-library-id for "langgraph" → query-docs for "node conditional edges interrupt"
3. resolve-library-id for "surrealdb" → query-docs for "record ID binding parameters"
```

### 10. `{{ verification_items }}`

Bulleted checklist of verification commands. All must pass before marking complete.

Format:
```
- [ ] `uv run ruff check .` — Python lint (0 errors)
- [ ] `uv run pytest tests/ -x` — Backend tests (all pass)
- [ ] `cd frontend && npm run build` — Frontend build (0 errors)
- [ ] `curl http://localhost:5055/api/acm/buildings?source_id=test` — API responds 200
- [ ] Screenshot: navigate to `/source/{id}` and verify building sidebar loads
```

### 11. `{{ files_summary }}`

Table of file operation counts from the key files list.

Format:
```
| Operation | Count | Files |
|-----------|-------|-------|
| NEW | 2 | mineru_v2.py, test_mineru_v2.py |
| MODIFY | 4 | base.py, __init__.py, acm.py, acm.ts |
| MOVE | 0 | — |
| DELETE | 0 | — |
```

### 12. `{{ commit_message }}`

Conventional commit template pre-filled with type, scope, and subject placeholder.

Format (select based on request type):
```
# Feature:
feat(extraction): add MinerU v2 extraction provider with fallback chain

# Bug fix:
fix(acm): resolve building sidebar crash when source has 0 records

# Refactor:
refactor(pipeline): reduce pre-extraction LLM calls from 3 to 1

# Docs:
docs(claude): add prompt generation system to CLAUDE.md

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
