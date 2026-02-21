# Story E1-S23: Token Limit Quality Validation

**Epic:** E1 — ACM Data Extraction Pipeline
**Priority:** P0
**Status:** done
**Added:** Post-merge review 2026-02-15

---

## User Story

**As a** system operator running ACM extraction on large buildings,
**I want** the pipeline to detect when table content exceeds the extraction model's context window and automatically chunk the input,
**So that** all records are extracted completely even when a building's register spans more tokens than a single model call can handle.

---

## Background

E1-S22 (Extraction Output Token Limit Fix) raised `max_tokens` from 8192 to 32768 to accommodate larger outputs. However, the *input* token limit is a separate constraint. Large SAMP documents — such as the Broadmeadows Police Station SAMP with 31 records spread across many pages — risk having table *content* that exceeds model context limits.

Current observed gap: E2E testing on Broadmeadows shows 8/31 records extracted (26%) when using Haiku's 8K context. The hypothesis is that a large portion of the register simply does not fit in a single Haiku call, causing silent truncation.

This story validates that hypothesis, implements smart chunking, and establishes quality metrics comparing single-pass vs. chunked extraction.

**Key reference documents:**
- E2E findings: `_bmad-output/implementation-artifacts/findings.md`
- Test document: `docs/samplePDF/Broadmeadows_Police_Station_SAMP.pdf` (31 records)

---

## Acceptance Criteria

### Detection
- [ ] After each extraction call, inspect the response to detect whether truncation may have occurred
- [ ] Add `token_limit_exceeded: bool` flag to `ExtractionRun` — set `True` when:
  - Estimated input tokens exceed 80% of the model's documented context window, OR
  - The extraction response ends abruptly (no closing JSON structure), OR
  - Record count is suspiciously low relative to known building size
- [ ] Log a warning when `token_limit_exceeded` is True
- [ ] Expose `token_limit_exceeded` and `chunk_count` in the extraction run API response

### Smart Chunking
- [ ] New `TokenLimitValidator` class in `open_notebook/extractors/`
- [ ] Accepts extracted page content (markdown/HTML tables) and target model identifier
- [ ] Splits large table content into chunks that fit within the model's context window (with headroom for system prompt + output)
- [ ] Chunk strategy: split by building/room boundaries where possible; fall back to row-count splitting
- [ ] Extracts each chunk independently using the same extraction model
- [ ] Merges chunk results into a single deduplicated `ACMRecord` list
- [ ] Deduplication: use existing dedup key logic from E1-S26 to avoid duplicate records at chunk boundaries
- [ ] `chunk_count: int` field on `ExtractionRun` records how many chunks were used (1 = no chunking needed)

### Model Comparison
- [ ] Configurable: extraction model selectable at run time (already supported via model registry)
- [ ] Document the context window limits for key models:
  - Haiku 3.5: 200K input tokens (but practical table extraction limit is ~8K due to output constraints)
  - Sonnet 3.5/3.7: 200K input tokens, 8K output by default
  - GPT-4o: 128K input tokens
- [ ] Add a comparison test: run extraction on Broadmeadows SAMP with Haiku (single-pass) vs. with chunking enabled; report record count and accuracy
- [ ] Test output stored in `_bmad-output/implementation-artifacts/token-limit-test-results.md`

### New Model/Schema Fields
- [ ] `ExtractionRun` domain model gains two new optional fields:
  ```python
  token_limit_exceeded: bool = False
  chunk_count: int = 1
  ```
- [ ] SurrealDB migration adds these columns to the `extraction_run` table
- [ ] API response for `GET /api/acm/extraction-run/{id}` includes both fields

### Performance
- [ ] Chunked extraction must complete within 2x the time of a single-pass extraction for the same document
- [ ] No regression on documents that do not require chunking (chunk_count stays 1)

---

## Technical Notes

### New Class: TokenLimitValidator

**Location:** `open_notebook/extractors/token_limit_validator.py`

