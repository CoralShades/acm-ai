# Session: Audit ACM extraction pipeline generalizability across 3 PDF formats — run extractions, compare against ground truth, diagnose format gaps

## Skills to Load

/systematic-debugging — structured diagnosis for extraction failures
/planning-with-files — persistent markdown plan for session continuity
/verification-before-completion — verify findings before claiming audit complete
/benchmark-compare — compare extraction results across runs

---

## Prerequisites

Before starting this session, verify:

- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`
- Worker running: check logs or `curl http://localhost:5055/api/commands/status`
- Branch: ACMV3
- Migration 51 applied: `FLEXIBLE TYPE option<object>` on `docling_document_json` (run API restart if needed — auto-applies migrations)
- Sample PDFs exist:
  - `D:/ailocal/acm-ai/docs/samplePDF/Clucth_Alexander_District_Hospital.pdf` (Greencap, 5 buildings, 43 items)
  - `D:/ailocal/acm-ai/docs/samplePDF/4601_AsbestosRegister.pdf` (NSW DoE SAMP, 10 buildings, 4 items)
  - `D:/ailocal/acm-ai/docs/samplePDF/3980_AsbestosRegister.pdf` (unknown format, no ground truth)
- Ground truth files exist:
  - `D:/ailocal/acm-ai/benchmarks/ground_truth/alexander.json` (43 records, 5 buildings)
  - `D:/ailocal/acm-ai/benchmarks/ground_truth/aldavilla_4601.json` (4 records, 10 buildings)
- Sources already uploaded:
  - Alexander Hospital: `source:3dt8aixydmc80cm6flfp` (17 tables extracted, 0 records, 0 buildings)
  - Aldavilla 4601: `source:qdbz3uhlthja8enqxbm6` (0 tables, 0 records)
  - 3980 Register: `source:iyklekqc55w11kiovdwu` (25 tables extracted, 1 building, 0 records)

---

## Project Glossary

Key terms for this session. Refer to these definitions when interpreting code or instructions.

| Term | Definition |
|------|-----------|
| Building__c | Salesforce object for a physical building. The pipeline produces one `BuildingRecord` per building. |
| Item__c | Salesforce object for an individual ACM sample. Maps to `ACMExtractionRecord`. |
| ExtractionState | LangGraph TypedDict carrying all data between pipeline nodes: source metadata, docling tables, building cache, records. |
| SAMP | School Asbestos Management Plan — the source PDF. Contains survey results for one or more buildings. |
| ARA | Asbestos Risk Assessment — an alternative report format used by some consultants (e.g., Greencap). Structurally similar to SAMP but with different page layout and table formats. |
| Per-row extraction | One LLM call per table row → 13 fields → deterministic post-processing. Requires `docling_document_json`. |
| Bulk extraction | One LLM call per building chunk, all items at once. Fallback when no Docling JSON available. |
| `docling_document_json` | Lossless cell-level JSON from Docling's `table.data.model_dump(mode="json")`. Stored in `acm_table_section`. Fixed by migration 51 (`FLEXIBLE`). |
| Ground truth | Manually extracted reference data in `benchmarks/ground_truth/`. Used for recall/precision measurement. |
| `building_inventory` | LLM-produced inventory of buildings in the document. Contains building names, page ranges, room lists. |
| `metadata_and_structure_node` | First graph node — extracts consultant name, site info, document type, building count. |
| Multi-building PDF | A SAMP containing multiple buildings (e.g., Alexander has 5, Aldavilla has 10). Requires correct building detection and page range assignment. |
| "No Asbestos" building | A building declared as having no ACM. Aldavilla has 9 of these — pipeline must recognize and skip extraction. |
| Skill | Markdown instruction set for Claude Code activated via `/skill-name`. |
| Subagent | Claude Code session spawned via Task tool for parallel work. Model: `sonnet` for complex, `haiku` for simple. |

---

## Current State

- Branch: ACMV3 (latest commit: `f6441995` — fix docling_document_json empty dict, restore per-row extraction)
- Migration 51 applied: `docling_document_json` now uses `FLEXIBLE TYPE option<object>`
- Broadmeadows (Clutch format, 1 building): **33/31 records** via per-row extraction ✅
- Alexander Hospital (Greencap format, 5 buildings): **0 records**, 17 tables extracted, 0 buildings detected
- Aldavilla 4601 (NSW DoE SAMP, 10 buildings): **0 records**, 0 tables extracted
- 3980 Register (unknown format): **0 records**, 25 tables extracted, 1 building detected
- Per-row extraction path: confirmed working (migration 51 fix)
- `ACM_ITEM_EXTRACTION_MODE=per_row` (default)

### Format Differences

