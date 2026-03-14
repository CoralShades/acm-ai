# Pipeline Debug Progress

## Status: Phase 3 — Fixes Applied, Awaiting Verification

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
| 4.1 Re-run extraction | PENDING | |
| 4.2 Ground truth compare | PENDING | |
| 4.3 DB verification | PENDING | |
