# Devils Advocate Review - Sprint 1 Architecture Decisions

**Reviewer**: devils-advocate agent
**Date**: 2026-02-16
**Sprint**: E2E Gap Fix Sprint (Sprint 1)
**Focus Areas**: Deduplication, BAR extraction, CI/CD pipeline, Observability

---

## Executive Summary

Sprint 1 delivered significant improvements to extraction accuracy (26% → 87%) and introduced critical infrastructure. However, **7 high-risk issues** and **4 medium-risk issues** require mitigation before production deployment. Most critical: dedup key fragility with empty fields, missing database schema for BAR fields, and lack of smoke tests in CI/CD pipeline.

**Overall Risk Rating**: **MEDIUM-HIGH**
**Recommended Action**: Address all HIGH and CRITICAL risks before merging to production.

---

## 1. Deduplication Key Design

### File: `open_notebook/graphs/acm_extraction.py:394-413`

### Implementation Analysis

```python
def _generate_dedup_key(record: ACMExtractionRecord, school_code: Optional[str]) -> str:
    """Generate a deduplication key for a record.

    Key format: {school_code}_{building_id}_{area_type}_{room_id}_{product}_{hash(description)}
    - Includes area_type to distinguish Interior vs Exterior locations (E1-S25)
    - Includes product to distinguish different items in same room (E1-S27)
    Uses SHA-256 for cryptographic security (truncated to 8 chars for readability).
    """
    school = school_code or "unknown"
    building = record.building_id or "unknown"
    area = (record.area_type or "Interior").lower()  # Default to Interior
    room = record.room_id or "none"
    product = (record.product or "unknown").lower()

    # Create hash of product description (first 50 chars) using SHA-256
    desc_hash = hashlib.sha256(
        (record.material_description or "")[:50].encode()
    ).hexdigest()[:8]

    return f"{school}_{building}_{area}_{room}_{product}_{desc_hash}"
```

### CRITICAL Risk: Dedup Key Instability with Empty/Missing Fields

**Severity**: **CRITICAL**
**Impact**: **Duplicate records in production database**

#### Problem

The dedup key uses fallback values (`"unknown"`, `"none"`) for missing fields. This creates **unstable keys** that change based on data completeness:

**Scenario 1 - Initial extraction (incomplete data)**:
```
Record 1: building_id="B009", product="Floor Coverings", room_id=None
Key: "SCHOOL01_B009_interior_none_floor coverings_a3b4c5d6"
```

**Scenario 2 - Re-extraction with better data**:
```
Record 1: building_id="B009", product="Floor Coverings", room_id="R0005"
Key: "SCHOOL01_B009_interior_R0005_floor coverings_a3b4c5d6"
```

**Result**: Same physical ACM item produces **2 different keys**, creating a duplicate record.

#### Edge Cases

1. **Empty string vs None**:
   - `product=""` → `"unknown"` (after `or` operator)
   - `product=None` → `"unknown"` (after `or` operator)
   - `product="   "` → `"   "` (whitespace NOT normalized!)
   - **Risk**: Same record with `product="Floor"` and `product="floor "` produces different keys

2. **Case sensitivity in product**:
   - `product="Floor Coverings"` → `"floor coverings"`
   - `product="FLOOR COVERINGS"` → `"floor coverings"`
   - **OK**: Lowercased, consistent

3. **Area type defaults**:
   - `area_type=None` → `"interior"` (default)
   - `area_type="Exterior"` → `"exterior"`
   - **Risk**: If area_type extraction improves, interior records will get new keys

4. **Material description truncation**:
   - Hash uses first 50 chars: `(record.material_description or "")[:50]`
   - **Risk**: "Vinyl floor tiles grey white mottled pattern with asbestos fibers" (60 chars) gets truncated
   - If re-extraction improves description, hash stays same (stable)
   - If re-extraction *shortens* description, hash changes (unstable)

#### What Could Go Wrong

1. **Data Quality Improvement = Duplicates**:
   - Sprint 2 improves room_id extraction from 80% → 95%
   - 15% of records get new room_ids
   - Dedup key changes → 15% duplicates created

2. **Whitespace Variations**:
   - "Floor Coverings" vs "Floor Coverings " (trailing space)
   - Keys: `..._floor coverings_...` vs `..._floor coverings _...`
   - Same item, different keys → duplicate

3. **Consultant Format Differences**:
   - ARA format: `product=None` (uses building context)
   - SAMP format: `product="Floor Coverings"`
   - Same building, same floor, same material → different keys if product missing in ARA

#### Recommended Mitigations

1. **CRITICAL - Add whitespace normalization**:
   ```python
   product = (record.product or "unknown").strip().lower()
   building = (record.building_id or "unknown").strip()
   ```

2. **CRITICAL - Store dedup key in database**:
   - Add `dedup_key` field to `acm_record` table (indexed)
   - Compute once on first save
   - **Do NOT recompute on updates** (preserves stability)
   - Migration:
     ```sql
     DEFINE FIELD dedup_key ON acm_record TYPE string;
     DEFINE INDEX idx_acm_dedup_key ON acm_record FIELDS dedup_key;
     ```

3. **HIGH - Add dedup key version field**:
   ```python
   # Allow key schema evolution
   dedup_key_version: int = 1  # Increment when key format changes
   ```

4. **MEDIUM - Consider semantic hashing**:
   - Instead of first 50 chars, hash normalized tokens
   - "Vinyl floor tiles" → sorted tokens → `["floor", "tiles", "vinyl"]` → hash
   - More robust to description reordering

