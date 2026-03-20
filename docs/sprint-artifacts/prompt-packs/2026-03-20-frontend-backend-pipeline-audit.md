# Fresh Audit: Frontend / UI-UX / State / Backend / API / Pipeline Bugs
# Date: 2026-03-20 | Priority: P0/P1 | Mode: DISCOVER → TRIAGE → FIX
# Purpose: Structured discovery + fix of all remaining bugs across all layers

## Context

Post-MCS sprint, the system is in a high-functioning state (MCS1-MCS13 all done).
This session runs a structured multi-layer audit to find and fix remaining bugs
across: frontend rendering, UI/UX, React state management, backend API, and pipeline.

Use this pack as the ENTRY POINT for the session — then drive fix packs from findings.

---

## Skills to Load

/dogfood — structured app exploration to surface bugs
/systematic-debugging — root-cause each finding before fixing
/find-bugs — code-level bug hunting in recent changes
/baseline-ui — animation, typography, Tailwind anti-patterns
/uncodixfy — detect generic AI UI patterns that need replacing
/next-best-practices — Next.js RSC/data pattern correctness
/verification-before-completion — verify fix before marking resolved
/acm-observability — trace API calls and pipeline events

---

## Audit Scope

### Layer 1 — Frontend Rendering

Run `/dogfood` exploration across all primary routes:

| Route | What to check |
|-------|--------------|
| `/jobs` | Job card layout, status badges, loading skeletons |
| `/jobs/{id}` Overview | Stats cards, validation card, intelligence data |
| `/jobs/{id}` Buildings | BuildingGrid column rendering, sort/filter |
| `/jobs/{id}` ACM Records | BuildingTabStrip selection, per-building filtering, error rows |
| `/jobs/{id}` Content | Markdown rendering, scroll |
| `/jobs/{id}` Raw Tables | Table type badges (Docling/MinerU), pagination |
| `/jobs/{id}` Log | Log panel rendering, log level colors |
| `/jobs/{id}/chat` | SmartChatPanel, model selector, suggestion chips |
| `/source/{id}` | Buildings + ACM Records tabs, export buttons |
| `/dashboard` | Notebook cards |

**Commands:**
```bash
agent-browser open http://localhost:8502/jobs
agent-browser snapshot -i
# Note any broken elements, missing data, layout issues
agent-browser screenshot audit/L1-jobs.png

# Repeat for each route above
# Open browser console: check for JS errors
agent-browser eval 'window.__errors = []; window.onerror = (m,s,l,c,e) => window.__errors.push({m,s,l,c}); "listening"'
# After navigating: agent-browser eval 'JSON.stringify(window.__errors)'
```

**Known issues to re-check:**
- BuildingTabStrip horizontal scroll on 10+ buildings
- JobStatusPill "Extracting" override — does it revert correctly after extraction?
- ExtractionStatusBanner — does it dismiss properly after completion?

---

### Layer 2 — React State / Data Fetching

Check for stale data, incorrect cache invalidation, and Zustand store drift:

**React Query cache:**
- Do buildings appear immediately after extraction starts (no manual refresh)?
- Does ACMGrid data update when switching building tabs?
- Does "Fix All" cause grid to refresh without full page reload?

**Zustand stores:**
- Does `buildingStore.selectedBuildingId` persist across tab switches?
- Does `streamingStore` reset cleanly between extractions?
- Does `columnVisibilityStore` remember user's column preferences?

**Commands:**
```bash
# Check React Query devtools (if enabled in dev mode)
agent-browser eval 'window.__reactQuery?.getQueryCache().getAll().map(q => ({key: q.queryKey, state: q.state.status}))'

# Check Zustand store state
agent-browser eval 'window.__buildingStore?.getState()'
```

