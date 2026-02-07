# Story 1.12: Consultant Wording Normalization

Status: ready-for-dev

## Story

As a **system**,
I want **to normalize consultant recommendations to canonical actions using regex pattern matching**,
so that **hygienist recommendations are consistent across different consultant formats (Prensa, Greencap, etc.) and BAR exports contain standardized action codes**.

## Acceptance Criteria

### AC1: Define Canonical Action Enum
- [ ] Define 6 canonical actions as a string enum/literal type:
  - `maintain_in_situ` - Keep ACM in place and manage under AMP; label; periodic review
  - `remove_prior_to_refurb_or_demolition` - Remove ACM before demolition/refurbishment by licensed contractor
  - `restrict_access_immediately` - Restrict access and arrange abatement ASAP
  - `remedial_within_months` - Organise remedial/removal works within ~3 months
  - `confirm_status_sampling` - Item not sampled; confirm via sampling/investigation
  - `height_or_access_restriction` - No access/height restriction; treat as presumed
- [ ] Include `review_required` as fallback for unmatched recommendations

### AC2: Regex Pattern Matching Engine
- [ ] Implement `normalize_recommendation(raw_text: str) -> NormalizationResult` function
- [ ] At minimum, 9 regex patterns from `consultant_wording_rules.json`:
  - `\bMaintain in current condition\b` → `maintain_in_situ`
  - `\blabel( and incorporate)? into an AMP\b` → `maintain_in_situ`
  - `\bRemove (under|by) .*licensed asbestos removal contractor\b` → `remove_prior_to_refurb_or_demolition`
  - `\bprior to demolition or refurbishment\b` → `remove_prior_to_refurb_or_demolition`
  - `\bRestrict access\b|\bASAP\b` → `restrict_access_immediately`
  - `\bwithin\s*3\s*months\b|\bnext few months\b` → `remedial_within_months`
  - `\bConfirm status\b|\bNot Sampled\b|\bPresumed\b` → `confirm_status_sampling`
  - `\bHeight restriction\b|\bRestricted Access\b|\bLive Electrical Hazard\b` → `height_or_access_restriction`
  - `\bcontrolled bonded asbestos removal conditions\b` → `remove_prior_to_refurb_or_demolition`
- [ ] Pattern matching is case-insensitive (`re.IGNORECASE`)
- [ ] Returns first matching action (patterns checked in priority order)
- [ ] Returns `review_required` if no patterns match

### AC3: Enum Value Normalization
- [ ] Implement `normalize_enum_value(raw_value: str, field_name: str) -> Optional[str]` function
- [ ] Normalize Sample Result synonyms:
  - "positive" / "pos" → `"Positive"`
  - "negative" / "neg" → `"Negative"`
  - "presumed" / "presumed positive" / "assumed" / "not sampled" → `"Assumed Positive"`
- [ ] Normalize Condition synonyms:
  - "good" → `"Good"`, "fair" → `"Fair"`, "poor" → `"Poor"`
  - "-" / "n/a" → `None`
- [ ] Normalize Disturbance Potential synonyms:
  - "low" → `"Low"`, "medium" → `"Moderate"` (BAR uses "Moderate" not "Medium"), "high" → `"High"`
  - "-" → `None`
- [ ] Normalize Friability: already handled by `taxonomy._normalize_friability()` — reuse, do not duplicate

### AC4: Dual Storage (Raw + Normalized)
- [ ] `NormalizationResult` stores both raw text and normalized value
- [ ] Domain model `ACMRecord.hygienist_recommendations` keeps raw text
- [ ] New field `ACMRecord.normalized_action` stores canonical action string
- [ ] SurrealDB migration adds `normalized_action` field to `acm_record` table
- [ ] Index on `normalized_action` for filtering

### AC5: Custom Pattern Configuration
- [ ] Patterns loaded from `consultant_wording_rules.json` at runtime
- [ ] Pattern file path resolved relative to project root (same as taxonomy.py)
- [ ] Cached after first load (singleton pattern, same as `_load_taxonomy_files()`)
- [ ] Graceful fallback to hardcoded defaults if JSON file missing

### AC6: Integration with Extraction Pipeline
- [ ] Normalization called during ACM record creation in `acm_extractor.py`
- [ ] Called after field extraction but alongside existing `classify_product()` call
- [ ] Both recommendation normalization and enum normalization applied
- [ ] All existing tests continue to pass (backward compatible — new fields are Optional)

