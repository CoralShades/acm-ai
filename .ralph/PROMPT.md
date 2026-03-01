You are implementing E19/E20 sprint stories for ACM-AI — an intelligent Asbestos Containing Material compliance management system.

Read `.ralph/@fix_plan.md` for the current task list.
Read `CLAUDE.md` for project conventions and architecture.
Read `docs/sprint-artifacts/e19-e20-implementation-prompts.md` for per-story detailed implementation instructions.

## Workflow Per Iteration

1. Read `.ralph/@fix_plan.md` — find the next unchecked task `- [ ]`
2. Read the corresponding story file from `docs/sprint-artifacts/` (path is in the task line)
3. Read the matching story section in `docs/sprint-artifacts/e19-e20-implementation-prompts.md` for detailed implementation steps
4. Implement the story following patterns in `CLAUDE.md`
5. Delegate to specialists based on file scope:
   - `migrations/`, `api/`, `open_notebook/`, `commands/` → `backend-specialist`
   - `frontend/` → `frontend-specialist`
   - Mixed stories (backend + frontend): delegate to `backend-specialist` FIRST, then `frontend-specialist` (API before UI)
   - Only use specialists when the story touches multiple files/layers; implement simple single-file changes directly
6. Run full verification after all implementation:
   ```
   uv run ruff check .
   uv run pytest tests/ -x
   cd frontend && npm run lint && npm run build
   ```
7. If all verification passes:
   - Check off the task in `.ralph/@fix_plan.md` (change `- [ ]` to `- [x]`)
   - Mark story `done` in `docs/sprint-artifacts/sprint-status.yaml`
   - Append a Dev Agent Record to the bottom of the story file:
     ```
     ---
     ## Dev Agent Record
     **Implemented:** [date]
     **Files changed:** [list key files]
     **Tests added:** [list test files]
     **Verification:** ruff ✓ | pytest ✓ | lint ✓ | build ✓
     ```
   - Advance the NEXT story in the sequence to `ready-for-dev` in `sprint-status.yaml` (see sequence below)
   - Log completion to `docs/sprint-artifacts/party-mode-20260224/progress.md` (create if missing)
   - Commit: `feat(STORY-ID): brief description of what was built`
8. If verification fails: fix and retry (max 3 attempts), then output `<promise>BLOCKED</promise>: [reason + error details]`
9. After ALL tasks are `[x]` in `@fix_plan.md` and verification passes: output `<promise>COMPLETE</promise>`

## Story Sequence (STRICT ORDER — one at a time)

```
E19-S1 → E19-S2 → E19-S3 → E19-S4 → E19-S5 → E19-S6 → E19-S7 → E19-S8 (P1)
→ E20-S1 → E20-S2 → E20-S3 → E20-S4
```

When advancing the next story, use this map:
- After E19-S1 done → set `e19-s2-jobs-dashboard: ready-for-dev`
- After E19-S2 done → set `e19-s3-feature-gating: ready-for-dev`
- After E19-S3 done → set `e19-s4-raw-extraction-table: ready-for-dev`
- After E19-S4 done → set `e19-s5-building-review-wizard: ready-for-dev`
- After E19-S5 done → set `e19-s6-acm-schema-mapping-wizard: ready-for-dev`
- After E19-S6 done → set `e19-s7-job-detail-page: ready-for-dev`
- After E19-S7 done → set `e19-s8-conversational-crud-chat: ready-for-dev`
- After E19-S8 done → set `e20-s1-page-boundary-fix: ready-for-dev`
- After E20-S1 done → set `e20-s2-regex-yield-check: ready-for-dev`
- After E20-S2 done → set `e20-s3-not-sampled-capture: ready-for-dev`
- After E20-S3 done → set `e20-s4-e2e-accuracy-validation: ready-for-dev`

## Special Rules

⚠️ **E19-S1 DESTRUCTIVE**: Migration 032 deletes ALL `acm_record` rows and adds `review_status` to `source`. This is expected and approved by the user — proceed without additional confirmation.

⚠️ **E20-S4 GATE**: Do NOT run real PDF extraction for E20-S4 until E20-S1, E20-S2, AND E20-S3 unit tests all pass. Before the extraction run, verify:
```
uv run pytest tests/test_building_inventory*.py tests/test_orchestrator*.py tests/test_acm_extraction*.py -x
```
Only run ONE real extraction on `docs/samplePDF/` to validate. Never re-run unless a specific bug is confirmed unfixed.

💰 **COST AWARENESS**: Never trigger real LLM extraction calls during unit test development. Write all code and tests first, lint + unit tests must pass, THEN run the single validation extraction for E20-S4.

🔄 **E19-S8 is P1**: Lower priority than P0 stories. Implement it after E19-S7 is fully done and verified.

## Commit Strategy

- Commit directly to `main` branch after each completed story
- Format: `feat(e19-s1): add review_status field and clean acm_record slate`
- Do NOT push — you only commit; push is handled by the user after review

## MANDATORY SKILL INVOCATIONS

Before implementing any task:
1. Invoke superpowers:test-driven-development — follow RED-GREEN-REFACTOR
2. Write the failing test FIRST, watch it fail, then implement

When debugging any failure:
1. Invoke superpowers:systematic-debugging — follow 4-phase process
2. Do NOT guess — trace root cause systematically

After completing all tasks:
1. Invoke superpowers:requesting-code-review — run pre-review checklist
2. Only output <promise>COMPLETE</promise> after review passes

## Never Skip

- Never mark a task complete without all verification passing
- Never skip tests or linting
- Always write unit tests alongside implementation
- Always read the full story spec AND the implementation prompt before coding
- Never run real extractions except as explicitly permitted above
- ALWAYS invoke superpowers skills when they apply — this is mandatory, not optional
