# Log Monitor - Findings

## Summary
The E2E test extraction pipeline ran **3 attempts**:
1. **Attempt 1** (13:56:00): FAILED - Race condition, `acm_extract` ran before `process_source` finished
2. **Attempt 2** (13:58:25): FAILED - Model `anthropic/claude-3.5-haiku-20241022` not found on OpenRouter
3. **Attempt 3** (13:59:33): **SUCCEEDED** - Model fixed to direct Anthropic API, **8 records extracted** in 75.56s

---

## Attempt 1: Race Condition Failure

### Timeline
| Timestamp | Event | Status |
|-----------|-------|--------|
| 13:56:00.071 | `acm_extract` command started | Started |
| 13:56:00.074 | `process_source` command started | Started |
| 13:56:00.096 | `acm_extract` checks source text | FAILED - no text content |
| 13:56:38.358 | `process_source` completed (38.28s total) | OK |

### Root Cause
Both commands dispatched simultaneously. `acm_extract` failed in 25ms because PDF text wasn't parsed yet.

### Evidence
```
13:56:00.071 | INFO  | acm_commands:79 - Starting AI-powered ACM extraction
13:56:00.074 | INFO  | source_commands:67 - Starting source processing
13:56:00.096 | ERROR | acm_commands:215 - ACM extraction failed: Source has no text content
```

---

## Attempt 2: Model Configuration Failure

### Timeline
| Timestamp | Event | Status |
|-----------|-------|--------|
| 13:58:25.221 | `acm_extract` started (command:2efksp566r109nwnhx5h) | Started |
| 13:58:25.242 | Source loaded: 33,595 chars | OK |
| 13:58:25-26 | STRUCTURE stage - all 4 LLM calls returned 404 | WARNING (heuristic fallbacks) |
| 13:58:27-35 | EXTRACT stage - 4 attempts, all 404 | FAILED |
| 13:58:35.369 | Pipeline FAILED (10.1s) | FAILED |

### Root Cause
Model ID `anthropic/claude-3.5-haiku-20241022` not valid on OpenRouter. The `user_id: org_39EEuJZZKvmuoIWd9RRKxp2eyq5` confirmed OpenRouter routing.

### Pipeline Stages (Degraded)
| Stage | Status | Duration | Notes |
|-------|--------|----------|-------|
| STRUCTURE | COMPLETED (degraded) | 1.6s | All 4 LLM calls 404, heuristic fallbacks |
| ORCHESTRATOR | SKIPPED | 0s | Below threshold |
| PREFLIGHT | COMPLETED | 0.0s | 1 chunk, 29,411 chars, 0 ACM indicators |
| EXTRACT | FAILED | ~8.5s | 4 attempts (1+3 retries), all 404 |

---

## Attempt 3: SUCCESSFUL Extraction

### Context
Team lead fixed model configuration: created new model record using direct Anthropic API (not OpenRouter) and updated SurrealDB default model assignments.

### Timeline
| Timestamp | Event | Duration | Status |
|-----------|-------|----------|--------|
| 13:59:33.846 | `acm_extract` started (command:xutxhvpo7aowse1v3iyq) | - | Started |
| 13:59:33.871 | Source loaded: 33,595 chars | 0.03s | OK |
| 13:59:33.873 | STRUCTURE stage started | - | OK |
| 13:59:48.052 | Metadata extracted: consultant=Prensa Pty Ltd, 13 fields | 14.2s | OK |
| 14:00:00.324 | Structure: type=DIVISION_5, 7 sections, 1 building | 12.3s | OK |
| 14:00:11.683 | Building inventory: 1 building, 1 group, pages 1-4 | 11.4s | OK |
| 14:00:28.001 | Page tagging: 12 pages, register_range=(3,4) | 16.3s | OK |
| 14:00:28.003 | STRUCTURE completed | **49.9s** | OK |
| 14:00:28.005 | ORCHESTRATOR started | - | OK |
| 14:00:28.007 | Plan: 1 building, 1 LLM call | - | OK |
| 14:00:49.050 | ORCHESTRATOR completed: 9 raw records | **21.0s** | OK |
| 14:00:49.051 | VALIDATE: 9 accepted, 0 rejected | ~0s | OK |
| 14:00:49.060 | STORE started | - | OK |
| 14:00:49.061 | Deduplication: 1 merged, 8 unique | - | OK |
| 14:00:49.091 | 1 parent table section created | - | OK |
| 14:00:49.363 | SiteConfig auto-fill FAILED (DB schema error) | - | WARNING |
| 14:00:49.406 | 8/8 records saved | **0.3s** | OK |
| 14:00:49.407 | **PIPELINE COMPLETE: 8 records in 71.3s** | **71.3s** | OK |
| 14:00:49.449 | EMBED started | - | OK |
| 14:00:50.289 | EMBED completed: 8/8 records embedded | **0.9s** | OK |
| - | **Total command time** | **75.56s** | OK |

### Pipeline Stage Breakdown

| Stage | Duration | Result |
|-------|----------|--------|
| STRUCTURE | 49.9s | 12 pages tagged, register=(3,4), type=DIVISION_5 |
| -- Metadata | 14.2s | consultant=Prensa Pty Ltd, 13/16 fields (3 missing) |
| -- Structure | 12.3s | type=DIVISION_5, 4 pages, 7 sections, 1 building |
| -- Building inventory | 11.4s | 1 building, 1 processing group, pages 1-4 |
| -- Page tagging | 16.3s | 12 pages tagged, register_range=(3,4) |
| ORCHESTRATOR | 21.0s | 1 building, 1 LLM call, 9 raw records |
| VALIDATE | ~0s | 9 accepted, 0 rejected, 0 with issues |
| STORE | 0.3s | 1 duplicate merged, 8 unique saved, 1 parent section |
| EMBED | 0.9s | 8/8 records embedded (Ollama mxbai-embed-large) |
| **Total** | **75.56s** | **8 records** |

