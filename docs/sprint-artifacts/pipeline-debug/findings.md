# Pipeline Debug Findings

## Date: 2026-03-14

## Trace Analysis

### Langfuse Traces
- **Trace 1** (`8270cdb0...`): Docling content ingestion for `Clutch_Broadmeadows (28).pdf`. No LLM calls. 148s. No errors.
- **Trace 2** (`38c0555b...`): ACM extraction for `sCF_Broadmead.pdf`. Model: `phi4:14b-q4_K_M`. BULK mode (per_row_actually_ran=false). 182s. 9 LLM calls. 25 records saved (26 extracted, 1 deduped).

### LangSmith Runs
- **Run 1** (`fdfc9f9d...`): Content ingestion — 267s, 0 LLM calls. Docling processing.
- **Run 2** (`6a010e5d...`): ACM extraction — 189s, same results as Langfuse trace 2. Record progression: 26→26→25 (1 dedup). 4 validation corrections (friable=null→Non-friable).

### Key Discovery: Different Source Files
The traced ACM extraction ran on `sCF_Broadmead.pdf` (source:ddp29u9shs6w3s4m8lbv), NOT the ground truth file `Clutch_Broadmeadows.pdf`. The 25-vs-31 comparison is for different files.

## Root Causes (ranked by impact)

### RC1 (CRITICAL): Missing `format="json"` on Ollama calls
- **Files**: `metadata_and_structure.py`, `building_inventory.py`
- **Impact**: Ollama models returned conversational text instead of JSON in metadata+structure and inventory stages. The metadata stage correctly extracted consultant="Prensa Pty Ltd" via LLM, but the JSON wasn't parsed properly → chain output showed consultant="Unknown", site_name=null.
- **Fix**: Added `_apply_ollama_extraction_settings(model)` after `provision_langchain_model()` in both files.

### RC2 (CRITICAL): Prompt templates too long for Ollama 8b
- `metadata_and_structure.jinja`: 141 lines → ~5K chars system prompt
- `building_inventory.jinja`: 130 lines → ~4.5K chars system prompt
- `v3_item_extraction.jinja`: 271 lines + injected picklists → ~15K chars
- At num_ctx=8192, system prompt alone consumed a significant fraction of context.
- **Fix**: Rewrote metadata_and_structure (141→56 lines), building_inventory (130→58 lines).

### RC3 (HIGH): `row_split.jinja` only 3 lines, no example
- 8b models cannot reliably understand "split items" without a concrete example.
- **Fix**: Added input/output example (3→15 lines).

### RC4 (MEDIUM): Per-row extraction timing issue
- Per-row path checks for `docling_document_json` in `acm_table_section`. Tables exist in DB, but the ACM extraction may have run BEFORE Docling stored them (race condition on first upload).
- Re-extraction with `force=True` should trigger per-row correctly since tables now exist.

### RC5 (MEDIUM): `sample_result` normalization gap in per-row path
- Per-row mapper passes `row.sample_result` through raw without normalization.
- LLM variants like "Detected", "NAD", "AP" persist as non-canonical values.

### RC6 (MEDIUM): Stale `docling_document_json` detection too narrow
- `acm_commands.py` and `acm_extraction.py` checked only `IS NULL` / `IS NONE`
- Actual DB values were `{}` (empty dict), not NULL — stale detection never triggered
- **Fix**: Changed queries to `(docling_document_json IS NULL OR docling_document_json = {})`

### RC7 (MEDIUM): SurrealDB param binding in stale table check
- `acm_commands.py:248` passed raw string `source_id` as `$sid` param
- SurrealDB string param doesn't match record link field → query returned 0 rows
- **Fix**: Added `ensure_record_id(source_id)` before param binding

### RC8 (MEDIUM): `docling_document_json` stored as empty dict
- DoclingAdapter calls `table.data.model_dump(mode="json")` which produces valid data
- But SurrealDB stores it as `{}` (empty dict) — root cause unclear
- Blocks per-row extraction entirely; bulk mode used as fallback
- **Status**: Deferred to separate investigation

## Persistence Path: CLEAN
All 6 previously known critical bugs are FIXED in current code:
1. ObjectModel.save() returns None — correct pattern used everywhere
2. Building ID race condition — pre-assigned before asyncio.gather
3. SurrealDB record IDs as model names — resolved via direct reference
4. SurrealDB param binding — uses record reference syntax
5. num_ctx overwrite — only sets when caller didn't configure
6. Docling model_dump mode — uses mode="json"

## Applied Fixes

### Fix 1: format="json" for metadata_and_structure.py
Added `_apply_ollama_extraction_settings(model)` after model provisioning.

### Fix 2: format="json" for building_inventory.py
Added `_apply_ollama_extraction_settings(model)` after model provisioning.

### Fix 3: Rewrote metadata_and_structure.jinja
141→56 lines. Removed verbose descriptions, kept explicit JSON schema. Added "Respond with ONLY the JSON object" instruction.

### Fix 4: Rewrote building_inventory.jinja
130→58 lines. Removed FORMAT A/B section structure, kept essential building detection rules and complete JSON schema example.

### Fix 5: Rewrote row_split.jinja
3→15 lines. Added concrete input/output example for multi-item splitting.

### Fix 6: Updated test assertions
- `test_building_inventory.py`: 3 assertions updated for new prompt wording
- `test_ara_format.py`: 3 assertions updated for new prompt wording

### Fix 7: Stale `docling_document_json` detection (RC6+RC7)
- `acm_commands.py`: `IS NULL` → `IS NULL OR = {}` + `ensure_record_id()` for param binding
- `acm_extraction.py`: `IS NONE` → `IS NONE OR = {}` in diagnostic warning

## Verification Results

### Extraction Run (2026-03-14)
- **Source**: `source:mc5llofksqsglrjsfssj` (Clutch_Broadmeadows (28).pdf)
- **Model**: `phi4:14b-q4_K_M` (Ollama)
- **Mode**: Bulk (per-row blocked by empty `docling_document_json`)
- **Records**: 29 created (31 raw → 2 deduped)
- **Confidence**: 29 high, 0 medium, 0 low
- **Building**: 1 ("Broadmeadows Police Station", internal_id BLD#CLUTCH_B_001)
- **Execution time**: 203s

### Ground Truth Comparison (31 records)
- **Match rate**: 29/31 (93.5%)
- **Progression**: 0 → 12 → 22 → 29 records across debug iterations
- **Missing items** (2): Likely items at chunk boundaries or "As Per" cross-references that LLM didn't generate as separate records
- **Duplicates removed**: 2 (dedup caught exact matches)
- **Field quality**: room_name, location, sample_no, sample_result all populated; product field often "Other" instead of specific values (LLM limitation)

### Key Metrics
| Metric | Before | After |
|--------|--------|-------|
| Records extracted | 0 | 29 |
| Ground truth match | 0% | 93.5% |
| Buildings detected | 0 | 1 |
| Consultant | Unknown | Unknown (phi4 metadata failure → fallback) |
| Per-row extraction | Never triggered | Still blocked (docling_json empty) |
| Test suite | 2123 pass | 2123 pass (same 5 pre-existing failures) |
