# ACM-AI Heuristic & Deterministic Rules Reference

**Source:** `V3/heuristic-rules-reference.html`
**Coverage:** 60+ rules across 15+ files in the extraction pipeline

---

## Relevance Assessment

**Status: PARTIALLY CURRENT — Core patterns valid; routing logic targeted for removal in E29**

This document captures every regex pattern, normalization rule, routing decision, and deterministic workflow in the current (E26) ACM-AI extraction pipeline.

**V3 relevance breakdown:**
- **KEEP AND CARRY FORWARD:** Page marker patterns, building/room header patterns, table data normalizations, enum normalizations, product taxonomy regex, deduplication logic, no-access recovery, Pydantic validation rules
- **SUPERSEDED BY E29:** `should_use_orchestrator()` conditional routing, legacy extraction path routing, Stage 5 (Strategy Routing) dual-path logic
- **TO EVOLVE FOR V3:** The pipeline structure (Phases 2-3) will be redesigned per E29's specialized agent architecture, but the individual regex patterns and normalization rules WITHIN those stages remain valid

**V3 planning steps that should reference this document:**
- `/bmad:mmm:dev-story` — Every extraction story needs to reference the canonical patterns here. Do NOT redefine patterns — import from their single source of truth.
- `Create Architecture` — The "Agent ① Table Parser" in E29's unified pipeline must embed the normalizations from §09 (Docling Table Data Normalizations)
- `Technical Research` — The product taxonomy regex (§13) is the baseline for Classifier agent efficiency claims

**Most critical sections for downstream agents:**
1. §01 — `_PAGE_PATTERN` (canonical, imported by all stages)
2. §09 — Docling table normalizations (must carry into E29 Table Parser agent)
3. §10 — Enum normalization tables (ground truth for BAR field values)
4. §13 — Product taxonomy regex (~80% classifier hit rate)
5. §15 — Deduplication composite key (4-field key, E26 fix)
6. §16 — No-access recovery logic (post-dedup scan)

---

## 01 / Page Marker Patterns

Page markers delimit PDF pages in Docling/PyMuPDF output. Used by nearly every pipeline stage.

### `_PAGE_PATTERN` — Canonical (document_structure.py)

**Single source of truth. All other files import this. Do NOT redefine.**

```python
_PAGE_PATTERN = re.compile(r"(?:^|\n)[-—]+\s*Page\s+(\d+)\s*[-—]+", re.IGNORECASE)
```

Matches: `--- Page 5 ---`, `——— Page 12 ———`, `--- page 1 ---`

**Used by:** `document_structure.py`, `building_inventory.py`, `page_tagger.py`, `acm_extraction.py` (chunking)

### Extended `page_pattern` (acm_extraction.py ~L248)

Extended pattern for chunking that supports HTML comments and simple format:

```python
# Supports 3 formats:
# 1. Dashes: "--- Page 5 ---" or "——— Page 5 ———"
# 2. HTML comment: "<!-- Page 5 -->"
# 3. Simple: "Page 5" at line start
page_pattern = r"(?:(?:^|\n)[-—]+\s*Page\s+(\d+)\s*[-—]+|<!--\s*Page\s+(\d+)\s*-->|(?:^|\n)Page\s+(\d+)(?:\s|$))"
```

Special handling: Multiple capture groups — extract page number via:
```python
int(next(g for g in match.groups() if g is not None))
```

### `_extract_total_pages()` (document_structure.py)

```python
def _extract_total_pages(content: str) -> int:
    matches = list(_PAGE_PATTERN.finditer(content))
    if not matches:
        return 1
    return max(int(m.group(1)) for m in matches)
```

### `_split_into_pages()` (page_tagger.py)

```python
def _split_into_pages(content: str) -> List[Tuple[int, str]]:
    matches = list(_PAGE_PATTERN.finditer(content))
    if not matches:
        return [(1, content)]
    pages = []
    for i, match in enumerate(matches):
        page_num = int(match.group(1))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        page_text = content[start:end].strip()
        if page_text:
            pages.append((page_num, page_text))
    return pages
```

---

## 02 / Building & Room Header Patterns

Two pattern sets exist with intentionally different behaviour.