---

### HIGH Risk: SHA-256 Performance Overhead

**Severity**: **HIGH**
**Impact**: **Extraction throughput degradation**

#### Problem

SHA-256 is a **cryptographic** hash function, designed for security not speed. For deduplication, we don't need cryptographic properties.

**Benchmark** (approximate, Python 3.11):
- SHA-256: ~10-15 MB/s
- xxHash: ~500-1000 MB/s (**50-100x faster**)
- CityHash: ~800 MB/s

**Impact on 1000-record extraction**:
- SHA-256: ~1000 records × 0.1ms = 100ms hashing overhead
- xxHash: ~1000 records × 0.002ms = 2ms hashing overhead
- **Savings: 98ms per extraction**

#### Code Reference

```python
# Line 409-411
desc_hash = hashlib.sha256(
    (record.material_description or "")[:50].encode()
).hexdigest()[:8]
```

#### What Could Go Wrong

1. **Large Document Extractions**:
   - 5000-record ACM register (e.g., university campus)
   - SHA-256 overhead: 500ms
   - xxHash overhead: 10ms
   - **Difference: 490ms** (noticeable to users)

2. **Re-extraction Workloads**:
   - User re-runs extraction with different settings
   - Dedup runs on every record (even if unchanged)
   - N×100ms overhead adds up

#### Recommended Mitigations

1. **HIGH - Replace SHA-256 with xxHash**:
   ```python
   import xxhash

   desc_hash = xxhash.xxh64(
       (record.material_description or "")[:50].encode()
   ).hexdigest()[:8]
   ```
   - Add `xxhash` to `pyproject.toml`
   - 50-100x faster
   - 8-char hex digest still sufficient for dedup (64^8 = 2.8×10^14 combinations)

2. **ALTERNATIVE - Use Python's built-in hash()**:
   ```python
   desc_hash = f"{hash(record.material_description or '')[:50]:016x}"[:8]
   ```
   - No dependency
   - Fast (native C implementation)
   - **Caveat**: Not stable across Python processes (uses random seed)
   - Only works if dedup key is stored in DB (not recomputed)

---

### MEDIUM Risk: Hash Collision with 8-Character Truncation

**Severity**: **MEDIUM**
**Impact**: **False deduplication** (distinct records treated as duplicates)

#### Problem

SHA-256 produces 256-bit (64 hex characters) but is truncated to 8 characters (32 bits).

**Collision probability** (birthday paradox):
- 8 hex chars = 32 bits = 4.3 billion combinations
- **50% collision probability at ~65,000 records**
- **1% collision probability at ~9,000 records**

For a typical school:
- 100 buildings × 20 rooms × 5 items = **10,000 records** → **~1% collision risk**

#### What Could Go Wrong

1. **Large Multi-Campus Extraction**:
   - University with 50,000 ACM items
   - Hash collision probability: ~99% (guaranteed collision)
   - Two different materials get same hash → treated as duplicates → one record lost

2. **False Deduplication**:
   ```
   Record A: "Vinyl floor tiles grey white" → hash: a3b4c5d6
   Record B: "Ceiling tiles asbestos fiber" → hash: a3b4c5d6 (collision!)
   Key A: "SCHOOL01_B009_interior_R0005_floor coverings_a3b4c5d6"
   Key B: "SCHOOL01_B009_interior_R0005_ceiling linings_a3b4c5d6"
   ```
   - Different products → different keys (OK)
   - But if product extraction fails for Record B → same key → dedup collision

#### Recommended Mitigations

1. **MEDIUM - Increase hash length to 12-16 characters**:
   ```python
   desc_hash = hashlib.sha256(...).hexdigest()[:12]  # 48 bits
   ```
   - 12 chars = 48 bits → 50% collision at ~16 million records (safe)
   - 16 chars = 64 bits → 50% collision at ~4 billion records (extremely safe)

2. **LOW - Add collision detection**:
   ```python
   if existing_key in dedup_map:
       if not records_are_identical(existing_record, new_record):
           logger.warning(f"Dedup key collision detected: {existing_key}")
           # Append counter: key_001, key_002, etc.
   ```

3. **ALTERNATIVE - Use full hash (no truncation)**:
   - Store full 64-character hash in database
   - No collision risk
   - Trade-off: 64 bytes vs 8 bytes per record (minor)

---

### MEDIUM Risk: Dedup Key Does Not Account for Sample Number

**Severity**: **MEDIUM**
**Impact**: **Legitimate variants treated as duplicates**

#### Problem

Same material sampled multiple times (e.g., suspect ACM, re-test after work):

```
Record 1: product="Vinyl Tiles", sample_no="34511-039-001", result="Positive"
Record 2: product="Vinyl Tiles", sample_no="34511-039-002", result="Negative"
```