| Document | Consultant | Buildings | Items | Table Style | Key Challenges |
|----------|-----------|-----------|-------|-------------|----------------|
| Broadmeadows | Clutch | 1 | 31 | Landscape register table, 18 columns | Single building — simple case ✅ |
| Alexander Hospital | Greencap Pty Ltd | 5 | 43 | Portrait risk assessment tables, per-building sections | Multi-building detection, different column names, building-per-section layout |
| Aldavilla 4601 | Dept of Education NSW | 10 | 4 | SAMP format with building summary grid | 9 buildings "No Asbestos", only B009 has ACM, very sparse data |
| 3980 Register | Unknown | ? | ? | Unknown | 25 tables but 0 records — needs diagnosis |

---

## Key Files

Files this session will read or modify. Verify all paths exist before starting.

**Read (ground truth):**
- `D:/ailocal/acm-ai/benchmarks/ground_truth/alexander.json` — 43 records, 5 buildings, match keys: sample_no primary
- `D:/ailocal/acm-ai/benchmarks/ground_truth/aldavilla_4601.json` — 4 records, 10 buildings, match keys: sample_no primary
- `D:/ailocal/acm-ai/benchmarks/ground_truth/broadmeadows.json` — 31 records (reference baseline)

**Read (pipeline code — format handling):**
- `D:/ailocal/acm-ai/open_notebook/graphs/acm_extraction.py` — graph definition, all nodes
- `D:/ailocal/acm-ai/open_notebook/extractors/metadata_and_structure.py` — metadata LLM prompt (building count detection)
- `D:/ailocal/acm-ai/open_notebook/extractors/building_inventory.py` — building inventory LLM prompt (page ranges)
- `D:/ailocal/acm-ai/open_notebook/extractors/document_structure.py` — document structure model
- `D:/ailocal/acm-ai/open_notebook/extractors/orchestrator.py` — `_get_docling_tables()` page range query
- `D:/ailocal/acm-ai/open_notebook/extractors/row_segmenter.py` — `COLUMN_ALIASES` (column name matching)
- `D:/ailocal/acm-ai/open_notebook/extractors/row_extractor.py` — per-row LLM extraction
- `D:/ailocal/acm-ai/commands/source_commands.py` — Docling extraction + table storage

**Read (prompts — format sensitivity):**
- `D:/ailocal/acm-ai/prompts/acm/metadata_and_structure.jinja` — metadata prompt template
- `D:/ailocal/acm-ai/prompts/acm/building_inventory.jinja` — building inventory prompt template
- `D:/ailocal/acm-ai/prompts/acm/row_extraction.jinja` — per-row extraction prompt template

**Read (PDF samples):**
- `D:/ailocal/acm-ai/docs/samplePDF/Clucth_Alexander_District_Hospital.pdf` — 5-building ARA
- `D:/ailocal/acm-ai/docs/samplePDF/4601_AsbestosRegister.pdf` — 10-building SAMP
- `D:/ailocal/acm-ai/docs/samplePDF/3980_AsbestosRegister.pdf` — unknown format

**Write (output):**
- `D:/ailocal/acm-ai/docs/sprint-artifacts/multi-format-audit/task_plan.md`
- `D:/ailocal/acm-ai/docs/sprint-artifacts/multi-format-audit/findings.md`
- `D:/ailocal/acm-ai/docs/sprint-artifacts/multi-format-audit/progress.md`

---

## Plan

Read `docs/sprint-artifacts/multi-format-audit/task_plan.md` before starting. Update it as you work.

### Task Plan Reference

- task_plan.md: `D:/ailocal/acm-ai/docs/sprint-artifacts/multi-format-audit/task_plan.md`
- findings.md: `D:/ailocal/acm-ai/docs/sprint-artifacts/multi-format-audit/findings.md`
- progress.md: `D:/ailocal/acm-ai/docs/sprint-artifacts/multi-format-audit/progress.md`

### Execution Strategy

**Phase 1 — Baseline Assessment (READ ONLY)**

Step 1: Read all 3 ground truth files. Document expected buildings, records, and match keys for each.

Step 2: For each source, query SurrealDB to understand current state:
```sql
-- Per source: tables, buildings, records, docling_json status
SELECT source_id, count() AS n FROM acm_table_section GROUP BY source_id;
SELECT source_id, count() AS n FROM building_record GROUP BY source_id;
SELECT source_id, count() AS n FROM acm_record GROUP BY source_id;

-- Check docling_document_json population
SELECT source_id,
  count(docling_document_json != {} AND docling_document_json IS NOT NONE) AS has_json,
  count(docling_document_json = {} OR docling_document_json IS NONE) AS missing_json
FROM acm_table_section GROUP BY source_id;
```

Step 3: For the 3980 source (25 tables, 0 records), investigate why extraction produced no output:
- Check `source_intelligence` for metadata/building inventory results
- Check if building_record exists but has wrong page ranges
- Check worker logs for errors during extraction

