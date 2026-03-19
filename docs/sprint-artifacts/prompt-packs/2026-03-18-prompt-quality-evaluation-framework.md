# Session: Build a prompt evaluation framework and systematically improve extraction prompt quality against ground truth

## Skills to Load

/planning-with-files — persistent markdown plan for session continuity
/prompt-engineering — optimize extraction prompts for quality
/systematic-debugging — structured diagnosis of prompt failures
/acm-observability — Langfuse/LangSmith trace analysis reference
/dogfood — E2E exploration with real extraction runs
/verification-before-completion — verify work before claiming done

---

## Prerequisites

Before starting this session, verify:

- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`
- Worker running: check for `run_worker.py` process
- Branch: `git checkout ACMV3`
- Ground truth CSVs exist or can be created from:
  - Broadmeadows: 31 records (docs/reviews/e26-s4-validation-results.md)
  - Alexander: 43 records (docs/reviews/e28-validation-results.md)
- Test PDFs available in `docs/samplePDF/`
- Langfuse running: `curl http://localhost:3000` (optional but recommended)
- Consider installing: `npx skills add hamelsmu/evals-skills@eval-audit -g -y`

---

## Project Glossary

| Term | Definition |
|------|-----------|
| Building__c | Salesforce object for a physical building. Extraction produces one `BuildingRecord` per building |
| Item__c | Salesforce object for individual ACM sample. Maps to `ACMExtractionRecord` (13 required fields) |
| Per-row extraction | v3.5 mode: one LLM call per table row → 9 fields (`ACMItemRow`) → mapper → `ACMExtractionRecord` |
| Bulk extraction | Original V3 mode: one LLM call per building, all items at once (13 fields) |
| Ground truth | Known-correct extraction results for benchmark PDFs (Broadmeadows 31, Alexander 43) |
| KV prompt | Key-value prompt template for per-row extraction (`prompts/acm/row_extraction.jinja`) |
| SF picklist normalization | Mapping raw text to valid Salesforce picklist options via `SalesforcePicklistValidator` |
| TruncationError | Custom ValueError subclass raised when LLM output appears truncated. Triggers cloud model retry |
| Correction loop | `correct_node` re-validates and re-extracts low-confidence records |
| Skill | Markdown instruction set for Claude Code activated via `/skill-name` |
| Subagent | Claude Code session spawned via Task tool for parallel work |
| Plan mode | Session reads/writes `task_plan.md` to prevent scope creep |

---

## Current State

- Branch: ACMV3
- Ground truth varies by run: Broadmeadows 28-31/31, Alexander 36-43/43
- No automated prompt evaluation pipeline exists
- LangSmith playground used ad-hoc for prompt iteration
- Per-row (9 fields) vs bulk (13 fields) creates field coverage gap
- Ollama models (qwen2.5) don't reliably follow JSON instructions
- 3 prompt rewrites already done (metadata 141→56 lines, inventory 130→58, row_split 3→15)
- `format="json"` added to Ollama ChatOllama but not all models comply

---

## Key Files

**Read (reference):**
- `prompts/acm/metadata_extraction.jinja` — metadata extraction prompt
- `prompts/acm/building_inventory.jinja` — building inventory prompt
- `prompts/acm/building_extraction.jinja` — building extraction prompt (bulk mode)
- `prompts/acm/row_extraction.jinja` — per-row KV extraction prompt
- `prompts/acm/row_split.jinja` — row split/segmentation prompt
- `open_notebook/extractors/row_extractor.py` — per-row extraction logic
- `open_notebook/graphs/acm_extraction.py` — extraction graph (where prompts are invoked)
- `open_notebook/domain/acm_row_schemas.py` — ACMItemRow (9 fields)
- `open_notebook/domain/acm.py` — ACMExtractionRecord (full SF schema)
- `docs/reviews/e26-s4-validation-results.md` — Broadmeadows ground truth
- `docs/reviews/e28-validation-results.md` — Alexander ground truth