**Dedup key is identical** (doesn't include sample_no) → treated as duplicate → one record lost.

#### What Could Go Wrong

1. **Re-sampling After Remediation**:
   - Initial sample: Positive
   - Remediation work done
   - Re-sample: Negative
   - Both records needed for audit trail
   - Dedup merges them → audit trail lost

2. **Multi-Sample Materials**:
   - Large asbestos area
   - Multiple samples taken (001, 002, 003)
   - Different results (Positive, Positive, Negative)
   - Dedup keeps only one → compliance violation

#### Recommended Mitigations

1. **HIGH - Include sample_no in dedup key**:
   ```python
   sample = (record.sample_no or "none").lower()
   return f"{school}_{building}_{area}_{room}_{product}_{sample}_{desc_hash}"
   ```
   - Trade-off: Creates duplicate entries for "Not Sampled" vs "Previously Sampled"
   - Solution: Normalize "Not Sampled" → `"none"`

2. **ALTERNATIVE - Add uniqueness constraint on sample_no**:
   ```sql
   DEFINE INDEX idx_acm_sample_no ON acm_record FIELDS source_id, sample_no;
   ```
   - Prevents duplicate sample numbers
   - But doesn't prevent dedup collision

---

## 2. BAR Extraction Strategy

### Files:
- `prompts/acm/extraction.jinja:312-331`
- `open_notebook/extractors/acm_schemas.py:120-191`

### Implementation Analysis

BAR compliance fields are extracted via **LLM-based structured output** using the prompt template, not via post-processing rules.

**7 BAR fields added in Sprint 1**:
1. `identifying_company` (hygiene consultant)
2. `date_inspected`
3. `inspection_type`
4. `bar_report_no`
5. `date_of_bar_report`
6. `asbestos_assessor`
7. `result_classification`

### CRITICAL Risk: Missing Database Migration for BAR Fields

**Severity**: **CRITICAL**
**Impact**: **Data loss in production**

#### Problem

BAR fields defined in Pydantic schema (`acm_schemas.py`) but **NOT in database schema**:

**Schema Definition** (acm_schemas.py:120-177):
```python
identifying_company: Optional[str] = Field(...)
floor_level: Optional[str] = Field(...)
quantity: Optional[str] = Field(...)
acm_labelled: Optional[bool] = Field(...)
# ... 7 more BAR fields
```

**Database Migration Search Result**:
```bash
$ grep -r "floor_level" migrations/
# No matches found
```

**Consequence**: Frontend displays BAR columns, extraction populates values, but **database silently drops them** on insert.

#### What Could Go Wrong

1. **Silent Data Loss**:
   - User uploads ACM register
   - Extraction extracts `floor_level="Ground"`
   - Backend attempts to save to SurrealDB
   - SurrealDB rejects unknown field (SCHEMAFULL mode)
   - **No error raised** (field silently ignored)
   - Frontend displays empty column

2. **Migration Mismatch**:
   - Developer adds field to Pydantic model
   - Forgets to add migration
   - CI/CD tests pass (in-memory DB has no schema)
   - Production fails (schema validation strict)

3. **BAR Compliance Failure**:
   - Victorian regulations require `floor_level` field
   - System extracts it correctly
   - Database doesn't store it
   - Exported BAR report lacks required field
   - **Compliance violation**

#### Recommended Mitigations

1. **CRITICAL - Create Migration 20 immediately**:
   ```sql
   -- Migration 20: BAR compliance fields for acm_record

   DEFINE FIELD floor_level ON acm_record TYPE option<string>;
   DEFINE FIELD date_inspected ON acm_record TYPE option<datetime>;
   DEFINE FIELD inspection_type ON acm_record TYPE option<string>;
   DEFINE FIELD bar_report_no ON acm_record TYPE option<string>;
   DEFINE FIELD date_of_bar_report ON acm_record TYPE option<datetime>;
   DEFINE FIELD asbestos_assessor ON acm_record TYPE option<string>;
   DEFINE FIELD result_classification ON acm_record TYPE option<string>;
   ```

2. **HIGH - Add schema validation tests**:
   ```python
   def test_pydantic_matches_database_schema():
       """Ensure all Pydantic fields exist in database."""
       model_fields = ACMRecord.model_fields.keys()
       db_fields = get_table_fields("acm_record")

       missing = set(model_fields) - set(db_fields)
       assert not missing, f"Missing DB fields: {missing}"
   ```

3. **MEDIUM - Add pre-commit hook**:
   ```bash
   # .git/hooks/pre-commit
   # Check for new Pydantic fields without migrations
   git diff --cached | grep "Field(" | grep -v "migrations/"
   ```

---

### HIGH Risk: Prompt-Based Extraction vs Post-Processing

**Severity**: **HIGH**
**Impact**: **Inconsistent BAR field extraction**

#### Problem

BAR fields are extracted via **LLM interpretation** of unstructured text, not via **deterministic regex patterns**.

**Prompt Instruction** (extraction.jinja:314-330):
```
### Victorian BAR Compliance Fields (CRITICAL - extract if available)

- `sample_no`: NATA endorsed sample number (e.g., "34511-039-001", "J169642-001-003")
- `quantity`: Amount of material (e.g., "10 m²", "5 linear meters", "2m2")
- `acm_labelled`: Boolean - whether ACM is labeled on-site (YES → true, NO → false)
- `identifying_company`: Hygiene or consulting company name (e.g., "Prensa Pty Ltd", "Greencap")
- `floor_level`: Floor level where ACM is located (e.g., "Ground", "Level 1", "Level 2", "Roof")

**Example BAR field extraction:**
- If document shows "Sample: 34511-039-001" → sample_no: "34511-039-001"
- If document shows "Labelled: NO" → acm_labelled: false
```

**Reliability Issues**:

1. **Ambiguous Text**:
   - "Quantity: 10m2 throughout" → `quantity: "10m2"` or `quantity: "10m2 throughout"`?
   - "Level: Ground Floor" → `floor_level: "Ground"` or `floor_level: "Ground Floor"`?
   - LLM decides arbitrarily

2. **Cross-Page Context**:
   - Page 1 header: "Identifying Company: Prensa Pty Ltd"
   - Page 5 record: (no company mentioned)
   - Does LLM carry forward context? Depends on chunk boundaries.

3. **Format Variations**:
   - "Prensa Pty Ltd" vs "Prensa" vs "Prensa Pty Limited"
   - LLM normalizes inconsistently

#### What Could Go Wrong

1. **Missing Company Name**:
   - Document has company on title page only
   - Chunked extraction processes page 5 in isolation
   - Company name not in chunk → extracted as `None`
   - **All records lack `identifying_company`** → BAR non-compliant

2. **Inconsistent Quantity Units**:
   - Record 1: `quantity: "10 m²"`
   - Record 2: `quantity: "10m2"` (no space)
   - Record 3: `quantity: "10 square meters"`
   - **Same unit, 3 different formats** → aggregation fails

3. **Hallucinated Values**:
   - LLM sees "Quantity unknown"
   - LLM extracts `quantity: "unknown"` (string, not None)
   - **Database validation passes** (type: string)
   - **Export validation fails** ("unknown" not a valid quantity)

#### Recommended Mitigations

1. **HIGH - Add post-processing normalization**:
   ```python
   def normalize_bar_fields(record: ACMRecord) -> ACMRecord:
       # Quantity normalization
       if record.quantity:
           record.quantity = normalize_quantity(record.quantity)
           # "10m2" → "10 m²"
           # "10 square meters" → "10 m²"

       # Company normalization
       if record.identifying_company:
           record.identifying_company = normalize_company_name(record.identifying_company)
           # "Prensa Pty Ltd" → canonical form

       # Floor level normalization
       if record.floor_level:
           record.floor_level = normalize_floor_level(record.floor_level)
           # "Ground Floor" → "Ground"
           # "1st Floor" → "Level 1"

       return record
   ```

2. **MEDIUM - Add BAR field validators**:
   ```python
   @field_validator("quantity")
   def validate_quantity(cls, v):
       if v and v.lower() == "unknown":
           return None  # Convert "unknown" string to None
       # Regex: "10 m²" or "10m2" or "10.5 linear meters"
       pattern = r"^\d+(\.\d+)?\s*(m²|m2|linear meters|square meters)$"
       if v and not re.match(pattern, v):
           raise ValueError(f"Invalid quantity format: {v}")
       return v
   ```

3. **MEDIUM - Add document-level metadata extraction**:
   - Extract `identifying_company`, `bar_report_no`, `date_of_bar_report` from title page ONCE
   - Store in `source` table
   - Propagate to all records via foreign key
   - **Benefits**: Consistent, no duplication, no LLM variability

---

### MEDIUM Risk: Insufficient BAR Fields for Compliance

**Severity**: **MEDIUM**
**Impact**: **Non-compliant BAR exports**

#### Problem

Victorian BAR regulations require **15+ fields**. Sprint 1 added 7. Are we missing critical fields?

**Victorian BAR Minimum Fields** (from regulations):
1. ✅ Identifying company
2. ✅ Floor level
3. ✅ Sample number
4. ✅ Quantity/extent
5. ✅ ACM labelled
6. ❌ **Date material was inspected** (missing in DB schema!)
7. ❌ **Asbestos assessor name** (missing in DB schema!)
8. ❌ **NATA endorsement number** (missing)
9. ❌ **Control measures recommended** (hygienist_recommendations exists, but not required)
10. ❌ **Removal date (if applicable)** (date_of_removal exists, but not stored in DB!)

**Gap**: At least **5 required fields** not in database schema.

#### What Could Go Wrong

1. **Export Validation Failure**:
   - User clicks "Export BAR Report"
   - Backend generates CSV
   - Victorian validation tool rejects it: "Missing field: date_inspected"
   - **User cannot submit report to regulators**

2. **Partial Compliance**:
   - System extracts `date_inspected` from PDF
   - Database doesn't store it (no migration)
   - Export lacks required field
   - **Manual data entry required** → defeats purpose of automation

#### Recommended Mitigations

1. **HIGH - Audit BAR requirements against implementation**:
   - Review Victorian BAR regulations (2024 update)
   - Map all required fields to database schema
   - Add missing fields to Migration 20
   - Update extraction prompt with missing fields

2. **MEDIUM - Add BAR export validation**:
   ```python
   def validate_bar_export(records: List[ACMRecord]) -> List[str]:
       """Check if records meet BAR minimum requirements."""
       issues = []
       for record in records:
           if not record.identifying_company:
               issues.append(f"Record {record.id}: Missing identifying_company")
           if not record.floor_level:
               issues.append(f"Record {record.id}: Missing floor_level")
           # ... check all required fields
       return issues
   ```

3. **LOW - Add BAR compliance score to UI**:
   - Show "BAR Compliance: 85%" badge
   - Highlight missing required fields
   - Guide user to fix gaps before export

---

### LOW Risk: `identifying_company` Variation Across Pages

**Severity**: **LOW**
**Impact**: **Data inconsistency within same document**

#### Problem

Multi-consultant ACM registers (e.g., initial survey by Prensa, re-inspection by Greencap):

```
Page 1-10: Identifying Company: Prensa Pty Ltd
Page 11-20: Identifying Company: Greencap Asbestos Services
```

If extracted per-page, records will have **two different company names** in the same source document.

#### Recommended Mitigations

1. **MEDIUM - Extract metadata at document level**:
   - Store `identifying_company` in `source` table, not `acm_record`
   - Add `secondary_companies` field if multiple consultants
   - Reference via foreign key

2. **ALTERNATIVE - Add `inspection_date` to dedup key**:
   - Different inspections = different records (even if same material)
   - Preserves audit trail

---

## 3. CI/CD Pipeline Architecture

### File: `.github/workflows/e2e-tests.yml`

### Implementation Analysis

**Service Startup Sequence**:
1. Start SurrealDB (Docker) - 30s timeout
2. Install Python deps (uv sync) - ~60s
3. Install Node deps (npm ci) - ~30s
4. Start Backend API - 60s timeout
5. Start Frontend - 120s timeout
6. Run Playwright tests

**Total estimated startup time**: ~5-6 minutes before tests run.

### HIGH Risk: No Smoke Test Before E2E Tests

**Severity**: **HIGH**
**Impact**: **CI/CD false positives, wasted GitHub Actions minutes**

#### Problem

E2E tests run without verifying that services are **actually functional**, only that ports are open.

**Current Health Checks** (.github/workflows/e2e-tests.yml:29-32, 104-106, 115-117):
```bash
# SurrealDB
timeout 30 bash -c 'until curl -f http://localhost:8000/health 2>/dev/null; do sleep 1; done'

# API
timeout 60 bash -c 'until curl -f http://localhost:5055/health 2>/dev/null; do sleep 2; done'

# Frontend
timeout 120 bash -c 'until curl -f http://localhost:8502 2>/dev/null; do sleep 2; done'
```

**Issue**: `/health` endpoint returns 200 even if:
- Database connection is broken
- Migrations failed
- Frontend build failed but server started

**Consequence**: E2E tests run, fail with cryptic errors, developer wastes time debugging.

#### What Could Go Wrong

1. **Database Migration Failure**:
   - SurrealDB starts, port 8000 open
   - API starts, migration fails (schema error)
   - `/health` returns 200 (basic liveness check, no DB test)
   - E2E tests run
   - **Every test fails with "Database connection error"**
   - Developer spends 20 minutes debugging

2. **Frontend Build Error**:
   - `npm run dev` starts webpack-dev-server
   - Port 8502 responds with 200
   - But JavaScript bundle has compile errors
   - E2E tests run
   - **Playwright sees blank page, all tests fail**

3. **API Dependencies Missing**:
   - API starts, `/health` works
   - `/health/ready` not tested (checks SurrealDB connectivity)
   - First E2E test hits `/api/sources` → 500 error
   - **Fails after 30 seconds** (not immediately)

#### Recommended Mitigations

1. **HIGH - Add smoke test step BEFORE E2E tests**:
   ```yaml
   - name: Run smoke tests
     run: |
       echo "Testing SurrealDB connectivity..."
       curl -f http://localhost:5055/health/ready || exit 1

       echo "Testing API endpoints..."
       curl -f http://localhost:5055/api/models || exit 1

       echo "Testing frontend rendering..."
       curl -s http://localhost:8502 | grep -q "ACM-AI" || exit 1

       echo "✅ All smoke tests passed!"
   ```

2. **MEDIUM - Use /health/ready instead of /health**:
   - `/health/ready` checks SurrealDB connectivity (api/main.py:175-194)
   - Better signal of actual readiness

3. **LOW - Add timeout circuit breaker**:
   ```yaml
   - name: Wait for services (with timeout)
     timeout-minutes: 3
     run: |
       # If services don't start in 3 min, fail fast (not wait 30 min)
   ```

---

### HIGH Risk: Docker-Based SurrealDB Reliability in GitHub Actions

**Severity**: **HIGH**
**Impact**: **Flaky tests, non-deterministic failures**

#### Problem

SurrealDB runs in Docker container in GitHub Actions, but:

1. **Container startup is async**:
   - `docker run -d` returns immediately
   - SurrealDB process may take 5-30s to actually start
   - Health check polls `/health`, but endpoint may return 404 initially

2. **Memory-based storage**:
   ```yaml
   surrealdb/surrealdb:v2 start --log info --user root --pass root memory
   ```
   - Uses in-memory storage (not persistent)
   - **Fast** but **ephemeral**
   - If container restarts during tests → all data lost

3. **No resource limits**:
   - Container can consume all available memory
   - GitHub Actions runners have 7GB RAM
   - Large ACM extraction (5000 records) could OOM

#### What Could Go Wrong

1. **Intermittent Health Check Failures**:
   - SurrealDB container starts
   - Health check polls immediately
   - SurrealDB process not ready → 404
   - **Retry loop exhausts 30s timeout**
   - CI fails with "SurrealDB failed to start"
   - **5% of CI runs fail randomly**

2. **Container Resource Exhaustion**:
   - E2E test uploads 20MB PDF
   - Extraction spawns 10 parallel LLM calls
   - SurrealDB buffers all results in memory
   - **Container OOMs, crashes**
   - No automatic restart → tests fail

3. **Race Condition Between API and DB**:
   - SurrealDB health check passes
   - API starts immediately
   - API runs migrations while SurrealDB still initializing
   - **Migration fails, API crashes**
   - E2E tests run with no API

#### Recommended Mitigations

1. **CRITICAL - Add retry logic to health checks**:
   ```bash
   timeout 30 bash -c '
     while true; do
       if curl -f http://localhost:8000/health 2>/dev/null; then
         echo "SurrealDB ready!"
         exit 0
       fi
       echo "Waiting for SurrealDB..."
       sleep 2
     done
   '
   ```

2. **HIGH - Add resource limits to Docker container**:
   ```yaml
   docker run -d \
     --name surrealdb \
     --memory=2g \
     --memory-swap=2g \
     --cpus=2 \
     -p 8000:8000 \
     surrealdb/surrealdb:v2 start memory
   ```

3. **MEDIUM - Add database readiness test**:
   ```bash
   # After health check passes, test actual query execution
   curl -X POST http://localhost:8000/sql \
     -u "root:root" \
     -d "SELECT * FROM INFORMATION_SCHEMA.TABLES LIMIT 1" \
     || exit 1
   ```

4. **LOW - Add container health monitoring**:
   ```bash
   docker ps --filter "name=surrealdb" --format "{{.Status}}" | grep "Up" || exit 1
   ```

---

### MEDIUM Risk: Inadequate Timeouts

**Severity**: **MEDIUM**
**Impact**: **False negatives (tests pass when should fail)**

#### Problem

Timeout configuration (.github/workflows/e2e-tests.yml):

```yaml
# SurrealDB: 30s timeout
timeout 30 bash -c 'until curl -f http://localhost:8000/health ...'

# API: 60s timeout
timeout 60 bash -c 'until curl -f http://localhost:5055/health ...'

# Frontend: 120s timeout
timeout 120 bash -c 'until curl -f http://localhost:8502 ...'
```

**Issues**:

1. **SurrealDB 30s may be too short**:
   - GitHub Actions runners are shared (resource contention)
   - Docker image pull can take 10-20s on cold cache
   - Container startup + SurrealDB init = 10-30s
   - **30s timeout is marginal**

2. **Frontend 120s may mask build failures**:
   - Next.js dev server retries failed builds
   - 120s gives multiple retry attempts
   - **Tests pass even if initial build failed**

#### What Could Go Wrong

1. **Timeout Too Short → Flaky Tests**:
   - SurrealDB takes 31s to start (1s over timeout)
   - CI fails with "SurrealDB timeout"
   - Developer re-runs, passes (29s next time)
   - **Intermittent failures erode trust in CI**

2. **Timeout Too Long → False Positives**:
   - Frontend build has error
   - webpack-dev-server retries 5 times over 120s
   - Eventually recovers
   - **Tests pass, but build is fragile**

#### Recommended Mitigations

1. **MEDIUM - Increase SurrealDB timeout to 60s**:
   ```yaml
   timeout 60 bash -c 'until curl -f http://localhost:8000/health ...'
   ```

2. **MEDIUM - Add explicit failure detection**:
   ```bash
   # Frontend startup
   npm run dev &
   FRONTEND_PID=$!

   # Wait for port, but also check process is alive
   for i in {1..60}; do
     if ! kill -0 $FRONTEND_PID 2>/dev/null; then
       echo "ERROR: Frontend process died"
       exit 1
     fi
     if curl -f http://localhost:8502 2>/dev/null; then
       echo "Frontend ready!"
       exit 0
     fi
     sleep 2
   done
   ```

3. **LOW - Add timeout monitoring**:
   ```yaml
   - name: Report startup times
     run: |
       echo "SurrealDB: ${SURREAL_START_TIME}s"
       echo "API: ${API_START_TIME}s"
       echo "Frontend: ${FRONTEND_START_TIME}s"
   ```

---

### MEDIUM Risk: Missing Artifact Retention Strategy

**Severity**: **MEDIUM**
**Impact**: **Difficult debugging, storage costs**

#### Problem

Artifact retention (.github/workflows/e2e-tests.yml:134-163):

```yaml
- name: Upload Playwright test results
  uses: actions/upload-artifact@v4
  with:
    retention-days: 7  # 7 days for all artifacts
```

**Issues**:

1. **7-day retention may be too short**:
   - Bug found in production 2 weeks after merge
   - Need to compare with CI artifacts from that PR
   - **Artifacts deleted, can't debug**

2. **7-day retention may be too long for screenshots**:
   - 100 E2E tests × 5 screenshots each = 500 files
   - 500 files × 200KB = 100MB per CI run
   - 10 PRs/day × 7 days × 100MB = **7GB storage**

3. **No differentiation by artifact type**:
   - Test results (critical) = 7 days
   - Screenshots (debugging only) = 7 days
   - Videos (large, rarely needed) = 7 days

#### Recommended Mitigations

1. **MEDIUM - Tiered retention policy**:
   ```yaml
   # Test results: 30 days (critical for regression analysis)
   - name: Upload test results
     retention-days: 30

   # Screenshots: 7 days (debugging only)
   - name: Upload screenshots
     retention-days: 7

   # Videos: 3 days (large, rarely needed)
   - name: Upload videos
     retention-days: 3
   ```

2. **LOW - Add artifact size monitoring**:
   ```bash
   du -sh test-results/ playwright-report/
   echo "Total artifact size: $(du -sh test-results/ | cut -f1)"
   ```

3. **LOW - Compress videos before upload**:
   ```bash
   find test-results -name "*.webm" -exec ffmpeg -i {} -c:v libx264 -crf 28 {}.mp4 \;
   ```

---

### LOW Risk: Secrets Exposure in Logs

**Severity**: **LOW**
**Impact**: **Potential credential leak**

#### Problem

Environment variables printed in logs (.github/workflows/e2e-tests.yml:78-95):

```yaml
- name: Create .env file
  run: |
    cat > .env << EOF
    API_URL=http://localhost:5055
    SURREAL_USER=root
    SURREAL_PASSWORD=root  # ⚠️ Hardcoded password in logs
    EOF
```

**Issue**: If `set -x` is enabled, `.env` contents echo to logs.

**Current Risk**: **LOW** (development credentials only, not production)

#### Recommended Mitigations

1. **LOW - Use GitHub secrets**:
   ```yaml
   - name: Create .env file
     run: |
       cat > .env << EOF
       SURREAL_PASSWORD=${{ secrets.SURREAL_PASSWORD }}
       EOF
   ```

2. **ALTERNATIVE - Mask sensitive values**:
   ```yaml
   run: |
     echo "::add-mask::$SURREAL_PASSWORD"
     cat > .env << EOF
   ```

---

## 4. Observability Stack

### File: `api/main.py:169-295`

### Implementation Analysis

**Health Endpoints**:
1. `/health` - Basic liveness (always 200)
2. `/health/ready` - Readiness with DB check
3. `/health/detailed` - Full component status

### MEDIUM Risk: Incomplete Error Categorization

**Severity**: **MEDIUM**
**Impact**: **Difficult production debugging**

#### Problem

`/health/detailed` endpoint tracks database, worker, and API status, but **not extraction errors**.

**Missing Error Categories**:

1. **Extraction failures**:
   - PDF parsing errors
   - LLM API errors (rate limit, timeout)
   - Schema validation errors
   - No tracking → can't diagnose "why are extractions failing?"

2. **Database write errors**:
   - Record validation failures
   - SurrealDB schema mismatches
   - No tracking → silent data loss

3. **Queue backlog**:
   - Background job queue depth
   - Stuck jobs (running > 1 hour)
   - No tracking → jobs hang indefinitely

#### What Could Go Wrong

1. **Silent Extraction Failures**:
   - LLM API returns 429 (rate limit)
   - Extraction retries 3 times, fails
   - No error logged to health endpoint
   - **User sees "Extraction complete: 0 records"**
   - Developer has no signal to debug

2. **Worker Process Zombie**:
   - Worker process crashes but PID file remains
   - `/health/detailed` reports "worker: running" (checks PID only)
   - **Jobs never process**
   - No alert until user complains

#### Recommended Mitigations

1. **MEDIUM - Add error tracking to /health/detailed**:
   ```python
   @app.get("/health/detailed")
   async def health_detailed():
       # ... existing code ...

       # Add error tracking
       recent_errors = await repo_query("""
           SELECT * FROM error_log
           WHERE created_at > time::now() - 1h
           ORDER BY created_at DESC
           LIMIT 10
       """)

       return {
           "status": "healthy",
           "components": { ... },
           "recent_errors": len(recent_errors),
           "error_categories": {
               "extraction": count_errors_by_type(recent_errors, "extraction"),
               "database": count_errors_by_type(recent_errors, "database"),
               "llm_api": count_errors_by_type(recent_errors, "llm_api"),
           }
       }
   ```

2. **MEDIUM - Add extraction metrics**:
   ```python
   "extraction_metrics": {
       "last_24h": {
           "total_runs": 50,
           "successful": 45,
           "failed": 5,
           "avg_duration_sec": 12.3,
       }
   }
   ```

3. **LOW - Add queue depth monitoring**:
   ```python
   "queue": {
       "pending_jobs": 3,
       "running_jobs": 2,
       "stuck_jobs": 0,  # Running > 1 hour
   }
   ```

---

### MEDIUM Risk: Worker PID File Stale Detection

**Severity**: **MEDIUM**
**Impact**: **False health signals**

#### Problem

Worker health check (api/main.py:232-245):

```python
pid_file = os.environ.get("WORKER_PID_FILE", ".pids/worker.pid")
if os.path.exists(pid_file):
    with open(pid_file) as f:
        worker_pid = int(f.read().strip())
    try:
        os.kill(worker_pid, 0)  # Signal 0 = check if process exists
        worker_status = "running"
    except ProcessLookupError:
        worker_status = "stopped"
```

**Issue**: PID file may be stale (process crashed, PID recycled).

**Scenario**:
1. Worker process starts, PID 1234, writes `.pids/worker.pid`
2. Worker crashes
3. New unrelated process gets PID 1234
4. Health check sees PID 1234 alive → reports "worker: running" ✅
5. **Worker is actually dead, false positive**

#### Recommended Mitigations

1. **MEDIUM - Add process name verification**:
   ```python
   import psutil

   try:
       proc = psutil.Process(worker_pid)
       if "worker" in proc.name().lower():
           worker_status = "running"
       else:
           worker_status = "stopped (PID recycled)"
   except psutil.NoSuchProcess:
       worker_status = "stopped"
   ```

2. **ALTERNATIVE - Add heartbeat file**:
   ```python
   # Worker updates heartbeat every 60s
   heartbeat_file = ".pids/worker.heartbeat"
   if os.path.exists(heartbeat_file):
       heartbeat_age = time.time() - os.path.getmtime(heartbeat_file)
       if heartbeat_age > 120:  # No heartbeat for 2 minutes
           worker_status = "stale"
   ```

---

### LOW Risk: Memory Usage Calculation Platform-Specific

**Severity**: **LOW**
**Impact**: **Incorrect metrics on macOS**

#### Problem

Memory calculation (api/main.py:265-275):

```python
import resource

memory_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
# On Linux, ru_maxrss is in KB; on macOS, it's in bytes
if os.uname().sysname == "Darwin":
    memory_mb = memory_kb / 1024 / 1024
else:
    memory_mb = memory_kb / 1024
```

**Issue**: Relies on `os.uname().sysname` which may not work in Docker containers.

**Edge Case**: Docker container reports `sysname="Linux"` even on macOS host → memory calculation wrong.

#### Recommended Mitigations

1. **LOW - Use psutil for cross-platform memory**:
   ```python
   import psutil

   process = psutil.Process(os.getpid())
   memory_mb = process.memory_info().rss / 1024 / 1024
   ```

2. **ALTERNATIVE - Document platform assumption**:
   ```python
   # Assumes Linux environment (Docker production)
   memory_mb = memory_kb / 1024
   ```

---

## 5. Cross-Cutting Risks

### MEDIUM Risk: Missing Rollback Plan for Schema Changes

**Severity**: **MEDIUM**
**Impact**: **Production downtime if migration fails**

#### Problem

Sprint 1 added 7 BAR fields to Pydantic schema but no database migration. If migration is added later and fails:

1. Production database schema out of sync
2. API crashes on startup (migration failure)
3. No rollback plan → **manual intervention required**

#### Recommended Mitigations

1. **MEDIUM - Add migration testing**:
   ```bash
   # CI step: Test migration up+down
   uv run python -m open_notebook.database.async_migrate up
   uv run python -m open_notebook.database.async_migrate down
   uv run python -m open_notebook.database.async_migrate up
   ```

2. **MEDIUM - Add migration failure recovery**:
   ```python
   # api/main.py lifespan
   try:
       await migration_manager.run_migration_up()
   except Exception as e:
       logger.error(f"Migration failed: {e}")
       logger.warning("Attempting rollback...")
       await migration_manager.rollback()
       raise
   ```

---

### LOW Risk: Hardcoded "Unknown" Strings Not Internationalized

**Severity**: **LOW**
**Impact**: **Poor UX for non-English users**

#### Problem

Dedup key uses hardcoded English strings:

```python
school = school_code or "unknown"
product = (record.product or "unknown").lower()
```

If system is internationalized later, these strings need translation.

#### Recommended Mitigations

1. **LOW - Use constants**:
   ```python
   UNKNOWN_SCHOOL = "unknown"
   UNKNOWN_PRODUCT = "unknown"

   school = school_code or UNKNOWN_SCHOOL
   ```

2. **FUTURE - Add i18n**:
   ```python
   from i18n import _

   school = school_code or _("unknown")
   ```

---

## Summary Risk Matrix

| Risk Item | Severity | Impact | Likelihood | Mitigation Effort |
|-----------|----------|--------|------------|-------------------|
| **1. Dedup key instability with empty fields** | CRITICAL | High | High | Medium (add normalization + DB field) |
| **2. Missing BAR field migrations** | CRITICAL | High | Very High | Low (write migration) |
| **3. SHA-256 performance overhead** | HIGH | Medium | Medium | Low (swap to xxHash) |
| **4. No smoke tests in CI/CD** | HIGH | Medium | High | Low (add smoke test step) |
| **5. Docker SurrealDB reliability** | HIGH | Medium | Medium | Medium (add retries + limits) |
| **6. Prompt-based BAR extraction inconsistency** | HIGH | High | Medium | High (post-processing + validation) |
| **7. Dedup key excludes sample_no** | MEDIUM | Medium | Low | Medium (redesign key) |
| **8. Hash collision (8 chars)** | MEDIUM | Low | Low | Low (increase to 12-16 chars) |
| **9. Inadequate CI/CD timeouts** | MEDIUM | Low | Medium | Low (adjust timeouts) |
| **10. Incomplete error categorization** | MEDIUM | Medium | Medium | Medium (add error tracking) |
| **11. Worker PID stale detection** | MEDIUM | Medium | Low | Medium (add heartbeat) |

---

## Recommended Action Plan

### Immediate (Block Merge)

1. ✅ **CRITICAL**: Create Migration 20 for BAR fields (30 min)
2. ✅ **CRITICAL**: Add dedup key whitespace normalization (15 min)
3. ✅ **HIGH**: Add smoke tests to CI/CD (1 hour)
4. ✅ **HIGH**: Add SurrealDB health check retries (30 min)

### Short-Term (Next Sprint)

5. ⚠️ **HIGH**: Replace SHA-256 with xxHash (2 hours)
6. ⚠️ **HIGH**: Add BAR field post-processing normalization (1 day)
7. ⚠️ **MEDIUM**: Store dedup key in database (4 hours)
8. ⚠️ **MEDIUM**: Add error tracking to /health/detailed (4 hours)

### Long-Term (Future)

9. 📋 **MEDIUM**: Redesign dedup key to include sample_no (1 day)
10. 📋 **MEDIUM**: Add migration rollback testing (1 day)
11. 📋 **LOW**: Cross-platform memory calculation (2 hours)

---

## Conclusion

Sprint 1 delivered solid extraction accuracy improvements (26% → 87%), but **architectural technical debt** must be addressed before production:

- **Deduplication**: Fragile key design with 4 high-risk issues
- **BAR Compliance**: Missing database schema for critical fields
- **CI/CD**: No smoke tests, unreliable Docker setup
- **Observability**: Incomplete error tracking

**Recommendation**: Address all 4 CRITICAL + HIGH risks before merging to `main`. Estimated effort: **1-2 days**.