**Phase 2 — Run Extractions**

Step 4: Run force=true extraction on Alexander Hospital:
```bash
curl -X POST http://localhost:5055/api/acm/extract \
  -H 'Content-Type: application/json' \
  -d '{"source_id": "source:3dt8aixydmc80cm6flfp", "force": true}'
```
Monitor command status. Wait for completion.

Step 5: Run force=true extraction on Aldavilla 4601:
```bash
curl -X POST http://localhost:5055/api/acm/extract \
  -H 'Content-Type: application/json' \
  -d '{"source_id": "source:qdbz3uhlthja8enqxbm6", "force": true}'
```
Monitor command status. Wait for completion.

Step 6: Run force=true extraction on 3980 (diagnostic — no ground truth):
```bash
curl -X POST http://localhost:5055/api/acm/extract \
  -H 'Content-Type: application/json' \
  -d '{"source_id": "source:iyklekqc55w11kiovdwu", "force": true}'
```

**Phase 3 — Results Analysis**

Step 7: For each source, after extraction completes:

a) **Building detection accuracy**:
```sql
SELECT id, building_name, internal_id, page_start, page_end
FROM building_record WHERE source_id = $sid;
```
Compare against ground truth building count and names.

b) **Record count and field population**:
```sql
SELECT count() AS total FROM acm_record WHERE source_id = $sid GROUP ALL;
SELECT id, building_id, room_name, location, product, sample_no, sample_result, friable, area_type
FROM acm_record WHERE source_id = $sid ORDER BY building_id, room_name LIMIT 20;
```

c) **Per-row path verification**:
```sql
-- Check if docling_document_json was populated for new tables
SELECT id, page_start,
  array::len(docling_document_json.table_cells) AS cell_count
FROM acm_table_section
WHERE source_id = $sid AND table_type = 'docling_direct_api';

-- Check data_issues for row_index markers (per-row evidence)
SELECT id, data_issues FROM acm_record WHERE source_id = $sid LIMIT 5;
```

d) **Field mapping accuracy**: Compare extracted field names against ground truth match keys. Are `building_name`, `room_name`, `location`, `product`, `sample_no`, `sample_result`, `friable` populated?

**Phase 4 — Ground Truth Comparison**

Step 8: For Alexander Hospital (43 expected records):
- Match by `sample_no` (primary key)
- For each ground truth record, check if a matching `acm_record` exists
- Calculate: true positives, false negatives, false positives
- Calculate recall: TP / (TP + FN), precision: TP / (TP + FP)
- Document which records were missed and why

Step 9: For Aldavilla 4601 (4 expected records, 10 buildings):
- Check if all 10 buildings were detected
- Check if "No Asbestos" buildings were correctly handled (no ACM records created)
- Match the 4 expected records by building_name + room_name + product
- Document building detection gaps

**Phase 5 — Format Gap Analysis**

Step 10: For each format, document:
- What worked well
- What failed (specific file:line if pipeline code issue)
- Whether the failure is in: (a) Docling table extraction, (b) metadata/structure LLM, (c) building inventory LLM, (d) per-row extraction LLM, (e) field mapping/normalization, (f) SurrealDB storage
- Whether the gap is fixable via prompt tuning, code change, or architectural change
- Column name variations: does `COLUMN_ALIASES` in `row_segmenter.py` cover the new format's column headers?

Step 11: Create a format compatibility matrix:

| Capability | Broadmeadows (Clutch) | Alexander (Greencap) | Aldavilla (NSW DoE) | 3980 (Unknown) |
|------------|----------------------|---------------------|--------------------|--------------------|
| Building detection | | | | |
| Page range assignment | | | | |
| Table extraction (Docling) | | | | |
| docling_document_json populated | | | | |
| Per-row extraction triggers | | | | |
| Field mapping correct | | | | |
| Record count vs ground truth | | | | |
| sample_no match rate | | | | |

---

## Agent Strategy

Strategy: SUBAGENT-DISPATCH
Use the Task tool to dispatch independent investigation and extraction runs.
**All subagents should use `model: "sonnet"` for team-based work.**

### Phase 1-2 Subagents (launch sequentially — extractions depend on baseline)

Run Phase 1 (baseline assessment) in main session, then dispatch extractions.

### Phase 3-4 Subagents (launch in parallel after extractions complete)

**Subagent 1: alexander-analyzer**
- Model: sonnet
- Task: Query SurrealDB for Alexander Hospital results. Compare buildings and records against `benchmarks/ground_truth/alexander.json`. Calculate recall/precision. Document field mapping gaps. Check if per-row path triggered. Return structured comparison table.

