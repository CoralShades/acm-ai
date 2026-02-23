# Extraction Pipeline Bugfix — Findings

## Date: 2026-02-22

## Bug Analysis from Worker Logs

Three distinct bugs identified from extraction pipeline worker logs when processing
`broadmeadows-police-station-samp.pdf` (Broadmeadows Police Station SAMP document).

---

### BUG 1: Pydantic Validation Rejects ALL Records (CRITICAL — P0)

**Symptom:** 0 records extracted despite LLM returning 17+ records successfully.
Every record fails with `26 validation errors for ACMExtractionResult`.

**Error Pattern:**
```
records.0.friable — Value error, friable must be one of ['Friable', 'Non Friable'], got 'N/A (negative)'
records.0.material_condition — Value error, material_condition must be one of ['Damaged', 'Fair', 'Good', 'Poor'], got 'N/A (negative)'
```
Repeated for records 0,1,2,3,5,8,9,10,11,12,13,15,16 (13 of ~17 records).

**Root Cause:** `open_notebook/extractors/acm_schemas.py` lines 216-228 and 240-250.
The `validate_friable()` and `validate_material_condition()` validators only accept
their canonical BAR values or None. When the LLM returns `"N/A (negative)"` for samples
that tested negative for asbestos (where friable/condition are genuinely not applicable),
the validator raises ValueError instead of normalizing to None.

**The fields are `Optional[str]` with `default=None`** — so None is a perfectly valid
value. The LLM is semantically correct: negative samples don't have friable status or
condition assessments.

**Fix:** Add N/A pattern recognition to both validators. If the value matches common
N/A patterns (`"N/A"`, `"N/A (negative)"`, `"Not Applicable"`, `"-"`, `"None"`),
return `None` instead of raising ValueError.

**File:** `open_notebook/extractors/acm_schemas.py` — `validate_friable()` and
`validate_material_condition()` methods.

**Impact:** CRITICAL. This bug causes 100% record rejection for documents with
negative asbestos results (which is most real-world SAMP documents).

---

### BUG 2: Google Vertex AI Rejects `anthropic-beta` Header (MEDIUM)

**Symptom:** Structure extraction and page tagging fall back to heuristic.
```
LLM structure extraction failed: Error code: 400 — 'Unexpected value(s)
`structured-outputs-2025-11-13` for the `anthropic-beta` header'
Provider: Google
```

**Root Cause:** The extraction model is routed through OpenRouter to a Google Vertex AI
provider for an Anthropic model. The `structured-outputs-2025-11-13` beta header is
Anthropic API-specific and not supported when Anthropic models are proxied through
Google Vertex AI.

**Impact:** Structure extraction falls back to heuristic (`DocumentType.UNKNOWN`,
`register_start=None`), which degrades quality but doesn't block extraction entirely.
The fallback heuristic still works. This is a model selection/routing issue — using a
direct Anthropic or OpenRouter-native provider would avoid this.

**Fix Strategy:** This is a model configuration issue, not a code bug. The user should
select a model routed through a provider that supports structured outputs (direct
Anthropic, OpenRouter native). No code change needed — user requested using
"openrouter / sonnet / gemini models for the demo."

---

### BUG 3: Amazon Bedrock Rejects integer min/max in JSON Schema (MEDIUM)

**Symptom:** Page tagging and structure extraction fall back to heuristic.
```
LLM page tagging failed: Error code: 400 — 'For 'integer' type, properties
maximum, minimum are not supported'
Provider: Amazon Bedrock
```

**Root Cause:** Amazon Bedrock's structured output implementation doesn't support
`minimum`/`maximum` constraints on integer fields in JSON schemas. Pydantic models
with `Field(ge=0)` or similar constraints generate these properties, which Bedrock
rejects.

**Impact:** Same as Bug 2 — falls back to heuristic. Not a blocker for extraction
but degrades quality.

**Fix Strategy:** Same as Bug 2 — model configuration issue. User should switch to
models that support full JSON schema. For the demo, use OpenRouter/Sonnet/Gemini.

---

### BUG 4: Token Limit Reached (LOW — secondary effect)

**Symptom:** Some structure/metadata extraction calls hit completion token limits.
```
Could not parse response content as the length limit was reached —
completion_tokens=2048
```

**Root Cause:** Some models have low `max_output_tokens` defaults (2048). The model
capabilities system (migration 20) should provide proper limits, but the extraction
code uses hardcoded fallbacks (`max_tokens=4096` in document_structure.py line 141).

**Impact:** Metadata extraction falls back to heuristic. Not a blocker.

**Fix Strategy:** This resolves itself when using better models (Sonnet/Gemini with
higher output limits). No code change needed for demo.

---

## Key Source Files Investigated

| File | Lines | What |
|------|-------|------|
| `open_notebook/extractors/acm_schemas.py` | 216-228, 240-250 | **BUG 1** — Validators for friable/material_condition |
| `open_notebook/extractors/orchestrator.py` | 341-401, 456, 472 | LLM extraction + error catch |
| `open_notebook/extractors/document_structure.py` | 114-152, 230-247 | **BUG 2/3** — Structure extraction LLM call |
| `open_notebook/extractors/page_tagger.py` | 435-454 | **BUG 2/3** — Page tagging LLM call |
| `open_notebook/graphs/utils.py` | 12-42 | Model provisioning logic |
| `open_notebook/graphs/acm_extraction.py` | 1065-1090 | Main extraction model provisioning |

## Decision Log

- **D1:** Bug 1 is the only code fix needed. Bugs 2/3/4 are provider-routing issues
  that resolve by selecting appropriate models for the demo.
- **D2:** Fix validators to normalize N/A values to None (matching the Optional field semantics).
- **D3:** Also apply the same N/A normalization to `risk_status` and `area_type` validators
  for defensive consistency.