### Key Metrics
- **Records extracted**: 9 raw -> 1 duplicate merged -> **8 saved**
- **Confidence**: high=8, medium=0, low=0 (100% high confidence)
- **Validation**: 9/9 accepted (0 rejected, 0 with issues)
- **Strategy**: full_llm=1 (single LLM extraction call for 1 building)
- **Embedding**: 8/8 embedded via Ollama mxbai-embed-large (local)
- **Document type**: DIVISION_5
- **Register pages**: 3-4 (of 12 total pages tagged)

### SiteConfig Error (Non-blocking)
During the STORE stage, `auto_populate_site_config` failed with a SurrealDB schema error:
```
Found 'source:lap4wnbxllavswdgghro' for field `source_id`, with record `site_config:ej1ljokhlbnxozug68zi`, but expected a record<source>
```
The `site_config.source_id` field expects a `record<source>` type but received a string. This was caught gracefully and did not prevent record saving. The 8 ACM records were saved successfully despite this error.

Stack trace: `acm_extraction.py:1664` -> `metadata_extractor.py:368` -> `site_config.py:239` -> `base.py:137` -> `repository.py:93`

---

## All Errors Found

| # | Attempt | Severity | Message | Location |
|---|---------|----------|---------|----------|
| 1 | 1 | CRITICAL | `Source has no text content` | `acm_commands:215` |
| 2 | 2 | CRITICAL | `No endpoints found for anthropic/claude-3.5-haiku-20241022` (8x) | Various extractors |
| 3 | 2 | CRITICAL | `Extraction failed after 3 retries` | `acm_commands:119` |
| 4 | 3 | ERROR | SurrealDB: `source_id` expected `record<source>` got string | `repository.py:93` |

## All Warnings Found

| # | Attempt | Message | Location |
|---|---------|---------|----------|
| 1 | 1 | `Consider using pymupdf_layout package` | PyMuPDF |
| 2 | 2 | 4x LLM calls failed with 404, heuristic fallback | Various extractors |
| 3 | 3 | `SiteConfig auto-fill failed` | `acm_extraction.py:1666` |

## Model Calls Summary

| Attempt | Calls | Result | Provider |
|---------|-------|--------|----------|
| 1 | 0 | Failed before LLM stage | N/A |
| 2 | 8 (4 structure + 4 extract) | All 404 | OpenRouter |
| 3 | 5 (4 structure + 1 orchestrator) | All succeeded | Direct Anthropic |

### Attempt 3 LLM Call Detail
| Call | Duration | Result |
|------|----------|--------|
| Metadata extraction | ~14s | consultant=Prensa Pty Ltd, 13 fields |
| Structure extraction | ~12s | type=DIVISION_5, 1 building |
| Building inventory | ~11s | 1 building, pages 1-4 |
| Page tagging | ~16s | 12 pages, register=(3,4) |
| Record extraction (orchestrator) | ~21s | 9 raw records |
| **Embedding** (Ollama local) | **0.9s** | 8/8 embedded |

## Timing Comparison Across Attempts

| Component | Attempt 1 | Attempt 2 | Attempt 3 |
|-----------|-----------|-----------|-----------|
| Source loading | 0.025s (fail) | 0.02s | 0.03s |
| Structure stage | N/A | 1.6s (degraded) | 49.9s |
| Orchestrator | N/A | SKIPPED | 21.0s |
| Extract/Validate | N/A | 8.5s (fail) | ~0s |
| Store | N/A | N/A | 0.3s |
| Embed | N/A | N/A | 0.9s |
| **Total** | **0.025s** | **10.1s** | **75.56s** |

## Recommendations

### P1 - Fix Race Condition
Ensure `acm_extract` runs AFTER `process_source` completes. Current behavior dispatches both simultaneously.

### P2 - Fix SiteConfig Schema
The `site_config.source_id` field type mismatch (`record<source>` vs string) causes a non-blocking error during auto-fill.

### P3 - Investigate Record Count
Only 8/31 records extracted (26%), consistent with previous E2E test (2026-02-10). Missing negative results and some positive/assumed positive records. This is likely an extraction prompt/logic issue, not an infrastructure problem.

### P4 - Fix Page Count in Pipeline Init
Pipeline reports "0 pages" at init but structure stage correctly identifies 12 pages later. The page count should be populated earlier.

### RESOLVED - Model Configuration
Fixed by team lead during this test. Direct Anthropic API model now configured in SurrealDB default models. OpenRouter model was returning 404.

## Files Analyzed
- Worker log: `/tmp/acm-worker.log` (1316 lines captured)
- Source ID: `source:lap4wnbxllavswdgghro`
- Commands:
  - `command:3a0z8miac0y9wrqh4hxj` (process_source) - SUCCEEDED (38.28s)
  - `command:ih3kl9ztean6zyma17eq` (acm_extract attempt 1) - FAILED (no text)
  - `command:2efksp566r109nwnhx5h` (acm_extract attempt 2) - FAILED (model 404)
  - `command:xutxhvpo7aowse1v3iyq` (acm_extract attempt 3) - **SUCCEEDED** (75.56s, 8 records)
