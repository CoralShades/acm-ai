# Findings — E29-S4 Capability Registry + Fallback Contract

## Date: 2026-03-01 | Agent: Amelia (Dev)

---

## Fallback Matrix Mapping (Architecture Delta § 3.1 → Code)

| Fallback | Condition | Current Code Location | S4 Change |
|----------|-----------|----------------------|-----------|
| F1 | No inventory | `orchestrator.py:937` — creates SyntheticExtractionPlan | Add `emit_fallback_telemetry(F1, ...)` |
| F2 | No Docling tables | `orchestrator.py:681-684` — `if docling_tables:` check | Add `emit_fallback_telemetry(F2, ...)` on else branch |
| F3 | JSON parse failure | `orchestrator.py:569-574` — `ValueError/ValidationError` catch | Add `emit_fallback_telemetry(F3, ...)` in except |
| F4 | Zero records | `orchestrator.py:1020-1035` — 0-record warning | Add `emit_fallback_telemetry(F4, ...)` |
| F5 | Validation failure | `acm_extraction.py:2106` — `not validation.is_valid` | Telemetry tag on correction entry |
| F6 | Correction exhausted | `acm_extraction.py:2085` — `attempt >= max_attempts` | Telemetry tag when cap hit |
| F7 | LLM 5xx/timeout | `orchestrator.py:576-649` — exception handler | Add `emit_fallback_telemetry(F7, ...)` |
| F8 | Docling extraction failure | `source_commands.py` Docling section | Already has `except` — add telemetry tag |

---

## Retry Contract — Current vs Target

| Aspect | Current | Target (S4) |
|--------|---------|-------------|
| Max correction attempts | `max_correction_attempts=2` in `should_correct()` | `max_retries=3` per AC-5 |
| LLM retry | No explicit retry on 5xx | 1 retry with 5s backoff (F7) |
| Backoff type | None | Fixed 5s (not exponential) |
| Retry budget check | Inline `attempt >= max_attempts` | Centralized `check_retry_budget()` in registry |

**Key change**: `should_correct()` at `acm_extraction.py:2083` uses `max_correction_attempts=2` default. Must change to `3` per AC-5. The registry codifies this but the actual enforcement remains in `should_correct()`.

---

## Strategy Registry Design

The registry is a **lookup table**, not an abstraction layer. Key design decisions:

1. **FallbackId enum** with string values matching telemetry tags: `F1="fallback.no_inventory"`, etc.
2. **FallbackContract** is a frozen dataclass (immutable) with all fields from arch delta § 3.1
3. **FALLBACK_MATRIX** is a module-level `dict[FallbackId, FallbackContract]` — no dynamic construction
4. **`emit_fallback_telemetry()`** uses `loguru.logger.info()` with structured dict for grep-ability
5. **`select_strategy()`** wraps existing `_select_strategy()` logic — no behavior change, just centralization
6. **`check_retry_budget()`** is a pure function: `attempt < contract.max_retries`

---

## Integration Points (orchestrator.py changes)

1. **`orchestrate_extraction()`** line 937-965: F1 synthetic plan → add `emit_fallback_telemetry(F1)`
2. **`extract_building()`** line 677-695: F2 no Docling tables → add `emit_fallback_telemetry(F2)` in else branch
3. **`_llm_extract_building()`** line 569-574: F3 JSON parse → add `emit_fallback_telemetry(F3)` in except
4. **`_llm_extract_building()`** line 576-649: F7 LLM error → add `emit_fallback_telemetry(F7)`
5. **`orchestrate_extraction()`** line 1020-1035: F4 zero records → add `emit_fallback_telemetry(F4)`
6. **`should_correct()`** in acm_extraction.py: F5/F6 correction loop → update max_attempts, add telemetry
7. **Return value**: Add `fallback_activated: list[str]` to orchestrator output dict

---

## Risk: Minimal Behavior Change

S4 is purely **additive** — it adds:
- A new file (`strategy_registry.py`)
- Structured log emissions at existing decision points
- A retry cap change from 2 → 3
- Metadata fields for fallback tracking

No routing logic changes. No extraction behavior changes. The benchmark numbers should be identical to post-S3 baseline.

---

## acm_schemas.py Changes (Minimal)

The story spec says T4 = "Update `acm_schemas.py` with strategy metadata fields" (~15 lines). Analysis:

- `BuildingExtractionStats` (in `orchestrator.py`) already has `strategy_used: str`. Add optional `fallback_tags: list[str]` field.
- `OrchestratorStats` (in `orchestrator.py`) — add `fallback_activated: list[str]` for aggregate tracking.
- No changes needed to `ACMExtractionRecord` itself.
- Could add a small `StrategyMetadata` model in `acm_schemas.py` but that's over-engineering. Keep it simple: just list[str] fields on existing models.

---

## Gate 2 Readiness Pre-Check

| # | Criterion | Pre-S4 Status | S4 Adds |
|---|-----------|---------------|---------|
| G2.1 | Broadmeadows >= 31/31 | Must verify post-S3 | No behavior change → same result expected |
| G2.2 | Alexander >= 36/43 all buildings | Must verify post-S3 | No behavior change → same result expected |
| G2.3 | Docling injection confirmed | Working (S3 did not change) | No change |
| G2.4 | Fallback contract tested | NOT YET | **S4 delivers this** |
| G2.5 | Synthetic plan for no-inventory | Working (S3 added) | Telemetry tag added |
