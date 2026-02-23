# Extraction Quality Research — E18-S5 Deep Dive

> **Date**: 2026-02-23
> **Story**: E18-S5 — Extraction Quality: Fuse Cartridge & No-Access Records
> **Baseline**: 26/31 (84%) → **Current**: 27/31 (87%)
> **Target**: 31/31 (100%)

---

## 1. Extraction Pipeline Architecture (for context)

```
PDF → PyMuPDF text extraction
    → _preprocess_samp_format() — injects structural markers:
        - === BUILDING: ... ===
        - --- ROOM: ... ---
        - >>> ACM DETECTED: ... <<<
        - >>> NO ASBESTOS: ... <<<
    → Chunking (prepare_context)
    → LLM extraction via `acm/extraction.jinja` prompt
        - with_structured_output(ACMExtractionResult)
        - Fallback JSON parser if structured output fails
    → Validation → Correction → Deduplication → Save
```

**Key discovery**: The pipeline uses `prompts/acm/extraction.jinja` (non-orchestrator path), NOT `prompts/acm/building_extraction.jinja` (orchestrator path). The orchestrator is skipped for documents below a building/page threshold. Both templates now have the same improvements.

---

## 2. Raw PDF Text Analysis — The 4 Missing Records

### Record #1: Switch Room / Auto Battery Charger / Fuse cartridge

**Page 5, lines 239-249:**
```
Apr-25
First
floor
Switch Room
Automatic
battery
charger
Fuses                    ← NOTE: "Fuses" not "Fuse cartridge"
Asbestos
Assumed
positive
```

**Root cause**: The PDF text says "Fuses" (short form), not "Fuse cartridge" (canonical BAR name). The LLM extracted the Switchboard fuse cartridge in the same room correctly (prompted to use "Fuse cartridge"), but this second item uses just "Fuses" — a word the LLM may not map to the canonical name, or may merge with the preceding Switchboard entry.

**CSV ground truth**: Row 9 — `item=Fuse cartridge, location=Automatic Battery Charger, result=Assumed Positive`

---

### Record #2: Roof / East Ductwork / Flange joints

**Page 7, lines 191-201:**
```
External
Roof
East
ductwork
Flange mastic           ← NOTE: "Flange mastic" not "Flange joints"
(grey)
Asbestos
Positive
34511-039-              ← Sample number split across line break
```

**Page 12, lines 25-30** (lab results section):
```
External, roof, east end, blue ductwork, grey flange mastic
Chrysotile (white asbestos) detected
34511-039-
-
015
```

**Root cause**: The PDF says "Flange mastic (grey)" but the CSV expects "Flange joints". The sample number `34511-039-015` is split across lines. The record IS likely extracted by the LLM (as "Flange mastic"), but the test matching fails because:
1. Room name: LLM may extract "Roof" or "East roof fan room" — CSV has "Roof"
2. Product name: LLM extracts "Flange mastic" — CSV has "Flange joints" (different names for same thing)
3. Sample number may be malformed from line split

**Key finding**: This is likely a **test matching issue**, not an extraction issue. The record may already be extracted under different naming.

---

### Record #3: Lift Foyer / Lift / Internal lining (No Access)

**Page 8, lines 48-65:**
```
Ground
floor
Lift foyer
Lift
Internal lining
-
-
-
-
-
-
-
-
-
 -
No access at the time of the Assessment
```

**Root cause**: The entry has:
- Room: "Lift foyer"
- Location: "Lift"
- Product: "Internal lining"
- Then a run of **12+ dash placeholders** (empty fields)
- Finally: "No access at the time of the Assessment"

The preprocessor (`_preprocess_samp_format`) does NOT inject any marker for "No access" text. It only injects markers for:
- `>>> ACM DETECTED: ...` (positive results)
- `>>> NO ASBESTOS: ...` (negative results)

There is NO `>>> NO ACCESS: ...` marker. The LLM sees 12 dashes followed by "No access" text buried in the flow — it treats this as a non-entry.

**CSV ground truth**: Row 30 — `item=Internal lining, location=Lift, result=Assumed Positive`

---

### Record #4: Main Foyer / Room Adjacent Disabled Toilet / Unknown (No Access)

**Page 8, lines 65-88:**
```
No access at the time of the Assessment    ← End of record #3
-
Apr-25
Ground
floor
Main foyer
Room Adjacent Disabled Toilet
-                                           ← No product name!
-
-
-
-
-
 -
 -
 -
 -
 -
No access due to locked door.
```

**Root cause**: Even worse than record #3:
- Room: "Main foyer"
- Location: "Room Adjacent Disabled Toilet"
- Product: `-` (dash — no product identified, CSV says "Unknown")
- Then another run of **12+ dash placeholders**
- "No access due to locked door."

No structural markers, no product name, no result — the LLM has nothing to anchor on.

**CSV ground truth**: Row 31 — `item=Unknown, location=Room Adjacent Disabled Toilet, result=Assumed Positive`

---

## 3. Proposed Fixes (Prioritized)

### Fix A: Inject "No Access" Markers in Preprocessor (HIGH PRIORITY)