### AC7: API Endpoint for Normalization
- [ ] `POST /api/acm/normalize` endpoint accepts raw recommendation text
- [ ] Returns `{ "raw": "...", "normalized_action": "...", "confidence": 1.0, "method": "pattern" }`
- [ ] Useful for testing and debugging normalization rules

### AC8: Comprehensive Testing
- [ ] Unit tests for each canonical action pattern
- [ ] Unit tests for all enum synonym mappings (SampleResult, Condition, DisturbancePotential)
- [ ] Edge cases: empty strings, None, multi-sentence recommendations, mixed-case
- [ ] Test custom pattern loading from JSON
- [ ] Test fallback to `review_required` for unmatched text
- [ ] Integration test: full extraction → normalization → ACMRecord with normalized fields

## Tasks / Subtasks

- [ ] Task 1: Create recommendation normalizer module (AC: 1, 2, 5)
  - [ ] Create `open_notebook/extractors/normalizers/recommendations.py`
  - [ ] Define `NormalizationResult` NamedTuple (match `ClassificationResult` pattern from taxonomy.py)
  - [ ] Define `CANONICAL_ACTIONS` Literal type with 6 actions + `review_required`
  - [ ] Implement `_load_wording_rules()` to load from `consultant_wording_rules.json` (cached singleton)
  - [ ] Implement `normalize_recommendation()` with regex pattern matching
  - [ ] Add logging for normalization decisions
- [ ] Task 2: Create enum normalizer module (AC: 3)
  - [ ] Create `open_notebook/extractors/normalizers/enums.py`
  - [ ] Define synonym dictionaries: `SAMPLE_RESULT_SYNONYMS`, `CONDITION_SYNONYMS`, `DISTURBANCE_SYNONYMS`
  - [ ] Implement `normalize_enum_value(raw_value, field_name)` function
  - [ ] Reuse `_normalize_friability()` from taxonomy.py (do not duplicate)
- [ ] Task 3: Update normalizers package exports (AC: 1, 2, 3)
  - [ ] Update `open_notebook/extractors/normalizers/__init__.py` to export new functions
- [ ] Task 4: Domain model update (AC: 4)
  - [ ] Add `normalized_action: Optional[str]` field to `ACMRecord` in `open_notebook/domain/acm.py`
  - [ ] Create SurrealDB migration for `normalized_action` field + index
- [ ] Task 5: Extraction pipeline integration (AC: 6)
  - [ ] Modify `open_notebook/extractors/acm_extractor.py` to call `normalize_recommendation()` on `hygienist_recommendations`
  - [ ] Modify extraction to call `normalize_enum_value()` on sample_result, condition, disturbance_potential
  - [ ] Ensure backward compatibility — new fields default to None
- [ ] Task 6: API endpoint (AC: 7)
  - [ ] Add `POST /api/acm/normalize` endpoint to `api/routers/acm.py`
  - [ ] Add request/response models to `api/models.py` or inline
- [ ] Task 7: Comprehensive tests (AC: 8)
  - [ ] Create `tests/test_recommendations_normalizer.py`
  - [ ] Create `tests/test_enum_normalizer.py`
  - [ ] Add integration tests in `tests/test_acm_extractor.py`
  - [ ] Run full test suite for zero regressions

## Dev Notes

### CRITICAL: Correct File Locations

The architecture document references `open_notebook/extraction/normalizers/` but the **ACTUAL codebase** uses `open_notebook/extractors/normalizers/`. All new files MUST go under:

```
open_notebook/extractors/normalizers/
├── __init__.py              # UPDATE: Add new exports
├── taxonomy.py              # EXISTING: Product classification (E1-S9) — DO NOT MODIFY
├── recommendations.py       # NEW: Recommendation normalization
└── enums.py                 # NEW: Enum value normalization
```

**DO NOT** create `open_notebook/extraction/` — that path does not exist.

### Existing Code to Understand Before Modifying

| File | Why | Key Details |
|------|-----|-------------|
| `open_notebook/extractors/normalizers/taxonomy.py` | **Pattern to replicate** | `ClassificationResult` NamedTuple, `_load_taxonomy_files()` cached singleton, pattern matching with `re.search()`, `CLASSIFICATION_PATTERNS` list |
| `open_notebook/extractors/normalizers/__init__.py` | **Must update** | Currently exports only taxonomy functions |
| `open_notebook/extractors/acm_extractor.py` | **Integration point** | `extract_acm_records()` entry point, `_extract_from_markdown()` main logic, calls `classify_product()` |
| `open_notebook/domain/acm.py` | **Add `normalized_action` field** | `ACMRecord(ObjectModel)` Pydantic model with 50+ fields |
| `docs/samplePDF/instructions-sample/consultant_wording_rules.json` | **Pattern source** | 6 universal_actions, 9 consultant_phrases_to_actions patterns |
| `docs/samplePDF/instructions-sample/register_enums.json` | **Enum reference** | SampleResult, Condition, DisturbancePotential, Friability enum values |
| `api/routers/acm.py` | **Add normalize endpoint** | Existing `/classify`, `/classify/batch`, `/taxonomy` endpoints (follow same pattern) |
| `tests/test_taxonomy.py` | **Test pattern to follow** | `TestNormalizeFriability`, `TestClassifyProduct` classes with pytest |