**Modify:**
- `prompts/acm/*.jinja` — improve prompt templates based on evaluation
- `open_notebook/extractors/row_extractor.py` — adjust extraction logic if needed

**Create:**
- `scripts/eval/prompt_eval_harness.py` — automated prompt evaluation runner
- `scripts/eval/ground_truth/broadmeadows.csv` — ground truth CSV (31 records)
- `scripts/eval/ground_truth/alexander.csv` — ground truth CSV (43 records)
- `tests/test_prompt_eval.py` — test that evaluation harness runs and scores

---

## Plan

### Approach

1. **Create ground truth CSVs** — Extract from validation reports into structured CSV with all 13 SF Item__c fields
2. **Build evaluation harness** — Python script that:
   - Runs extraction on a test PDF
   - Compares output to ground truth CSV
   - Scores: exact match, fuzzy match (Levenshtein), field-level accuracy, record-level recall
   - Outputs: per-field accuracy matrix, overall score, regression comparison
3. **Baseline current prompts** — Run eval harness on current prompts, record scores
4. **Systematic prompt improvement** — For each low-scoring field:
   - Analyze LangSmith traces for failure patterns
   - Identify prompt weaknesses (ambiguity, missing examples, wrong output format)
   - Iterate prompt, re-run eval, compare scores
5. **Ollama-specific optimization** — Test with `llama3.1:8b`, `qwen2.5:7b`, `qwen2.5:32b`:
   - Verify `format="json"` compliance
   - Adjust prompt structure for smaller context windows
   - Test per-row vs bulk modes per model
6. **Regression gate** — Ensure no prompt change drops below baseline score

### Task Plan Reference
- task_plan.md: `docs/sprint-artifacts/pipeline-audit-2026-03-18/task_plan.md`
- findings.md: `docs/sprint-artifacts/pipeline-audit-2026-03-18/findings.md`
- progress.md: `docs/sprint-artifacts/pipeline-audit-2026-03-18/progress.md`

---

## Agent Strategy

Strategy: SOLO
Run all steps in sequence in a single Claude Code session.
Prompt evaluation requires iterative test-edit-retest loops that benefit from continuous context.

Optional: dispatch a background subagent to run extraction while you analyze traces:
- extraction-runner: Run extraction on Broadmeadows, save output for eval
- trace-analyzer: Query Langfuse/LangSmith for LLM call details

---

## Context7 Directives

Run these at session start to load current library documentation:

1. resolve-library-id for "langchain" → query-docs for "prompt template jinja2 structured output"
2. resolve-library-id for "pydantic" → query-docs for "model_validate field_validator json schema"

---

## Verification Checklist

- [ ] Ground truth CSVs created: `scripts/eval/ground_truth/broadmeadows.csv` (31 records), `alexander.csv` (43 records)
- [ ] Eval harness runs: `uv run python scripts/eval/prompt_eval_harness.py --pdf docs/samplePDF/Clutch_Broadmeadows_2.pdf`
- [ ] Baseline scores recorded in findings.md
- [ ] At least 1 prompt improvement tested with measurable score increase
- [ ] No regression below baseline for any field
- [ ] `uv run ruff check .` — lint clean
- [ ] `uv run pytest tests/test_prompt_eval.py -v` — eval test passes

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| READ | 11 | 5 prompt templates, row_extractor.py, acm_extraction.py, acm_row_schemas.py, acm.py, 2 validation reports |
| MODIFY | 2-5 | prompts/acm/*.jinja (based on eval results), row_extractor.py |
| NEW | 4 | prompt_eval_harness.py, broadmeadows.csv, alexander.csv, test_prompt_eval.py |

---

## Commit Template

```
feat(eval): add prompt evaluation framework with ground truth scoring

- Create evaluation harness for automated prompt quality assessment
- Add ground truth CSVs for Broadmeadows (31) and Alexander (43) benchmarks
- Baseline current prompts: [SCORE]% overall accuracy
- Improve [FIELD] prompts: [OLD]% → [NEW]% accuracy

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```
