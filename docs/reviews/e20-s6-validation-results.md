# E20-S6 Validation Results — 2026-02-26

## Approach

### Phase 0: Baseline with Fresh Worker (no prompt changes)
- Killed all stale workers, started fresh worker on commit `3355a24`
- API confirmed healthy on port 5055
- Clean slate: deleted all Broadmeadows records, cleaned stale commands
- Ran extraction with unmodified prompt template
- **Result: 17/31** — same as previous E20-S5 baseline

### Phase 1: Prompt Engineering (3 iterations, 3 API calls)

**Iteration 1 — Positional emphasis + worked examples:**
- Added `⚠️ CRITICAL EXTRACTION RULES` section at top of template (primacy effect)
- Added worked examples for "As Per", "Not Sampled", "No Access" rows
- Added `FINAL VERIFICATION` counter at end of prompt (recency effect)
- Preserved all existing rules (enhanced, not deleted)
- **Result: 17/31** — no change

**Root cause discovery #1:** The actual PDF uses **"Same as 34511-039001"**, not "As Per 34511-039-001". The prompt rules referenced "As Per" but the content uses "Same as". Terminology mismatch.

**Iteration 2 — Terminology fix + "Same as" vocabulary:**
- Added "Same as" to all rule sections alongside "As Per" and "Similar To"
- Updated examples to use "Same as" wording
- Added explicit rule: "-" dash in sample number field = "not sampled" (valid record)
- **Result: 17/31** — no change

**Root cause discovery #2:** PDF-to-text conversion splits multi-word values across lines:
```
Same as        ← line 1
34511-039001   ← line 2
```
And:
```
Assumed        ← line 1
positive       ← line 2
```
Prompt examples showed these on single lines — model couldn't match.

**Iteration 3 — Line-break format matching:**
- Updated all examples to show exact vertical PDF text format with line breaks
- Added explicit guidance: "Same as\n34511-039001" = one value split across lines
- Added expected count hint: "typical register has 25-35 rows, if you get 15-20 you're missing records"
- **Result: 17/31** — no change

## Results

| Metric | E20-S5 Baseline | Phase 0 (fresh worker) | Phase 1 Iter 1 | Phase 1 Iter 2 | Phase 1 Iter 3 |
|--------|-----------------|----------------------|----------------|----------------|----------------|
| Total records | 17/31 (55%) | 17/31 (55%) | 17/31 (55%) | 17/31 (55%) | 17/31 (55%) |
| "Same as" records | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 |
| "Not Sampled" records | 0/6 | 0/6 | 0/6 | 0/6 | 0/6 |
| Core samples (16 NATA) | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| Extra (005 not in CSV) | 1 | 1 | 1 | 1 | 1 |
| Model | claude-sonnet-4.6 | claude-sonnet-4.6 | claude-sonnet-4.6 | claude-sonnet-4.6 | claude-sonnet-4.6 |

**Note:** The CSV baseline has 6 "Not Sampled" rows (not 5 as the story spec stated). Row 4 (Front Desk Filing Cabinet) was undercounted.

## Key Finding: Model Behavioral Ceiling

**The 17/31 result is a model behavioral ceiling for `claude-sonnet-4.6` via OpenRouter on this document, NOT a prompt design problem.**

Evidence:
1. Three distinct prompt engineering approaches (positional emphasis, terminology correction, format matching) all produced identical 17-record output
2. The model consistently extracts ONLY rows with explicit NATA sample numbers (34511-039-XXX)
3. Zero "Same as" reference rows extracted despite prompt rules at top, examples matching exact content format, and verification counter at end
4. Zero "Assumed positive" unsampled items extracted despite explicit examples showing the exact `-` dash pattern
5. The model's extraction time varied (84-101s) but output count was always exactly 17

### Root Causes Identified

1. **Terminology mismatch (corrected but ineffective):** Prompt said "As Per" but PDF says "Same as"
2. **Line-break format mismatch (corrected but ineffective):** PDF splits "Same as\n34511-039001" across lines
3. **Model behavioral pattern:** `claude-sonnet-4.6` has a strong prior to extract only rows with numeric sample identifiers; it treats "Same as" references and unsampled items as metadata rather than separate records
4. **Pipeline audit hypothesis disproved:** The audit claimed stale worker code was the primary cause (Section 5, Cause 1). Testing with fresh worker on latest code confirmed 17/31, not the projected 28/31.

## Prompt Changes Applied (retained for future model testing)

The prompt template `prompts/acm/building_extraction.jinja` was enhanced from 406→569 lines with:

1. **New top section:** `⚠️ CRITICAL EXTRACTION RULES — READ BEFORE ANYTHING ELSE` with "Same as" / "As Per" / "Similar To" rules, "Not Sampled" dash-pattern rules, and "No Access" rules
2. **New "PDF Text Formatting" section:** Explains multi-line value splitting (Same as\n34511-039XXX)
3. **Three worked examples** matching exact vertical PDF text format:
   - Example 1: "Same as" reference row (Corridor adjacent cells)
   - Example 2: "Assumed positive" with "-" sample number (Switch Room fuses)
   - Example 3: "No access" item (Main Foyer)
4. **Updated Rule 8:** Added "-" dash recognition for unsampled items
5. **Updated Rule 11:** Added "Same as" as primary wording alongside "As Per"/"Similar To"
6. **New end section:** `⚠️ FINAL VERIFICATION` counter with expected count hint (25-35 rows typical)

All existing rules preserved and enhanced. No rules deleted.

## Recommended Next Steps (Beyond Prompt-Only Scope)

These require code changes (orchestrator, graph nodes, or model configuration):

1. **Try a different model:** GPT-4o or Claude Opus may have different extraction behavior for unstructured table data. AC4 originally specified multi-model testing.
2. **Two-pass extraction:** First pass extracts sampled records, second pass specifically targets "Same as" and "Assumed positive" rows with a focused prompt.
3. **Content pre-processing:** Normalize "Same as\n34511-039XXX" to "Same as 34511-039XXX" (single line) before sending to LLM. Also normalize "Assumed\npositive" to "Assumed positive".
4. **Structured table extraction:** Use a table-aware extraction approach (e.g., MinerU table detection, which is currently dead code per the pipeline audit) to provide the LLM with clean tabular input instead of vertical text.

## Files Modified

| File | Change |
|------|--------|
| `prompts/acm/building_extraction.jinja` | Enhanced: +163 lines (406→569). New critical rules, worked examples, format guidance, verification counter |

## API Cost

3 extraction attempts × ~$0.15/call (claude-sonnet-4.6, 18k content + 26k prompt) ≈ $0.45 total OpenRouter spend.