### Implementation Patterns (Follow Existing taxonomy.py)

**NormalizationResult (match ClassificationResult pattern):**
```python
class NormalizationResult(NamedTuple):
    """Result of recommendation normalization."""
    raw_text: str
    normalized_action: Optional[str]  # canonical action or "review_required"
    confidence: float  # 1.0 for pattern match, 0.0 for no match
    method: Literal["pattern", "config", "none"]
```

**Cached JSON Loading (match _load_taxonomy_files pattern):**
```python
_WORDING_RULES: Optional[dict] = None

def _load_wording_rules() -> dict:
    """Load consultant wording rules JSON. Cached after first load."""
    global _WORDING_RULES
    if _WORDING_RULES is not None:
        return _WORDING_RULES

    project_root = Path(__file__).parent.parent.parent.parent
    rules_path = project_root / "docs" / "samplePDF" / "instructions-sample" / "consultant_wording_rules.json"

    try:
        with open(rules_path, encoding="utf-8") as f:
            _WORDING_RULES = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Wording rules not found: {e}. Using defaults.")
        _WORDING_RULES = {"consultant_phrases_to_actions": [], "universal_actions": []}

    return _WORDING_RULES
```

**Regex Pattern Matching:**
```python
def normalize_recommendation(raw_recommendation: str) -> NormalizationResult:
    """Map consultant wording to canonical action."""
    if not raw_recommendation or not raw_recommendation.strip():
        return NormalizationResult(raw_text="", normalized_action=None, confidence=0.0, method="none")

    rules = _load_wording_rules()
    for rule in rules.get("consultant_phrases_to_actions", []):
        pattern = rule["pattern"]
        action = rule["action"]
        if re.search(pattern, raw_recommendation, re.IGNORECASE):
            return NormalizationResult(
                raw_text=raw_recommendation,
                normalized_action=action,
                confidence=1.0,
                method="config"
            )

    # Fallback to hardcoded patterns...
    for pattern, action in DEFAULT_PATTERNS:
        if re.search(pattern, raw_recommendation, re.IGNORECASE):
            return NormalizationResult(
                raw_text=raw_recommendation,
                normalized_action=action,
                confidence=1.0,
                method="pattern"
            )

    return NormalizationResult(
        raw_text=raw_recommendation,
        normalized_action="review_required",
        confidence=0.0,
        method="none"
    )
```

### Enum Normalization Dictionaries

**From `extraction-pipeline.md` and `register_enums.json`:**

```python
SAMPLE_RESULT_SYNONYMS = {
    "positive": "Positive",
    "pos": "Positive",
    "detected": "Positive",
    "negative": "Negative",
    "neg": "Negative",
    "not detected": "Negative",
    "presumed": "Assumed Positive",
    "presumed positive": "Assumed Positive",
    "assumed": "Assumed Positive",
    "assumed positive": "Assumed Positive",
    "not sampled": "Assumed Positive",
}

CONDITION_SYNONYMS = {
    "good": "Good",
    "fair": "Fair",
    "poor": "Poor",
    "unknown": "Unknown",
    "-": None,
    "n/a": None,
    "na": None,
}

DISTURBANCE_SYNONYMS = {
    "low": "Low",
    "medium": "Moderate",     # BAR uses "Moderate" NOT "Medium"
    "moderate": "Moderate",
    "high": "High",
    "unknown": "Unknown",
    "-": None,
    "n/a": None,
}
```

### SurrealDB Migration

Next available migration number — check existing migrations to find the highest number, then use the next one.

```sql
-- Migration: Add normalized_action field to acm_record
DEFINE FIELD normalized_action ON acm_record TYPE option<string>;
DEFINE INDEX acm_normalized_action ON acm_record FIELDS normalized_action;
```

### Integration Point in acm_extractor.py

The normalization should be applied at record creation time, alongside the existing `classify_product()` call. Example integration:

