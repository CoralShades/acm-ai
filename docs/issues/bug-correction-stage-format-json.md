# Correction stage format="json" not applied — 100% failure with Ollama

> **GitHub Issue**: #97
> **Discovered**: 2026-03-05 (E36-S2 + E36-S4 benchmark)
> **Findings**: F003, F008, F014
> **Priority**: CONCERN
> **Status**: Open — correction stage still unresolved (metadata/inventory stages fixed in commit `476c285e`)

## Problem

The `format="json"` parameter (E35-S3 fix) is applied to the **extraction** LLM call via `_apply_ollama_extraction_settings()` but is **NOT** applied to the **correction** LLM call in `_llm_correct_records()`. All Ollama correction attempts return empty JSON bodies (`Expecting value: line 1 column 1 (char 0)`), causing 100% correction failure rate.

## Evidence

During E36-S4 benchmark, every Ollama model (qwen2.5:7b, llama3.1:8b, mistral:7b, qwen3:32b, qwen2.5:32b, phi4:14b) failed 100% of correction attempts:

```
WARNING | _llm_correct_records:2621 - LLM correction failed for record 15: Expecting value: line 1 column 1 (char 0)
WARNING | _llm_correct_records:2621 - LLM correction failed for record 16: Expecting value: line 1 column 1 (char 0)
# 39 failures in a single run, 0 successes
```

Broadmeadows extraction with llama3.1:8b: `Correction stats: auto=0, llm=0, failed=39, total_validated=76`

## Impact

- Validated field errors persist (corrections never apply with Ollama)
- Records are still saved (extraction works), but quality is lower
- Cloud providers (Anthropic, OpenRouter) are unaffected

## Fix

Apply `_apply_ollama_extraction_settings()` to the correction LLM call:

```python
# In acm_extraction.py:_llm_correct_records() (~line 2600)
correction_model = _provision_correction_model(state)
correction_model = _apply_ollama_extraction_settings(correction_model)  # ADD THIS
```

## Key Files

- [`open_notebook/graphs/acm_extraction.py`](../../open_notebook/graphs/acm_extraction.py) — `_llm_correct_records()` function (~line 2600)
- [`open_notebook/graphs/utils.py`](../../open_notebook/graphs/utils.py) — `_apply_ollama_extraction_settings()` (~line 247)

## Related

- GitHub Issue: [#97](https://github.com/CoralShades/acm-ai/issues/97)
- Existing Issue: [#93](https://github.com/CoralShades/acm-ai/issues/93) (Ollama extraction hardening — partial fix)
- Findings: F003, F008, F014 in [`docs/sprint-artifacts/e36/findings.md`](../sprint-artifacts/e36/findings.md)
- Log sentinel: [`docs/sprint-artifacts/e36/evidence/log-sentinel-e36s4.md`](../sprint-artifacts/e36/evidence/log-sentinel-e36s4.md)
- Stories: E35-S3 (Ollama Hardening), E35-S4 (Provider Priority)

## Note (2026-03-14)

Commit `476c285e` applied `_apply_ollama_extraction_settings()` to the **metadata_and_structure** and **building_inventory** extraction stages — not to `_llm_correct_records()`. The correction stage remains unpatched. This issue stays open.
