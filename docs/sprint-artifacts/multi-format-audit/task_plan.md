# Task Plan: Multi-Format Extraction Pipeline Audit
Date: 2026-03-14
Status: PARTIALLY COMPLETE (blocked by F8 concurrent extraction hang)

## Goal

Test ACM extraction pipeline against 3 PDF formats (Greencap ARA, NSW DoE SAMP, unknown register) and compare against ground truth. Identify format-specific gaps in building detection, per-row extraction, and field mapping.

## Steps

### Phase 1 — Baseline Assessment
- [x] 1.1 Read ground truth files (alexander.json, aldavilla_4601.json)
- [x] 1.2 Query SurrealDB for current extraction state per source
- [x] 1.3 Investigate 3980 source (25 tables, 0 records) — why no output?

### Phase 2 — Run Extractions
- [x] 2.1 Run force=true extraction on Alexander Hospital (source:3dt8aixydmc80cm6flfp) — COMPLETED, 0 records
- [~] 2.2 Run force=true extraction on Aldavilla 4601 (source:qdbz3uhlthja8enqxbm6) — STUCK
- [~] 2.3 Run force=true extraction on 3980 (source:iyklekqc55w11kiovdwu) — STUCK

### Phase 3 — Results Analysis
- [x] 3.1 Alexander: building detection accuracy (10 detected, 5 expected — FAIL)
- [x] 3.2 Alexander: record count and field population (0/43 — COMPLETE FAILURE)
- [x] 3.3 Alexander: per-row path verification (never triggered)
- [~] 3.4 Aldavilla: building detection accuracy (10/10 count correct, names wrong) — BLOCKED
- [~] 3.5 Aldavilla: record count (extraction stuck) — BLOCKED
- [~] 3.6 3980: diagnostic analysis (extraction stuck) — BLOCKED

### Phase 4 — Ground Truth Comparison
- [x] 4.1 Alexander: 0/43 recall, N/A precision
- [~] 4.2 Aldavilla: match by building_name + room_name + product — BLOCKED
- [~] 4.3 Document false negatives and false positives per source — PARTIALLY BLOCKED

### Phase 5 — Format Gap Analysis
- [x] 5.1 Per-format findings with file:line references (11 findings, 6 gaps)
- [x] 5.2 Column alias coverage check (row_segmenter.py COLUMN_ALIASES)
- [x] 5.3 Prompt template format sensitivity check
- [x] 5.4 Format compatibility matrix (partial — Aldavilla/3980 extraction data pending)
- [x] 5.5 Fix recommendations (8 priorities documented)

## Risks

- [REALIZED] Ollama extraction slow — phi4:14b used instead of llama3.1:8b (F7)
- [REALIZED] Multi-building detection fails for Greencap format (F2)
- [REALIZED] SAMP format page ranges not differentiated (F5, F11)
- [NEW] Concurrent extraction hangs pipeline (F8)

## Command IDs

| Source | Command | Status |
|--------|---------|--------|
| Alexander (first attempt) | command:d90q864mzaj4n4fq91y9 | Completed (file not found) |
| Alexander (retry) | command:geza6d81p0m3hg2fwbb4 | Completed (0 records) |
| Aldavilla | command:ie2pge2fefddd19tnnjo | STUCK (40+ min) |
| 3980 | command:axl8yv96fuinf9yg3rns | STUCK (40+ min) |