```python
# After extracting record fields...
from open_notebook.extractors.normalizers import normalize_recommendation, normalize_enum_value

# Normalize enum fields
record["sample_result"] = normalize_enum_value(record.get("sample_result"), "sample_result")
record["material_condition"] = normalize_enum_value(record.get("material_condition"), "condition")
record["disturbance_potential"] = normalize_enum_value(record.get("disturbance_potential"), "disturbance_potential")

# Normalize recommendation
if record.get("hygienist_recommendations"):
    norm_result = normalize_recommendation(record["hygienist_recommendations"])
    record["normalized_action"] = norm_result.normalized_action
```

### Business Rules to Apply AFTER Normalization

From PRD and extraction-pipeline.md — these are NOT part of this story but inform the normalization:
- If `sample_result` is `"Negative"` or `"Assumed Negative"`:
  - Set `material_condition` to `"N/A (negative)"` or `"N/A (assumed negative)"`
  - Set `disturbance_potential` to `"N/A (negative)"` or `"N/A (assumed negative)"`

These business rules are applied by `apply_business_rules()` in Stage 2, which runs after normalization. This story provides the normalized inputs that those rules depend on.

### What This Story Does NOT Include

- **Parser framework** (E1-S11) — that's a separate story for consultant-specific extraction
- **LLM fallback** for recommendation normalization — pattern matching only for now
- **Business rules application** — that's part of Stage 2 pipeline (E1-S3)
- **BAR export changes** — E5-S3/E5-S4 handle export configuration
- **HTML table parsing** (MinerU output) — future enhancement
- **Frontend UI changes** — no UI impact, backend-only story

### Dependencies

| Story | Relationship | Status |
|-------|-------------|--------|
| E1-S3 (Two-Stage Pipeline) | **Depends on** — needs extraction pipeline infrastructure | Done |
| E1-S9 (Product Classification) | **Pattern reference** — follow taxonomy.py architecture | Done |
| E1-S11 (Parser Framework) | **Works with** — parsers extract raw recommendations, this normalizes them | Ready-for-dev |
| E5-S2 (Excel Export) | **Blocks** — normalized actions needed for complete BAR compliance | Done (but will benefit from this) |

### Previous Story Learnings (E1-S9, E1-S10)

1. **Follow `taxonomy.py` exactly** — NamedTuple result, cached JSON loading, regex patterns with `re.search()` + `re.IGNORECASE`
2. **Keep all new fields Optional** — backward compatibility with existing records is critical
3. **Test count matters** — E1-S9 taxonomy tests have 22 test classes. Aim for equivalent coverage
4. **Regex patterns need word boundaries** — Use `\b` to prevent partial matches (e.g., `\bfibro\b` not `fibro`)
5. **MinerU fallback chain works** — same graceful degradation pattern for JSON file loading

### Project Structure Notes

- **All normalizers** go in `open_notebook/extractors/normalizers/` (existing package)
- **Tests** follow existing pattern: `tests/test_*.py` with pytest
- **API endpoints** follow existing pattern in `api/routers/acm.py` (see `/classify` endpoint)
- **Migrations** are numbered sequentially in `migrations/` directory

### References

- [Source: _bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md#E1-S12]
- [Source: _bmad-output/project-planning-artifacts/acm-ai/04-architecture.md#5.1.2-Stage-2-INTERPRET]
- [Source: _bmad-output/project-planning-artifacts/acm-ai/03-prd.md#5.5-Enum-Definitions]
- [Source: docs/reference/extraction-pipeline.md#Stage-2-INTERPRET]
- [Source: docs/samplePDF/instructions-sample/consultant_wording_rules.json]
- [Source: docs/samplePDF/instructions-sample/register_enums.json]
- [Source: open_notebook/extractors/normalizers/taxonomy.py]
- [Source: open_notebook/domain/acm.py]
- [Source: tests/test_taxonomy.py]

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

(to be filled by dev agent)

### Completion Notes List

(to be filled by dev agent)

### File List

**Files to Create:**
- `open_notebook/extractors/normalizers/recommendations.py`
- `open_notebook/extractors/normalizers/enums.py`
- `tests/test_recommendations_normalizer.py`
- `tests/test_enum_normalizer.py`
- `migrations/15.surrealql` (next available migration number — verify before creating)
- `migrations/15_down.surrealql`

**Files to Modify:**
- `open_notebook/extractors/normalizers/__init__.py` — add new exports
- `open_notebook/extractors/acm_extractor.py` — integrate normalization calls
- `open_notebook/domain/acm.py` — add `normalized_action` field
- `api/routers/acm.py` — add `/normalize` endpoint
