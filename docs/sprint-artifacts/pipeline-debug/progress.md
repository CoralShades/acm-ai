# Pipeline Debug Progress

## Status: Phase 4 — Verification Complete

| Step | Status | Notes |
|------|--------|-------|
| 1.1 Langfuse traces | DONE | Both traces analyzed — content ingestion + ACM extraction |
| 1.2 LangSmith runs | DONE | Both runs analyzed — confirmed bulk mode, 25 records |
| 1.3 Prompt audit | DONE | 13 templates audited, 3 CRITICAL, 2 HIGH issues found |
| 1.4 Persistence audit | DONE | All 6 known bugs FIXED, 7 new issues (2 MEDIUM, 5 LOW) |
| 2.1 Synthesize findings | DONE | 5 root causes ranked by impact |
| 2.2 Draft prompt rewrites | DONE | 3 templates rewritten for Ollama |
| 2.3 Draft code fixes | DONE | format="json" added to 2 files |
| 2.4 User approval | DONE | Approved |
| 3.1 Apply prompts | DONE | metadata_and_structure, building_inventory, row_split |
| 3.2 Apply code fixes | DONE | format="json" in metadata_and_structure.py, building_inventory.py |
| 3.3 Lint | DONE | ruff check passes |
| 3.4 Tests | DONE | 2123 passed, 5 pre-existing failures (unrelated) |
| 4.1 Re-run extraction | DONE | 29 records extracted (up from 0) |
| 4.2 Ground truth compare | DONE | 29/31 (93.5%) — see findings.md for details |
| 4.3 DB verification | DONE | 1 building, 29 records, all high confidence |

## Additional Fixes Applied (Phase 3b)

| Fix | Status | Notes |
|-----|--------|-------|
| RC6: Stale `docling_document_json` detection | DONE | `IS NULL` → `IS NULL OR = {}` in acm_commands.py + acm_extraction.py |
| RC7: SurrealDB param binding in stale check | DONE | Added `ensure_record_id()` for `$sid` param in acm_commands.py |
| WebSocket retry in orchestrator.py | DONE | Retry once on timeout for `_get_docling_tables` |

## Known Remaining Issues

| Issue | Severity | Notes |
|-------|----------|-------|
| `docling_document_json` stores as `{}` | MEDIUM | DoclingAdapter `model_dump()` returns data but SurrealDB stores empty dict — prevents per-row extraction |
| Per-row extraction never triggers | MEDIUM | Blocked by empty docling_document_json — bulk mode used as fallback |
| Model selection: phi4:14b used instead of configured qwen2.5:7b | LOW | DB model default resolves to phi4 record ID |