> **Important:** The `acm_extractor.py` patterns treat rooms as a type of building. The `building_inventory.py` patterns use `\s+[-–]\s+` (space-dash-space) for buildings vs `-R####` prefix for rooms.

### Set A: Regex Parser Patterns (acm_extractor.py ~L32-51)

```python
BUILDING_PATTERN = re.compile(
    r"^#+\s*(?:Building[:\s]*)?([A-Z]\d{2,3}[A-Z]?)\s*[-–]\s*(.+?)(?:\s*[-–]\s*(\d{4}))?(?:\s*[-–]\s*(.+))?$",
    re.IGNORECASE | re.MULTILINE
)
# Matches: "## B00A - Other-Dse Admin - 1924 - Brick"
# Groups: (1) building_id=B00A, (2) name=Other-Dse Admin, (3) year=1924, (4) construction=Brick

ROOM_PATTERN = re.compile(
    r"^#+\s*(?:Room[:\s]*)?([A-Z0-9]+-?R?\d+)\s*[-–]\s*(.+?)(?:\s*[-–]\s*([\d.]+)\s*m²)?$",
    re.IGNORECASE | re.MULTILINE
)
# Matches: "### B00A-R0001 - Main Office - 32.5 m²"
# Groups: (1) room_id=B00A-R0001, (2) name=Main Office, (3) area_m2=32.5

AREA_TYPE_PATTERN = re.compile(
    r"^#+\s*(?:Area\s*Type[:\s]*)?(\bExterior\b|\bInterior\b|\bGrounds\b)",
    re.IGNORECASE | re.MULTILINE
)
# Matches: "## Interior" or "## Area Type: Exterior"

SCHOOL_PATTERN = re.compile(
    r"^#\s*(.+?)(?:\s*[-–]\s*(?:Asbestos|ACM|SAMP))?.*?$",
    re.IGNORECASE | re.MULTILINE
)
# Extracts school/site name from H1 header
```

### Set B: Inventory Patterns (building_inventory.py)

```python
# Matches SAMP format: "B00A - Admin Block - 1924"
# Does NOT match rooms (they use B00A-R0001 with no space before dash)
_BUILDING_HEADER = re.compile(r"([A-Z]\d{2,3}[A-Z]?)\s+[-–]\s+(.+?)(?:\s+[-–]\s+(\d{4}))?")

# For ARA format: detects "Building Name:" header blocks via _detect_ara_buildings()

# Requires -R#### prefix to positively identify rooms vs buildings
# Matches: "B00A-R0001 - External Movement" or "B00A-R0001 - Office - 32.5 m²"
_ROOM_HEADER = re.compile(r"([A-Z]\d{2,3}[A-Z]?-R\d{3,4})\s*[-–]\s*(.+?)(?:\s*[-–]\s*([\d.]+)\s*m²)?")

# Broader pattern used during extraction (orchestrator.py)
# Matches dash, en-dash, AND tab separators
ROOM_ENTRY_PATTERN = re.compile(r"([A-Z]\d{2,3}[A-Z]?-R\d+)(?:\s*[-–\t]\s*)(.+)")
```

---

## 03 / Content Detection Patterns

```python
# Building ID Detection
r"\b(B\d{2,3}[A-Z]?)\b"  # SAMP B-series: B000, B00A, B12C
r"\b(D\d{1,3})\b"          # D-series: D01, D02

# Australian Address Patterns (metadata_extractor.py)
ADDRESS_PATTERN = r"(\d+[-/]?\d*)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Court|Ct|Crescent|Cres|Boulevard|Blvd|Way|Place|Pl))"
SUBURB_STATE_POSTCODE = r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:VIC|NSW|QLD|SA|WA|TAS|NT|ACT)\s+(\d{4})"

# Report Reference Patterns (metadata_extractor.py)
REPORT_REF_PATTERNS = [
    r"(?:Report\s+(?:No|Number|Ref)\.?[:\s]+)([\w\-/]+)",
    r"(?:Reference[:\s]+)([\w\-/]+)",
    r"(?:Job\s+(?:No|Number)\.?[:\s]+)([\w\-/]+)",
]
```

---

## 04 / Stage: Document Structure Heuristic