```python
class TokenLimitValidator:
    """
    Detects token limit violations and splits large extraction inputs into
    manageable chunks. Chunks are extracted independently and merged.
    """

    def __init__(self, model_id: str, context_window: int, safety_margin: float = 0.8):
        self.model_id = model_id
        self.context_window = context_window
        self.safety_margin = safety_margin  # use 80% of window to leave room for prompt + output

    def needs_chunking(self, content: str, prompt_overhead: int = 2000) -> bool:
        """Returns True if content exceeds the safe token budget."""
        ...

    def split_into_chunks(self, table_rows: list[RawACMItem], max_rows_per_chunk: int) -> list[list[RawACMItem]]:
        """Split rows into chunks, respecting building/room boundaries."""
        ...

    def merge_chunk_results(self, chunk_results: list[list[ACMRecord]]) -> list[ACMRecord]:
        """Merge and deduplicate records across chunk results."""
        ...
```

### Integration Point in Pipeline

In `open_notebook/extractors/pipeline.py` (or the agentic orchestrator from E1-S20), after Stage 1 extraction and before Stage 2 interpretation:

```python
validator = TokenLimitValidator(model_id=extraction_model.id, context_window=model_context_window)
if validator.needs_chunking(raw_content):
    chunks = validator.split_into_chunks(raw_items, max_rows_per_chunk=15)
    all_records = []
    for chunk in chunks:
        records = await extract_chunk(chunk, model)
        all_records.extend(records)
    records = validator.merge_chunk_results(all_records)
    extraction_run.chunk_count = len(chunks)
    extraction_run.token_limit_exceeded = True
else:
    records = await extract_single_pass(raw_content, model)
    extraction_run.chunk_count = 1
    extraction_run.token_limit_exceeded = False
```

### Token Estimation

Use a simple character-based heuristic for fast estimation (avoid adding a tokenizer dependency):
- 1 token ≈ 4 characters for English prose
- 1 token ≈ 3 characters for structured table data (denser)
- Apply 3-char/token rule for table content estimation

For more precise counting, optionally use `tiktoken` (already available as a transitive dependency via LangChain) — but only if the simple heuristic proves insufficiently accurate in testing.

### Migration

New file: `migrations/XX-extraction-run-token-fields.surrealql`

```sql
-- Add token limit tracking fields to extraction_run table
DEFINE FIELD token_limit_exceeded ON extraction_run TYPE bool DEFAULT false;
DEFINE FIELD chunk_count ON extraction_run TYPE int DEFAULT 1;
```

### Test Procedure

1. Run extraction on `Broadmeadows_Police_Station_SAMP.pdf` with chunking disabled → record baseline (expected: ~8/31 records with Haiku)
2. Run extraction with chunking enabled → verify record count improves toward 31/31
3. Run extraction with Sonnet 32K → compare as control
4. Document results in `_bmad-output/implementation-artifacts/token-limit-test-results.md`:
   - Records extracted per run
   - chunk_count per run
   - token_limit_exceeded flag per run
   - Wall-clock time per run

---

## Key Files

| File | Change |
|------|--------|
| `open_notebook/extractors/token_limit_validator.py` | New: `TokenLimitValidator` class |
| `open_notebook/domain/acm.py` (or `extraction_run.py`) | Add `token_limit_exceeded: bool`, `chunk_count: int` to `ExtractionRun` |
| `open_notebook/extractors/pipeline.py` | Integrate `TokenLimitValidator` into Stage 1 → Stage 2 handoff |
| `migrations/XX-extraction-run-token-fields.surrealql` | New columns on `extraction_run` table |
| `api/models.py` | Expose `token_limit_exceeded`, `chunk_count` in extraction run API response |
| `_bmad-output/implementation-artifacts/token-limit-test-results.md` | New: test results document |

---

## Dependencies

- **Requires:**
  - E1-S1 (ACM Data Model — done) — `extraction_run` table exists
  - E1-S2 (Domain Model — done) — `ACMRecord`, `ExtractionRun` models exist
  - E1-S20 (Agentic Orchestrator — done) — pipeline orchestration layer where chunking integrates
- **Blocks:** Nothing currently blocked by this story
- **Related:** E1-S22 (output token limit fix — done) — raised `max_tokens`; this story addresses input token limits

---

## Estimated Effort

M (Medium) — New `TokenLimitValidator` class is the core deliverable; integration into the existing pipeline is straightforward. The main risk is accurately detecting truncation and correctly splitting at building/room boundaries. The test procedure adds validation overhead but uses existing test infrastructure.

---

## Dev Agent Record

*To be filled in during implementation.*

- Build status: —
- Files verified: —
- Pages verified: —
- Test results path: —
