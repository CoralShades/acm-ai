# RAG Disposition Research: E1-S14 and E1-S15

**Date:** 2026-04-11
**Constraint:** "Only literal values from the PDF + deterministic mapping from a controlled vocabulary table. No free-form LLM reasoning. No inference from surrounding context."

---

## Code Locations Found

### E1-S14 — Contextual Embedding Enrichment

| File | Line(s) | Role |
|------|---------|------|
| `open_notebook/domain/acm.py` | 391–394 | `enriched_text: Optional[str]` field on `ACMRecord` |
| `open_notebook/domain/acm.py` | 615 | `get_enriched_embedding_text()` method on `ACMRecord` |
| `open_notebook/domain/acm.py` | 932–934 | `enriched_text` on `ACMExtractionRecord` (intermediate) |
| `api/services/acm_embedding_service.py` | ~34–79 | `embed_records()` now calls `get_enriched_embedding_text()` |
| `open_notebook/extractors/acm_extractor.py` | (post-extraction) | `_enrich_record_dicts()` helper fills `enriched_text` |
| `open_notebook/graphs/acm_extraction.py` | 2909–2910 | `acm_record.enriched_text = acm_record.get_enriched_embedding_text()` in `save_records()` |
| `api/routers/acm.py` | (added endpoint) | `POST /api/acm/re-embed` |
| `migrations/16.surrealql` | — | `DEFINE FIELD enriched_text ON TABLE acm_record TYPE option<string>` |

### E1-S15 — Corrective RAG Validation Loop

| File | Line(s) | Role |
|------|---------|------|
| `open_notebook/graphs/acm_extraction.py` | 171–174 | State fields: `correction_attempt`, `correction_stats`, `enable_corrective_loop`, `max_correction_attempts` |
| `open_notebook/graphs/acm_extraction.py` | 1470 | `validate_records_strict()` node |
| `open_notebook/graphs/acm_extraction.py` | 1705 | `correct_records()` node |
| `open_notebook/graphs/acm_extraction.py` | 1849–1860 | `_apply_field_correction()` — writes `sample_result`, `material_condition`, `friable`, `disturbance_potential` |
| `open_notebook/graphs/acm_extraction.py` | 1863 | `_llm_correct_records()` — LLM correction path |
| `open_notebook/graphs/acm_extraction.py` | 2047 | `should_correct()` router |
| `open_notebook/graphs/acm_extraction.py` | 3060–3061, 3078–3080 | Graph wiring: `validate → should_correct → {correct, deduplicate}` |
| `open_notebook/graphs/acm_extraction.py` | 3217–3226 | Initial state: `enable_corrective_loop: True`, `max_correction_attempts: 2` |
| `open_notebook/domain/acm.py` | 329–349 | `data_issues`, `validation_status`, `validation_errors`, `correction_attempts` fields on `ACMRecord` |
| `open_notebook/extractors/validators/acm_validator.py` | — | Validation logic |
| `prompts/acm/correction.jinja` | — | LLM correction prompt template |

---

## What S14 Writes To

S14 writes only to:
- `ACMRecord.enriched_text` — a secondary text field used exclusively as input to the embedding model (`ACMEmbeddingService.embed_records()`), which produces the `ACMRecord.embedding` vector.
- `ACMRecord.embedding`, `ACMRecord.embedding_text`, `ACMRecord.embedded_at` — standard embedding pipeline fields.

**None of these fields appear in `ITEM_SF_MAPPING` in `open_notebook/extractors/exporters/sf_export.py`** (lines 48–72). The SF export covers `Room_Name__c`, `ACM_Name__c`, `Result__c`, etc. — zero overlap with `enriched_text`, `embedding`, or `embedding_text`.

**Conclusion: S14 writes only to the chat/search layer. It does not touch any Salesforce-bound field.**

---

## What S15 Writes To

S15's `_apply_field_correction()` (line 1849) writes directly to:
- `record.sample_result` → maps to `Sample_Result__c` in `ITEM_SF_MAPPING`
- `record.material_condition` → maps to `Condition__c` in `ITEM_SF_MAPPING`
- `record.friable` → maps to `Friability_of_Material__c` in `ITEM_SF_MAPPING`
- `record.disturbance_potential` → maps to `Disturbance_Potential__c` in `ITEM_SF_MAPPING`