**Subagent 2: aldavilla-analyzer**
- Model: sonnet
- Task: Query SurrealDB for Aldavilla 4601 results. Verify all 10 buildings detected. Check "No Asbestos" handling. Compare 4 expected records against `benchmarks/ground_truth/aldavilla_4601.json`. Return structured comparison table.

**Subagent 3: format-gap-auditor**
- Model: sonnet
- Task: Read `row_segmenter.py` COLUMN_ALIASES, `metadata_and_structure.jinja`, `building_inventory.jinja`, `row_extraction.jinja`. Check if these prompts and column mappings are format-specific (Clutch-only) or generalizable. Identify hardcoded assumptions. Return structured gap list with file:line references.

---

## Verification Checklist

Run these checks before marking the session complete. All must pass.

- [ ] **Alexander Hospital extraction complete**: command status = `completed`, no errors
- [ ] **Alexander building detection**: ≥4/5 buildings detected (ground truth: Myrtle Street Clinic, Mortuary Buildings, Boiler House, Amenities Block, Main Hospital)
- [ ] **Alexander record count**: ≥35/43 records extracted (≥80% recall)
- [ ] **Alexander field mapping**: `sample_no`, `sample_result`, `building_name`, `product` populated on ≥80% of records
- [ ] **Aldavilla extraction complete**: command status = `completed`, no errors
- [ ] **Aldavilla building detection**: ≥8/10 buildings detected
- [ ] **Aldavilla "No Asbestos" handling**: ≤1 record per "No Asbestos" building (9 buildings should produce 0 items)
- [ ] **Aldavilla record count**: ≥3/4 records extracted
- [ ] **3980 extraction complete**: some records extracted (diagnostic — no ground truth)
- [ ] **docling_document_json**: populated (not `{}`) for all new tables across all 3 extractions
- [ ] **Per-row path**: triggered for at least 1 of the 3 new extractions (check `row_index:` in `data_issues`)
- [ ] **Format compatibility matrix**: completed in `findings.md`
- [ ] **Gap list**: documented with file:line references and fix recommendations
- [ ] No test regressions: `uv run pytest tests/ -x` passes

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| READ | ~18 | Ground truth JSONs, pipeline code, prompts, sample PDFs |
| MODIFY | 0 | This is an AUDIT session — read-only investigation unless fixes identified |
| NEW | 3 | multi-format-audit/task_plan.md, findings.md, progress.md |
| DELETE | 0 | — |

---

## Commit Template

When work is complete, use this commit message structure:

```
docs(extraction): multi-format pipeline audit — Alexander, Aldavilla, 3980

Tested pipeline against 3 PDF formats with ground truth comparison.
Format compatibility matrix: [FILL — e.g., 2/3 formats pass, 1 needs prompt tuning].
Key gaps: [FILL — e.g., multi-building detection, column alias coverage].

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

---

## Critical Rules

1. **AUDIT FIRST, FIX LATER** — this session is primarily diagnostic. Document findings before proposing code changes.
2. **Wait for extractions** — each extraction takes 2-5 minutes with Ollama. Monitor command status, don't spam re-extractions.
3. **Ground truth is authoritative** — if the pipeline disagrees with ground truth, the pipeline is wrong (unless the ground truth has a documented error).
4. **Per-source analysis** — analyze each source independently. Don't aggregate results across formats until Phase 5.
5. **Column aliases matter** — the `COLUMN_ALIASES` dict in `row_segmenter.py` may only cover Clutch format column headers. New formats may need additional aliases.
6. **Multi-building is the hard case** — single-building PDFs are "easy mode". The real test is whether `building_inventory` correctly identifies 5 or 10 buildings with accurate page ranges.
7. **"No Asbestos" is a valid result** — Aldavilla has 9 buildings with no ACM. The pipeline should detect these and NOT create phantom records.
8. **File:line references** — all findings must cite specific code locations for actionable follow-up.

---

## Quick-Start Commands

```bash
# 1. Confirm services
curl http://localhost:5055/health
docker ps | grep acm-ai-db

# 2. Check current extraction state
curl -s -X POST http://localhost:8000/sql \
  -H "surreal-ns: open_notebook" -H "surreal-db: development" \
  -u "root:root" \
  -d "SELECT source_id, count() AS n FROM acm_record GROUP BY source_id;"

# 3. Trigger Alexander extraction
curl -X POST http://localhost:5055/api/acm/extract \
  -H 'Content-Type: application/json' \
  -d '{"source_id": "source:3dt8aixydmc80cm6flfp", "force": true}'

# 4. Monitor extraction status
curl -s -X POST http://localhost:8000/sql \
  -H "surreal-ns: open_notebook" -H "surreal-db: development" \
  -u "root:root" \
  -d "SELECT id, status, error FROM command ORDER BY created DESC LIMIT 3;"
```