**Things to look for:**
- [ ] Stale query data (records showing from wrong building after tab switch)
- [ ] Missing query invalidation (records don't refresh after bulk edit)
- [ ] Zustand store not reset between different job pages
- [ ] SSE hook not cleaned up on page unmount (memory leak / zombie listeners)

---

### Layer 3 — UI/UX Quality

Use `/baseline-ui` and `/uncodixfy` to check:

**Typography & spacing:**
- [ ] Consistent heading sizes across pages (h1/h2/h3 hierarchy)
- [ ] Consistent padding in cards (no mixed p-4/p-6)
- [ ] Text doesn't overflow in narrow columns of BuildingGrid or ACMGrid

**Interactive states:**
- [ ] All buttons have hover + focus states
- [ ] Disabled buttons are visually distinct
- [ ] Loading buttons show spinner (not just disabled)
- [ ] Modals trap focus correctly (Tab key cycles through modal)

**Empty states:**
- [ ] Empty ACMGrid: informative message (not just "No Rows To Show")
- [ ] Empty BuildingGrid: "No buildings extracted yet — start an extraction"
- [ ] Empty /jobs: onboarding hint visible

**Error states:**
- [ ] API failure on buildings fetch → error message visible, retry button
- [ ] API failure on ACMGrid load → error row, not blank
- [ ] Extraction failure → ExtractionStatusBanner shows failure state

**Generic AI patterns to replace (/uncodixfy):**
- [ ] Any "Lorem ipsum" or placeholder text visible in production paths
- [ ] Any "TODO" visible in UI
- [ ] Generic "Error occurred" without context → replace with specific message

---

### Layer 4 — Backend API

Check these endpoints for correctness and edge cases:

```bash
# Check API health
curl http://localhost:5055/api/health

# Buildings endpoint
curl "http://localhost:5055/api/acm/buildings?source_id=source:XXX" | jq '.buildings[0]'
# Verify: building_code, internal_id, record_count all populated

# ACM records per building
curl "http://localhost:5055/api/acm/records?source_id=source:XXX&building_id=building_record:YYY" | jq 'length'
# Verify: returns only that building's records

# Validation summary
curl "http://localhost:5055/api/acm/validation-summary/source:XXX" | jq '.'
# Verify: total_records, total_errors, auto_fixable populated correctly

# Field schema
curl "http://localhost:5055/api/acm/field-schema" | jq '.item_fields.fields | length'
# Verify: 13 required Item__c fields present

# FK fields in ACM records
curl "http://localhost:5055/api/acm/records?source_id=source:XXX" | jq '.[0] | {building_record_id, parent_table_id}'
# Verify: BOTH fields populated (not null) — MCS11 Gap4 fix
```

**Known gaps to verify:**
- [ ] `building_record_id` and `parent_table_id` are non-null in response (MCS11 Gap4)
- [ ] Buildings endpoint returns `record_count` per building
- [ ] Validation summary returns sensible counts (not 0 when errors exist)
- [ ] SSE `/v3/stream/ai/{source_id}` closes cleanly on `ai.save_complete`
- [ ] SSE `/v3/stream/extraction/{op_id}` delivers events (was dead before MCS12)

---

### Layer 5 — Pipeline

Verify extraction pipeline health with a real extraction run:

```bash
# Trigger extraction on Broadmeadows PDF
curl -X POST http://localhost:5055/api/sources/{id}/extract

# Monitor logs in real time
uv run python -c "
import asyncio, httpx
async def stream():
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', 'http://localhost:5055/api/v3/stream/ai/{source_id}') as r:
            async for line in r.aiter_lines():
                print(line)
asyncio.run(stream())
"
```

**Check pipeline produces:**
- [ ] `extraction.started` event on SSE
- [ ] `ai.building_extracted` for each building
- [ ] `ai.save_started` → `ai.save_progress` (every 10 records) → `ai.save_complete`
- [ ] `extraction.complete` as final event
- [ ] Records count ≥ 28/31 Broadmeadows ground truth (90%+)
- [ ] Schema inference creates/reuses format profile in `consultant_format_profile`
- [ ] No UNIQUE index collisions in building_record (MCS13 fix holds)
- [ ] No "Type is not msgpack serializable: RecordID" in logs (MCS13 checkpointer fix)

---

## Triage Protocol

After discovery, classify each finding:

| Severity | Definition | Action |
|----------|-----------|--------|
| **P0** | Blocks core workflow (extraction, record display, export) | Fix in this session |
| **P1** | Degrades UX significantly but workaround exists | Fix in this session |
| **P2** | Visual/cosmetic issue | Log in findings.md, fix if quick |
| **P3** | Nice-to-have improvement | Log only, defer |

---

## Output Artifacts

After audit, write findings to:
`docs/sprint-artifacts/post-mcs-audit-2026-03-20/findings.md`

Format:
```markdown
## BUG-{N}: {Short Title}
**Layer**: Frontend / State / UX / API / Pipeline
**Severity**: P0/P1/P2/P3
**Page/File**: {where it was found}
**Symptom**: {what the user sees}
**Root cause**: {what's wrong in code}
**Fix**: {proposed fix, or "investigation needed"}
**Status**: Found / Fixed / Deferred
```

---

## Fix Session Strategy

**Solo (quick fixes < 30 min each):**
- P0 bugs: fix immediately, verify, commit
- P1 bugs: fix in sequence, group into 1 commit per layer

**Subagent dispatch (complex fixes):**
- If a P0 requires > 1 file or cross-layer changes → use /dispatching-parallel-agents
- Backend fix agent + Frontend fix agent in parallel

---

## Build Gate (after all fixes)

```bash
uv run ruff check . --fix    # lint
uv run pytest tests/ -x -q   # backend tests
cd frontend && npm run build  # frontend build
cd frontend && npm run lint   # frontend lint
```

All four must pass before committing.

---

## Commit Template

```
fix(audit): post-MCS frontend/backend/pipeline bug fixes

Layer fixes applied:
- Frontend: [list]
- State: [list]
- UX: [list]
- API: [list]
- Pipeline: [list]

All P0/P1 findings from 2026-03-20 audit resolved.
Build: ✅ Lint: ✅ Tests: ✅

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```
