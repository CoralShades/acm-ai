# Findings — E27-S4: Native JSON Schema Structured Outputs

## Spike Results (2026-02-28)

### completionState Wrapper: CONFIRMED GONE
- **0** occurrences of `completionState present: True` across 13 parse_json_response calls
- RAW extraction output: `{"records":[{"building_id":"Broadmeadows...` — clean JSON, no wrapper
- Applies to ALL stages: document_structure, building_inventory, page_tagger, extract_records
- Root cause confirmed: wrapper was a non-Anthropic provider routing artifact (E27-S3 fixed routing)

### Broadmeadows: 31/31 (100%) PASS
- Duration: 139.6s (down from ~220s baseline — ~80s improvement)
- Records #9, #30, #31 all found
- 31 extracted + 1 merged duplicate + 2 no-access recovered = 32 saved

### Alexander: 29/43 (67.4%) REGRESSION
- 14 missing records — mostly "Not Sampled" fire doors, shower cubicles
- Root cause: `response_format: json_schema` with `strict: True` on legacy `acm_extraction.py` path
- Alexander uses ARA format (Greencap) — different structure from SAMP
- Strict schema constrains LLM output too tightly for ARA format diversity

### Architecture Decision: Split response_format by Path

| Path | response_format | Rationale |
|------|----------------|-----------|
| Orchestrator (`orchestrator.py`) | YES — `_inject_response_format()` | SAMP format, structured building sections, benefits from schema enforcement |
| Legacy (`acm_extraction.py`) | NO — pure `ainvoke() + parse_json_response() + Pydantic` | ARA format diversity, strict schema too constraining |

This is the correct split because:
1. Orchestrator handles per-building extraction with known structure (SAMP)
2. Legacy path handles whole-document extraction (ARA, mixed formats)
3. `parse_json_response()` + `_normalize_extraction_json()` + Pydantic validation still enforce schema post-hoc

### Call Sites Audit (pre-cleanup)

| # | File | Line | Action |
|---|------|------|--------|
| DEF | `utils.py` | ~492 | DELETE function |
| 1 | `orchestrator.py` | ~557 | REMOVE call (keep _inject_response_format) |
| 2 | `orchestrator.py` | ~623 | REMOVE call |
| 3 | `document_structure.py` | 170 | REMOVE call + import |
| 4 | `building_inventory.py` | 504 | REMOVE call + import |
| 5 | `page_tagger.py` | 381 | REMOVE call + import |
| 6 | `acm_extraction.py` | ~1307 | REMOVE call (also remove _inject_response_format) |
| 7 | `acm_extraction.py` | ~1456 | REMOVE call |

### Non-Extraction Stages — Pre-existing Issues (Not E27-S4 scope)
- `document_structure`: LLM returned prose instead of JSON → heuristic fallback (pre-existing)
- `building_inventory`: 17 validation errors → heuristic fallback (pre-existing)
- `page_tagger`: Missing field → heuristic fallback (pre-existing)
- These fallbacks work correctly. Not introduced by E27-S4 changes.