Runs when LLM structured output fails (currently fails 100% of the time due to `completionState` envelope). Extracts document structure using regex only.

**File:** `document_structure.py → _heuristic_fallback()`

| What It Extracts | How | Accuracy |
|-----------------|-----|---------|
| `total_pages` | `_extract_total_pages()` — highest page marker number | 100% |
| `register_start_page` | Scan for first page with building header regex (B### or D##) | High (SAMP), moderate (ARA) |
| `building_ids` | Regex scan: `\b(B\d{2,3}[A-Z]?)\b` and `\b(D\d{1,3})\b` | High |
| `document_type` | Set to `UNKNOWN` (can't determine SAMP vs ARA without LLM) | N/A — cosmetic field |
| `sections` | Not populated by heuristic — empty list | N/A |

**Impact Assessment:** Minimal accuracy loss. `document_type=UNKNOWN` is cosmetic. `register_start_page` and `building_ids` are detected correctly for SAMP format.

---

## 05 / Stage: Building Inventory Heuristic

Compiles building-level metadata (page ranges, rooms, complexity). Even when LLM succeeds, heuristic ALWAYS runs as cross-validation and merges discoveries.

**File:** `building_inventory.py → _heuristic_fallback()`

**Step-by-Step Logic:**

1. **Trim to Register:** `_trim_to_register()` — uses `register_start_page` from DocumentStructure to discard cover/TOC pages
2. **Find Buildings:** Scan trimmed content for `_BUILDING_HEADER` matches. For ARA format, also run `_detect_ara_buildings()` (looks for "Building Name:" header blocks)
3. **Find Rooms:** For each building section, scan for `_ROOM_HEADER` matches. Extract `room_id`, `name`, `area_m2`
4. **Map Page Ranges:**
```python
# _find_page_at_position(content, char_position) → page number
# Finds the closest _PAGE_PATTERN marker BEFORE the character position
# _find_page_end(building) → last page of this building
# Uses room page data + checks for content after page markers
# Avoids counting trailing markers that belong to next building
```
5. **Classify Complexity:**
```python
def _classify_complexity(building_text: str) -> Tuple[BuildingComplexity, int]:
    # "No Asbestos" at BUILDING level → SIMPLE
    # (NOT individual row "Not Detected" — that's per-record)
    if re.search(r"no\s+asbestos", building_text, re.IGNORECASE):
        return BuildingComplexity.SIMPLE, 0
    # Count ACM items (rows in register tables)
    acm_count = len(re.findall(r"R\d{3,4}", building_text))
    if acm_count > 20:
        return BuildingComplexity.COMPLEX, acm_count
    return BuildingComplexity.COMPLEX, acm_count
```
6. **Create Processing Groups:** Group buildings by page proximity, targeting 3-5 pages per group. Isolate large buildings (B009) into their own group.

| Field | Requires LLM? | Impact |
|-------|--------------|--------|
| `purpose` | Yes — text comprehension | Informational only |
| `area_m2` | Yes — unless in header | Informational only |
| `levels` | Yes — text comprehension | Informational only |
| `construction_type` | Partially — present in header for some formats | Informational only |

---

## 06 / Stage: Page-Level Section Tagging Heuristic

Tags each page with a section_id (0-7) using keyword matching and upstream data.

**File:** `page_tagger.py → _heuristic_tag_all() → _heuristic_tag_page()`

| ID | Section | Heuristic Detection | Confidence |
|----|---------|-------------------|-----------|
| 0 | Cover / TOC | Page 1-2 (no other markers), or contains "Table of Contents" / "Contents" | 0.7 / 0.9 |
| 1 | Introduction | Contains "Introduction" heading | 0.8 |
| 2 | Site Description | Contains "Site Description" heading | 0.8 |
| 3 | Methodology | Contains "Methodology" heading | 0.8 |
| 4 | Register (ACM data) | Contains building headers (B###) OR ACM table data OR falls within BuildingInventory page ranges | 0.9 / 0.85 |
| 5 | Findings / Summary | Contains "Findings" or "Summary" heading after register | 0.7 |
| 6 | Conclusions / Recommendations | Contains "Conclusion" or "Recommendation" heading | 0.7 |
| 7 | Appendix | Contains "Appendix" heading, or after all register content | 0.7 |

**Cross-Validation with Upstream Data:**
- `DocumentStructure.sections` → ground truth anchors (if section(id=4, page_start=13, page_end=30) exists, pages 13-30 pre-tagged as register)
- `BuildingInventory.buildings[].page_start/page_end` → confirms register pages at 0.85 confidence
- `DocumentStructure.register_start_page` → strong anchor for section 4 start

---

## 07 / Stage: Extraction Strategy Routing

Decides how each building gets extracted: LLM, regex-only, or skip.

**File:** `orchestrator.py → plan_extraction() → _determine_strategy()`

### Strategy Selection Logic

```python
def _determine_strategy(building, page_tags) -> ExtractionStrategy:
    # No page tags available → safe default
    if not page_tags:
        return ExtractionStrategy.FULL_LLM

    # Check if ANY of this building's pages are register pages
    building_pages = [
        tag for tag in page_tags.pages
        if building.page_start <= tag.page_number <= building.page_end
    ]
    register_pages = [p for p in building_pages if p.section_id == 4]

    # No register content → skip entirely
    if not register_pages:
        return ExtractionStrategy.SKIP

    # Simple "No Asbestos" buildings → regex extraction only
    if building.complexity == "simple":
        return ExtractionStrategy.REGEX_ONLY

    # Complex buildings → full LLM extraction
    return ExtractionStrategy.FULL_LLM
```

### `should_use_orchestrator()` — ⚠️ REMOVE IN E29-S2

> GAP-1 target: Remove this conditional. Currently gates the dual-path legacy/orchestrator split.

```python
def should_use_orchestrator(state: ExtractionState) -> bool:
    # Returns True if building_inventory is not None AND has 1+ buildings
    # Returns False → routes to legacy prepare → extract → loop path
    return (
        state.get("building_inventory") is not None
        and len(state["building_inventory"].buildings) > 0
    )
```

### `_SAMP_BUILDING_ID` Detection (orchestrator.py)

```python
# SAMP IDs: B00A, B009, D01 — match this pattern
_SAMP_BUILDING_ID = re.compile(r"^[A-Z]\d{2,3}[A-Z]?$")

# ARA buildings (non-SAMP ID) → always FULL_LLM
# SAMP buildings → may get REGEX_ONLY if classified SIMPLE
```

---

## 08 / Stage: SAMP Preprocessing

Text transformations applied BEFORE LLM extraction to improve accuracy.

**File:** `acm_extraction.py → _preprocess_samp_format()`

### `NO_ACCESS_PHRASES` — Marker Injection (E18-S5, Fix A)

Detects "No Access" entries and injects visible markers so the LLM doesn't skip them:

```python
NO_ACCESS_PHRASES = [
    "No access", "No Access", "NO ACCESS",
    "Height restriction", "Height Restriction",
    "Restricted access", "Restricted Access",
    "Live Electrical Hazard",
    "Not accessible", "Not Accessible",
    "Locked", "Unable to access",
]

# Single-pass combined alternation regex (Fix C1 — prevents double markers)
pattern = "|".join(re.escape(phrase) for phrase in NO_ACCESS_PHRASES)
combined_re = re.compile(f"({pattern})", re.IGNORECASE)

# Injects: ">>> NO ACCESS ENTRY: {matched_phrase}" before each matched line
```

### `PRODUCT_NORMALIZATIONS` — Vocabulary Mapping (E18-S5, Fix B)

Normalizes product names in raw text BEFORE LLM sees it:

```python
PRODUCT_NORMALIZATIONS = {
    "Fuses": "Fuse cartridge",       # Plural → canonical
    "Fuse": "Fuse cartridge",        # Standalone (not "Fuse cartridge" which is already correct)
    "Flange mastic": "Flange joints", # Product name variation
}
# Applied via regex with word boundaries to avoid partial matches
```

---

## 09 / Docling Table Data Normalizations

Applied to DataFrames immediately after Docling extraction, BEFORE any LLM processing.

**File:** `source processing (E26) → extract_docling_tables()`

### Fix Split Sample Numbers (100% fixable)

ALL sample numbers from Docling have embedded spaces: `34511-039- 001`.

```python
# Applied to every cell in every DataFrame
df = df.map(
    lambda v: re.sub(r"(\d+)-\s+(\d+)", r"\1-\2", str(v))
    if isinstance(v, str) else v
)
# "34511-039- 001" → "34511-039-001"
```

### Strip "Asbestos " Prefix from Hazard Status

Docling outputs "Asbestos Negative" / "Asbestos Positive" — strip the prefix:

```python
# Applied to columns with "hazard" or "status" in name
for col in df.columns:
    if "hazard" in col.lower() or "status" in col.lower():
        df[col] = df[col].apply(
            lambda v: re.sub(r"^Asbestos\s+", "", str(v))
            if isinstance(v, str) else v
        )
# "Asbestos Negative" → "Negative"
```

### "Same as" ↔ "As Per" Normalization

Docling uses "Same as 34511-039-XXX" where BAR ground truth uses "As Per 34511-039-XXX". Semantic equivalence.

```python
# Deferred to orchestrator/BAR mapper layer (not in source processing)
# Simple string replacement: "Same as" → "As Per"
```

### Column-to-BAR Positional Mapping

Column headers vary per table. Column POSITION is consistent (E25 finding):

```python
# Semantic column mapping by position:
# cols 0-3 = location data (Level, Room, Feature, Item)
# col 4    = hazard type + status
# col 5    = sample number
# col 6    = friability
# Regardless of actual header text
```

---

## 10 / Enum Value Normalization

Normalizes consultant-specific wording to BAR-standard enum values.

**Files:** `normalizers/` (E1-S12) + `acm_schemas.py` (E2-S11)

### Sample Result

| Raw Input | Normalized Output |
|-----------|------------------|
| "positive", "pos" | `Positive` |
| "negative", "neg" | `Negative` |
| "presumed", "presumed positive", "assumed", "not sampled" | `Assumed Positive` |
| "assumed negative" | `Assumed Negative` |

### Material Condition

| Raw Input | Normalized Output |
|-----------|------------------|
| "good" | `Good` |
| "fair" | `Fair` |
| "poor" | `Poor` |
| "-", "n/a" | `None` |

### Disturbance Potential

| Raw Input | Normalized Output | Note |
|-----------|------------------|------|
| "low" | `Low` | |
| "medium" | `Moderate` | **BAR uses "Moderate" not "Medium"!** |
| "high" | `High` | |
| "-" | `None` | |

### Business Rules: Negative Result Cascade

```
If Sample Result is Negative or Assumed Negative:
  → Set Condition to "N/A (negative)" or "N/A (assumed negative)"
  → Set Disturbance Potential to "N/A (negative)" or "N/A (assumed negative)"
```

### Pydantic Validators (acm_schemas.py)

```python
@field_validator("result", mode="before")
@classmethod
def validate_result(cls, v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    normalized = v.strip().title()
    allowed = {"Positive", "Assumed Positive", "Negative", "Assumed Negative", "Unknown"}
    if normalized not in allowed:
        raise ValueError(f"result must be one of {sorted(allowed)}, got '{v}'")
    return normalized

@field_validator("quantity", mode="before")
@classmethod
def validate_quantity(cls, v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    match = re.match(r"^\s*(-?\d+(?:\.\d+)?)", str(v))
    if match and float(match.group(1)) < 0:
        raise ValueError(f"quantity cannot be negative, got '{v}'")
    return v
```

---

## 11 / Product Vocabulary Normalization

Synonym mappings for testing and matching.

**Files:** `test_broadmeadows_e2e.py`, `_preprocess_samp_format()`

```python
PRODUCT_SYNONYMS = {
    "flange joints": "flange mastic",
    "flange mastic": "flange joints",
    "fuse cartridge": "fuses",
    "fuses": "fuse cartridge",
    "internal lining": "internal lining",
    # ... covers common variations
}
# Used in Tier 2.5 matching: if exact match fails, try synonym-normalized version
```

---

## 12 / Hygienist Action Classification

Regex-based classification of free-text hygienist recommendations into canonical action codes.

**File:** `normalizers/ → consultant_wording_rules.json` (E1-S12)

| Regex Pattern | Canonical Action |
|--------------|----------------|
| `\bLeave undisturbed\b\|\bno action\b\|\bMonitor\b\|\bmanage.*in\s*situ\b` | `leave_undisturbed_and_manage` |
| `\bMaintain.*into an AMP\b` | `maintain_in_situ` |
| `\bRemove (under\|by) .*licensed asbestos removal contractor\b` | `remove_prior_to_refurb_or_demolition` |
| `\bprior to demolition or refurbishment\b` | `remove_prior_to_refurb_or_demolition` |
| `\bRestrict access\b\|\bASAP\b` | `restrict_access_immediately` |
| `\bwithin\s*3\s*months\b\|\bnext few months\b` | `remedial_within_months` |
| `\bConfirm status\b\|\bNot Sampled\b\|\bPresumed\b` | `confirm_status_sampling` |
| `\bHeight restriction\b\|\bRestricted Access\b\|\bLive Electrical Hazard\b` | `height_or_access_restriction` |
| `\bcontrolled bonded asbestos removal conditions\b` | `remove_prior_to_refurb_or_demolition` |
| (no match) | `review_required` |

**Rules:** Case-insensitive (`re.IGNORECASE`). Checked in priority order — first match wins. Stores both raw text (in `hygienist_recommendations`) and canonical code (in `normalized_action`).

---

## 13 / Product Taxonomy Regex Classification

60+ regex patterns classifying ACM products into BAR taxonomy groups. Primary method (~80% hit rate); LLM fallback for ambiguous items.

**File:** `normalizers/taxonomy.py` (E1-S9)

### Non-Friable Taxonomy (T1-T8)

| Pattern | Group | Product Type |
|---------|-------|-------------|
| `vinyl\s*(sheet\|flooring)` | T3 Vinyl products | Vinyl sheet |
| `vinyl\s*tile` | T3 Vinyl products | Vinyl Tiles |
| `linoleum` | T3 Vinyl products | Vinyl sheet |
| `(fibre\|fiber)\s*cement\|fc\s*sheet` | T1 Cement products | Flat Sheeting |
| `corrugated.*roof` | T1 Cement products | Corrugated Roof Sheeting |
| `weatherboard` | T1 Cement products | Weatherboards |
| `mastic` | T4 Gasket, friction products | Mastic |
| `gasket` | T4 Gasket, friction products | Gasket(s) |
| `bitumen\|bituminous` | T2 Bitumen products | Bituminous Membrane |
| `malthoid` | T2 Bitumen products | Malthoid |
| `millboard` | T8 Insulation | Millboard |

### Friable Taxonomy (T1-T6)

| Pattern | Group | Product Type |
|---------|-------|-------------|
| `lagging` | T3 Insulation products (f) | Lagging |
| `vermiculite` | T3 Insulation products (f) | Vermiculite |

> **Full list:** 60+ patterns in `normalizers/taxonomy.py → CLASSIFICATION_PATTERNS`

### Classification Flow

```python
def classify_product(item_description: str, friability: str) -> tuple[str, str]:
    # 1. Select taxonomy based on friability
    if friability == "Friable":
        taxonomy = FRIABLE_TAXONOMY  # T1-T6
    else:
        taxonomy = NONFRIABLE_TAXONOMY  # T1-T8 (default)

    # 2. Try regex patterns (primary, ~80% hit rate)
    for pattern, ftype, group, ptype in CLASSIFICATION_PATTERNS:
        if re.search(pattern, item_description, re.IGNORECASE):
            if ftype matches friability:
                return (group, ptype)  # confidence: 0.9

    # 3. LLM fallback for ambiguous items (confidence: varies)
    return await _llm_classify(item_description, friability)
    # If LLM confidence < 0.7 → flag for manual review
```

---

## 14 / Friability Rules

**Handled by `taxonomy._normalize_friability()` — do NOT duplicate this logic elsewhere.**

**File:** `normalizers/taxonomy.py`

| Raw Input | Normalized | Taxonomy |
|-----------|-----------|---------|
| "Friable", "friable", "F" | `Friable` | T1-T6 Friable |
| "Non-friable", "Non Friable", "NF", "non-friable" | `Non-friable` | T1-T8 Non-friable |
| null, empty, unknown | `Non-friable` (default) | T1-T8 Non-friable |

---

## 15 / Deduplication

Removes duplicate records using a composite key.

**File:** `acm_extraction.py → deduplicate stage`

### Dedup Composite Key (E26 fix — CURRENT)

```python
# Pre-E26: room + product + sample_number (3 fields)
# PROBLEM: Record #8 (Switch Room/Switchboard/Fuse) and
# Record #9 (Switch Room/Battery Charger/Fuse) had identical keys
# because both shared room + product + empty sample.

# Post-E26 (current): room + product + location + sample_number (4 fields)
dedup_key = f"{record.room_name}|{record.product}|{record.location}|{record.sample_number}"

# On duplicate detection: keep record with higher confidence, merge data_issues
```

**E26 Fix Impact:** Adding `location` to the dedup key changed Broadmeadows from 31 raw → 28 after dedup (losing 3 real records) to 31 raw → 30 after dedup (only losing 1 true duplicate). This single change recovered 2 records.

---

## 16 / No-Access Record Recovery

Post-dedup regex scan that catches "No Access" entries the LLM missed.

**File:** `acm_extraction.py → _recover_no_access_records()` (E26-S6, Fix 3)

```python
# Scans source.full_text for patterns like:
# "Room Adjacent Disabled Toilet" + "No Access" within nearby lines
# "Lift Foyer" + "No access - Height restriction"

# Creates new ACMExtractionRecord with:
# result = "Assumed Positive"
# data_issues = "No access - recovered by regex fallback"

# Dedup check: only adds if (room + product + location) key
# not already present in extracted records

# E26 result: recovered Record #31 (Disabled Toilet)
# Also caught false-positive Ceiling Space record (already extracted — harmless)
```

---

## 17 / Pydantic Schema Validation

Validates extracted records against `ACMExtractionRecord` schema. Failed records go to corrective LLM loop.

**Files:** `acm_schemas.py`, `acm_extraction.py → validate_records`

### Required Fields

| Field | Required? | On Failure |
|-------|----------|-----------|
| `building_id` | Yes | Record rejected |
| `room_id` or `room_name` | Yes (at least one) | Record rejected |
| `product` | Yes | Record rejected |
| `result` | Yes | Sent to corrective loop |

### Confidence Assignment

```python
# high: All required fields present, clear source text
# medium: Required fields present but some ambiguity
# low: Required fields inferred from context, uncertain

# Invalid records logged but NOT saved (with full context for debugging)
```

---

## Quick Reference: Files Index

| File | Purpose | Key Patterns |
|------|---------|-------------|
| `document_structure.py` | Document structure analysis | `_PAGE_PATTERN` (canonical), `_heuristic_fallback()` |
| `building_inventory.py` | Building discovery and page mapping | `_BUILDING_HEADER`, `_ROOM_HEADER`, `_heuristic_fallback()` |
| `page_tagger.py` | Page section classification | `_split_into_pages()`, `_heuristic_tag_all()` |
| `orchestrator.py` | Extraction strategy routing | `should_use_orchestrator()` ⚠️, `_determine_strategy()`, `ROOM_ENTRY_PATTERN` |
| `acm_extraction.py` | Main extraction pipeline | `_preprocess_samp_format()`, `_recover_no_access_records()`, dedup |
| `acm_extractor.py` | Regex parser extraction | `BUILDING_PATTERN`, `ROOM_PATTERN`, `AREA_TYPE_PATTERN`, `SCHOOL_PATTERN` |
| `acm_schemas.py` | Pydantic validation | `validate_result()`, `validate_quantity()` |
| `normalizers/taxonomy.py` | Product classification | `CLASSIFICATION_PATTERNS`, `_normalize_friability()` |
| `normalizers/consultant_wording_rules.json` | Action classification | Hygienist recommendation regex patterns |
| `metadata_extractor.py` | Address and report reference extraction | `ADDRESS_PATTERN`, `REPORT_REF_PATTERNS` |

> ⚠️ Items marked for removal in E29-S2: `should_use_orchestrator()`, legacy `prepare_context()`, legacy `extract_records()` nodes

---

*Last updated: March 2026 · Reflects E26 pipeline state · E29 changes noted inline*