These are all Salesforce-bound fields. When the LLM correction path (`_llm_correct_records`) runs, it calls an LLM to infer a corrected enum value for these fields and writes the result back. The normalizer-only (Layer 1) path is deterministic synonym substitution; the LLM path (Layer 2) is free-form inference.

S15 also writes `correction_attempts` (int, internal), `data_issues` (list of strings, internal), and `validation_status` to `ACMRecord`, but those are metadata fields not in `ITEM_SF_MAPPING`.

**Conclusion: S15's LLM correction path directly modifies four Salesforce-bound enum fields using LLM inference — a direct conflict with the new "no free-form LLM reasoning" rule. The normalizer-only Layer 1 path (synonym mapping) is deterministic and consistent with the rule.**

---

## Feature Flags Present

No environment-level flags exist for either stage:
- No `ENABLE_CONTEXTUAL`, `ENABLE_CORRECTIVE`, `ENABLE_RAG`, `CONTEXTUAL_EMBEDDING`, or `CORRECTIVE_RAG` in `.env`, any `.yaml`, or any `.py` file.
- S15 has a code-level toggle: `enable_corrective_loop: bool` in `ExtractionState`, hardcoded to `True` at line 3225. It can be set to `False` via the state dict to skip the LLM correction path entirely.
- S14 has no toggle at all; it runs unconditionally in `save_records()`.

---

## Sprint Status

From `docs/sprint-artifacts/sprint-status.yaml` (lines 65–66):
```yaml
e1-s14-contextual-embedding-enrichment: done
e1-s15-corrective-rag-validation-loop: done
```

No retrospective entry disables or flags either story as problematic. Both are fully implemented and active in the current production code path.

---

## Recommendation: (C) Keep S14, neuter S15's LLM path via the existing flag

### Justification

S14 (contextual embeddings) produces `enriched_text`, which feeds only the vector search index used by the chat sidebar. It does not touch any Salesforce-bound field and is fully consistent with the "literal values only" rule — it merely concatenates existing structured metadata already on the record. Removing it would degrade chat quality with no extraction correctness benefit.

S15's Layer 1 (normalizer) is also safe to keep: it applies a static synonym table (e.g., `"Bonded" → "Non-friable"`) with no LLM involvement, which is exactly what a "deterministic mapping from a controlled vocabulary table" means. However, S15's Layer 2 (LLM path in `_llm_correct_records`) calls an LLM to infer corrected enum values for `sample_result`, `material_condition`, `friable`, and `disturbance_potential` — four fields that land in Salesforce. This directly violates the new rule.

The safest and lowest-risk action is to set `enable_corrective_loop: False` in the initial state dict (line 3225 of `acm_extraction.py`) OR to surgically remove only the `await _llm_correct_records(...)` call at line 1811, leaving the Layer 1 normalizer loop intact. The former is a one-line flag change that is immediately reversible; the latter is a slightly more invasive edit that eliminates the LLM call path permanently.

---

## Risks of This Recommendation

- **Enum accuracy regression**: Disabling the LLM correction path means records whose enum values survive Layer 1 normalization but still fail validation (e.g., a value not in the synonym table) will be saved with `data_issues` set but the bad enum intact. This was the problem S15 was designed to solve — the 10–20% of enum errors not caught by the normalizer. Teams reviewing exports will see these as validation warnings.
- **Layer 1 synonym coverage gaps**: If a PDF uses terminology not in the existing `SAMPLE_RESULT_SYNONYMS` / `CONDITION_SYNONYMS` / `DISTURBANCE_SYNONYMS` tables, no correction will occur. This is acceptable under the new rule but should be tracked as a data quality metric and the synonym tables expanded over time.
- **S14 safe but wasted work on re-embed**: If embeddings are regenerated after rule change, `enriched_text` will still include values that were LLM-corrected in prior runs. This is a data hygiene issue, not a new extraction issue, but worth noting for any re-extraction passes over historical documents.