**Fixes**: Records #3 and #4
**Effort**: Small (regex in `_preprocess_samp_format`)
**Reliability**: High

Add to `_preprocess_samp_format()` in `open_notebook/graphs/acm_extraction.py`:

```python
# Mark "No access" patterns as valid entries
no_access_marker = ">>> NO ACCESS: Assumed Positive — this entry MUST be extracted <<<"
for no_access_phrase in [
    "No access at the time of the Assessment",
    "No access due to locked door",
    "No access",
    "Height restriction",
    "Restricted Access",
    "Live Electrical Hazard",
]:
    processed = processed.replace(no_access_phrase, no_access_marker)
```

This makes "No access" entries as visually prominent as ACM DETECTED and NO ASBESTOS markers, which the LLM already handles well.

**File**: `open_notebook/graphs/acm_extraction.py`, function `_preprocess_samp_format()`, after line ~346

---

### Fix B: Add "Fuses" → "Fuse cartridge" Vocabulary Mapping (MEDIUM PRIORITY)

**Fixes**: Record #1
**Effort**: Tiny (one line in prompt)
**Reliability**: Medium (LLM-dependent)

Add to the ACM Product Vocabulary Guide in `prompts/acm/extraction.jinja`:

```
**Important abbreviations:**
- "Fuses" or "Fuse" in register → product: "Fuse cartridge" (canonical BAR name)
```

**Alternative** (more reliable): Add a regex replacement in `_preprocess_samp_format()`:
```python
# Normalize abbreviated product names to canonical BAR vocabulary
processed = re.sub(r'\bFuses\b', 'Fuse cartridge', processed)
```

---

### Fix C: Improve Test Matching for "Flange joints" vs "Flange mastic" (MEDIUM PRIORITY)

**Fixes**: Record #2
**Effort**: Small (test code only)
**Reliability**: High (deterministic)

This record is likely already extracted but under the name "Flange mastic" (what the PDF actually says), while the CSV expects "Flange joints." Two options:

**Option C1**: Add synonym mapping to the test matching:
```python
PRODUCT_SYNONYMS = {
    "flange joints": "flange mastic",
    "flange mastic": "flange joints",
}
```

**Option C2**: Verify by checking the extracted records output — if sample `34511-039-015` appears in extracted records, the issue is purely matching.

**Option C3**: The three-tier fuzzy match (room+location only) should already handle this IF the room name matches. Check if the LLM uses "Roof" (CSV) or something else for the room name.

---

### Fix D: Record Count Hint in Prompt (LOW PRIORITY)

**Fixes**: General extraction completeness
**Effort**: Small (prompt addition)
**Reliability**: Medium

Count the number of room headers detected by the SAMP preprocessor and pass it to the LLM:

```
**Expected minimum records**: Based on document structure analysis, this section contains
approximately {{ estimated_record_count }} register entries. If you extract significantly
fewer, re-scan the content for missed entries.
```

This gives the LLM a self-check mechanism.

---

### Fix E: Two-Pass Extraction with Targeted Re-Extraction (LOW PRIORITY)

**Fixes**: All remaining misses
**Effort**: Medium (new pipeline node)
**Reliability**: Medium-High

After the first extraction pass:
1. Count extracted records per room
2. Compare against preprocessor's room entry count
3. If any room has fewer records than expected, re-prompt with just that room's content and a "find the missing entries" instruction

This is the most expensive option (extra API calls) but handles all cases.

---

## 4. Structured Output / OpenRouter Compatibility

### Problem Discovered

`ChatOpenAI.with_structured_output(ACMExtractionResult)` fails consistently with OpenRouter + Claude Sonnet. The LLM returns explanatory text + markdown-wrapped JSON instead of raw function call arguments.

### Fix Applied (this session)

Added fallback JSON parser in `extract_records()` that:
1. Catches `ValidationError` / `Exception` from `with_structured_output()`
2. On first failure, calls `model.ainvoke(messages)` directly (no function calling)
3. Extracts JSON from markdown code blocks or raw text using regex
4. Parses into `ACMExtractionResult` manually

### Also Fixed

- `max_tokens` fallback increased from 8192 to 16384 (31 records in JSON was truncating at 8K tokens)

---

## 5. Summary of Changes Made This Session

| Commit | Description | Files |
|--------|-------------|-------|
| `dce30de` | Prompt + test matching improvements | `building_extraction.jinja`, `test_broadmeadows_e2e.py`, story, sprint-status |
| `0b05bda` | Primary extraction prompt + fallback parser | `extraction.jinja`, `acm_extraction.py` |
| `a5d57cb` | Story update with E2E results | story file |

---

## 6. Next Steps (Recommended Order)

1. **Implement Fix A** (No Access markers) — highest ROI, fixes 2/4 records
2. **Investigate Fix C** (check if record #2 is already extracted under different name)
3. **Implement Fix B** ("Fuses" → "Fuse cartridge" mapping)
4. **Re-run E2E test** to validate improvements
5. **Consider Fix D/E** only if still below 31/31 after A+B+C
6. **Update E18-S5 story** based on results
