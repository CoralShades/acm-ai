# Fix Prompt: P0 + P1 Extraction & UI Issues

> Generated: 2026-03-17 | Target: 12 issues (6 P0 + 6 P1)
> Strategy: Subagent dispatch — 3 parallel tracks

---

## Prompt

```
You are fixing 12 critical and high-priority bugs in the ACM-AI extraction pipeline and frontend.
Read the issue registry at `docs/sprint-artifacts/issue-registry.md` and the planning files
(`task_plan.md`, `findings.md`, `progress.md`) before starting.

### Skills to load
- /systematic-debugging — for root-cause analysis before each fix
- /verification-before-completion — verify each fix with tests before moving on

### Strategy: 3 Parallel Tracks

Use /dispatching-parallel-agents to run 3 tracks concurrently:

---

#### Track A: Backend/Worker (6 bugs)

Agent: backend-specialist | Model: sonnet

**A1. BUG-CORRECT-BYPASS** — `should_correct` node in `acm_extraction.py`
- The routing condition only checks `with_issues > 0` but ignores `rejected > 0`
- Fix: change to `rejected > 0 OR with_issues > 0`
- Add a pytest case that sets `rejected=3, with_issues=0` and asserts route → "correct"

**A2. BUG-CORRECT-JSON** — Correction LLM at `acm_extraction.py:~2600`
- The correction LLM is instantiated without `_apply_ollama_extraction_settings()`
- Fix: add the call after LLM creation, same pattern as the extraction LLM
- Verify: `format="json"` appears in model kwargs

**A3. BUG-NO-ACCESS-DEAD** — `acm_extraction.py:1024-1031`
- Per-row extraction path skips `recover_no_access_node` entirely
- Fix: add a per-row recovery branch that re-processes no-access items individually
- If complex, add a TODO and move on — this is P0 but low frequency

**A4. BUG-PROGRESS-STUCK** — `pipeline_logger.py` + `acm_commands.py`
- The STORE stage completes but never emits "completed" status
- Fix: after final `stage_exit(STORE)`, call `self.mark_completed()` or equivalent
- Also check `acm_commands.py` — it may need to update the command status

**A5. BUG-TWO-BUILDING** — Building extraction `asyncio.gather`
- `asyncio.gather` without `return_exceptions=True` — one failure kills all
- Fix: add `return_exceptions=True`, then check each result for exceptions
- Test: Alexander Hospital (5 buildings) should produce results even if one fails

**A6. BUG-COMPOUND-SAMPLE** — `orchestrator.py` sample_result handling
- Compound values like "Positive (Chrysotile)/Negative" not split
- Fix: add splitter in normalization that handles `/` and `;` delimiters
- Fix empty correction JSON: add fallback when correction returns `{}`

---

#### Track B: API (2 bugs)

Agent: backend-specialist | Model: sonnet

**B1. BUG-BACKFILL-500** — `api/routers/acm.py`
- `source.name` → `source.title` (AttributeError)
- Quick fix, add proper error handling for missing source

**B2. BUG-REREV-NULLIFY** — `open_notebook/database/repository.py:179-203`
- SurrealDB MERGE with partial object nullifies unset fields
- Fix: filter out None/unset fields before MERGE, or use field-by-field SET
- Test: re-review a building, then verify intelligence fields survive

---

#### Track C: Frontend (3 bugs)

Agent: frontend-specialist | Model: sonnet

**C1. BUG-HITL-INFINITE** — `frontend/src/components/jobs/CrudToolRenderers.tsx`
- useEffect dependency loop causes infinite re-render
- Fix: stabilize dependencies with useMemo/useCallback, or move state update out of effect
- Test: `npm run build` must pass, manually verify write operation works

**C2. BUG-HIDDEN-TABS** — `frontend/src/app/(dashboard)/jobs/[id]/page.tsx`
- TabsContent exists for "Raw Tables" and "Log" but TabsTrigger is missing
- Fix: add TabsTrigger elements to TabsList
- Verify: tabs visible and clickable in browser

**C3. BUG-ROOM-NAME** — Prompt/schema alignment
- Prompt uses `room_name` but SF schema expects `Specific_Location__c`
- Fix: update the extraction prompt OR add a mapping in `acm_row_mappers.py`
- Check: `prompts/acm/row_extraction.jinja` and `open_notebook/domain/acm_row_mappers.py`

---

### Verification Checklist

After all 3 tracks complete:

1. [ ] `uv run pytest tests/ -x` — all tests pass
2. [ ] `cd frontend && npm run build` — no type errors
3. [ ] Re-extract Broadmeadows (source:ktioihsjj9ih7kd95fcx, force=true):
   - ≥29 ACM records (ground truth: 31)
   - `docling_document_json` populated (not `{}`)
   - Per-row extraction path used (check logs for `row_segmenter`)
   - `area_type` populated on records
4. [ ] Re-extract Alexander Hospital (upload `docs/samplePDF/Clucth_Alexander_District_Hospital_A Cooper.pdf`):
   - 5 buildings with clean names (no pipe-delimited garbage)
   - ≥40 ACM records (ground truth: 43)
5. [ ] HITL write operation works in chat UI

### Commit Template

```
fix(pipeline): resolve P0+P1 extraction and UI issues

- Fix CORRECT stage bypass for rejected-only records
- Apply Ollama JSON format to correction LLM
- Fix extraction progress stuck at "running"
- Fix backfill-buildings AttributeError (source.name → source.title)
- Fix HITL dialog infinite re-render loop
- Expose hidden Raw Tables and Log tabs
- Add return_exceptions=True to multi-building asyncio.gather
- Fix room_name/Specific_Location__c field alignment

Resolves: BUG-CORRECT-BYPASS, BUG-CORRECT-JSON, BUG-PROGRESS-STUCK,
BUG-BACKFILL-500, BUG-HITL-INFINITE, BUG-HIDDEN-TABS, BUG-TWO-BUILDING,
BUG-ROOM-NAME

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

### Key Files Reference

| File | Issues |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | A1, A2, A3, A5, A6 |
| `open_notebook/extractors/pipeline_logger.py` | A4 |
| `commands/acm_commands.py` | A4 |
| `open_notebook/extractors/orchestrator.py` | A6 |
| `api/routers/acm.py` | B1 |
| `open_notebook/database/repository.py` | B2 |
| `frontend/src/components/jobs/CrudToolRenderers.tsx` | C1 |
| `frontend/src/app/(dashboard)/jobs/[id]/page.tsx` | C2 |
| `prompts/acm/row_extraction.jinja` | C3 |
| `open_notebook/domain/acm_row_mappers.py` | C3 |
| `docs/sprint-artifacts/issue-registry.md` | All (reference) |
```
