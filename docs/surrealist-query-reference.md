# Surrealist Query Reference — ACM Record Verification

Use these queries in **Surrealist** (SurrealDB v2 GUI) to verify extracted records are saved correctly.

## Connection Settings

```
Endpoint:  ws://localhost:8000
Namespace: open_notebook
Database:  development
Username:  root
Password:  root
```

---

## IMPORTANT: Use the Query Tab, NOT Record Explorer

> **The "Record Explorer" bar at the top of Surrealist auto-appends
> `ORDER BY id ASC LIMIT 20` to every query you type.** This breaks
> any query that uses `GROUP ALL`, `GROUP BY`, subqueries, or custom
> `ORDER BY` / `LIMIT` clauses — producing a **Parse error**.
>
> **Always paste these queries into the "Query" tab** (click the `</>` Query
> icon in the left sidebar). That gives you a full SQL editor with no
> auto-appended clauses.

### Record ID Format in SurrealDB v2

Record IDs look like `source:6of6s8u4oa3dhatmv4dp`. To use them in queries:

```sql
-- Plain alphanumeric IDs — no escaping needed
WHERE source_id = source:6of6s8u4oa3dhatmv4dp

-- IDs with special characters (hyphens, dots, etc.) — use angle brackets
WHERE source_id = source:⟨my-special-id⟩

-- Or use backtick syntax
WHERE source_id = source:`my-special-id`
```

### How to Find Your Source ID

```sql
-- List all sources — grab the id from the result
SELECT id, name, created FROM source ORDER BY created DESC LIMIT 10;
```

Copy the `id` value (e.g., `source:6of6s8u4oa3dhatmv4dp`) and replace
`source:YOUR_ID` in the queries below.

---

## 1. Overview Counts

### Total records across all jobs
```sql
SELECT count() AS total FROM acm_record GROUP ALL;
```

### Total buildings across all jobs
```sql
SELECT count() AS total FROM building_record GROUP ALL;
```

### Records per job (source)
```sql
SELECT source_id, count() AS record_count
FROM acm_record
GROUP BY source_id;
```

### Buildings per job
```sql
SELECT source_id, count() AS building_count
FROM building_record
GROUP BY source_id;
```

---

## 2. Query by Source ID

Replace `source:YOUR_ID` with your actual source record ID.

### All ACM records for a job
```sql
SELECT * FROM acm_record WHERE source_id = source:YOUR_ID;
```

### Record count for a job
```sql
SELECT count() AS total
FROM acm_record
WHERE source_id = source:YOUR_ID
GROUP ALL;
```

### All buildings for a job
```sql
SELECT * FROM building_record WHERE source_id = source:YOUR_ID;
```

### Summary: buildings with their record counts
```sql
SELECT
  building_id,
  building_name,
  count() AS item_count
FROM acm_record
WHERE source_id = source:YOUR_ID
GROUP BY building_id, building_name;
```

---

## 3. Query by Building

### All records for a specific building (by building_id string)
```sql
SELECT * FROM acm_record
WHERE source_id = source:YOUR_ID
  AND building_id = 'BLD001';
```

### All records for a building (by building_record FK)
```sql
SELECT * FROM acm_record
WHERE building_record_id = building_record:YOUR_BUILDING_ID;
```

### Building detail
```sql
SELECT * FROM building_record:YOUR_BUILDING_ID;
```

### Buildings with specific fields only
```sql
SELECT
  internal_id,
  building_code,
  building_name,
  building_year,
  building_construction,
  building_type,
  building_address,
  suburb,
  postcode
FROM building_record
WHERE source_id = source:YOUR_ID;
```

---

## 4. Query by Room

### All records in a specific room
```sql
SELECT * FROM acm_record
WHERE source_id = source:YOUR_ID
  AND room_name = 'Corridor';
```

### Rooms per building
```sql
SELECT
  building_name,
  room_name,
  count() AS items
FROM acm_record
WHERE source_id = source:YOUR_ID
GROUP BY building_name, room_name
ORDER BY building_name, room_name;
```

---

## 5. Filter by Risk & Condition

### High risk records
```sql
SELECT building_name, room_name, product, material_description, risk_status
FROM acm_record
WHERE source_id = source:YOUR_ID
  AND risk_status = 'High';
```

### Friable records
```sql
SELECT building_name, room_name, product, friable, risk_status
FROM acm_record
WHERE source_id = source:YOUR_ID
  AND friable = 'Friable';
```

### No-access records
```sql
SELECT building_name, room_name, product
FROM acm_record
WHERE source_id = source:YOUR_ID
  AND no_access = true;
```

### Records by sample result
```sql
SELECT building_name, room_name, product, result, sample_no
FROM acm_record
WHERE source_id = source:YOUR_ID
  AND result = 'Positive';
```

Valid `result` values: `Positive`, `Negative`, `Not Sampled`, `No Access`, `Presumed`

---

## 6. Data Quality Checks

### Records with low extraction confidence
```sql
SELECT building_name, room_name, product, extraction_confidence, data_issues
FROM acm_record
WHERE source_id = source:YOUR_ID
  AND extraction_confidence = 'low';
```

### Records with data issues
```sql
SELECT building_name, product, data_issues
FROM acm_record
WHERE source_id = source:YOUR_ID
  AND data_issues IS NOT NONE
  AND array::len(data_issues) > 0;
```

### Records missing required fields
```sql
SELECT id, building_id, product, material_description, result
FROM acm_record
WHERE source_id = source:YOUR_ID
  AND (product IS NONE OR material_description IS NONE OR result IS NONE);
```

### Records missing building linkage
```sql
SELECT id, building_id, building_name
FROM acm_record
WHERE source_id = source:YOUR_ID
  AND building_record_id IS NONE;
```

### Duplicate check (same building + room + product)
```sql
SELECT
  building_id,
  room_name,
  product,
  count() AS dupes
FROM acm_record
WHERE source_id = source:YOUR_ID
GROUP BY building_id, room_name, product
HAVING count() > 1;
```

---

## 7. ACM Classification & Enrichment

### Records by product group
```sql
SELECT
  acm_product_group,
  acm_product_type,
  count() AS total
FROM acm_record
WHERE source_id = source:YOUR_ID
GROUP BY acm_product_group, acm_product_type;
```

### Records that have embeddings
```sql
SELECT count() AS embedded
FROM acm_record
WHERE source_id = source:YOUR_ID
  AND embedding IS NOT NONE
GROUP ALL;
```

### Records with enriched text
```sql
SELECT id, building_name, product, string::len(enriched_text) AS enriched_len
FROM acm_record
WHERE source_id = source:YOUR_ID
  AND enriched_text IS NOT NONE
LIMIT 10;
```

---

## 8. Table Sections (Provenance)

### All table sections for a job
```sql
SELECT * FROM acm_table_section WHERE source_id = source:YOUR_ID;
```

### Records linked to a table section
```sql
SELECT * FROM acm_record
WHERE parent_table_id = acm_table_section:YOUR_SECTION_ID;
```

### Table section coverage (which records have provenance)
```sql
SELECT
  parent_table_id,
  count() AS records
FROM acm_record
WHERE source_id = source:YOUR_ID
GROUP BY parent_table_id;
```

---

## 9. Source & Notebook Context

### Find a source by ID
```sql
SELECT * FROM source:YOUR_ID;
```

### List all sources (jobs)
```sql
SELECT id, name, notebook_id, created, updated
FROM source
ORDER BY created DESC
LIMIT 20;
```

### Find source by name pattern
```sql
SELECT id, name FROM source WHERE name ~ 'Alexander';
```

### Get notebook for a source
```sql
SELECT id, name FROM notebook
WHERE id = (SELECT notebook_id FROM source:YOUR_ID);
```

---

## 10. CRUD Audit Trail

### All CRUD operations for a job
```sql
SELECT * FROM crud_audit
WHERE job_id = source:YOUR_ID
ORDER BY timestamp DESC;
```

### Recent CRUD operations (all jobs)
```sql
SELECT job_id, operation, natural_language, generated_surql, confirmed_by, timestamp
FROM crud_audit
ORDER BY timestamp DESC
LIMIT 20;
```

---

## 11. Full-Text Search

### Search records by product/material description
```sql
SELECT id, building_name, product, material_description
FROM acm_record
WHERE source_id = source:YOUR_ID
  AND (product @@ 'ceiling' OR material_description @@ 'ceiling');
```

### BM25-scored search across all product fields
```sql
SELECT *, search::score(0) AS relevance
FROM acm_record
WHERE product @0@ 'vinyl tiles'
ORDER BY relevance DESC
LIMIT 10;
```

---

## 12. Cross-Job Comparisons

### Record counts across all jobs
```sql
SELECT
  source_id,
  count() AS records
FROM acm_record
GROUP BY source_id
ORDER BY records DESC;
```

### Buildings across all jobs
```sql
SELECT
  source_id,
  count() AS buildings
FROM building_record
GROUP BY source_id;
```

---

## 13. Database Introspection

### List all tables
```sql
INFO FOR DB;
```

### Show table schema (fields, indexes, events)
```sql
INFO FOR TABLE acm_record;
```

```sql
INFO FOR TABLE building_record;
```

```sql
INFO FOR TABLE source;
```

---

## 14. Delete / Cleanup (USE WITH CAUTION)

### Delete all records for a specific job
```sql
-- Step 1: Check what you're about to delete
SELECT count() AS to_delete
FROM acm_record
WHERE source_id = source:YOUR_ID
GROUP ALL;
```

```sql
-- Step 2: Delete (IRREVERSIBLE)
DELETE FROM acm_record WHERE source_id = source:YOUR_ID;
DELETE FROM building_record WHERE source_id = source:YOUR_ID;
DELETE FROM acm_table_section WHERE source_id = source:YOUR_ID;
```

### Delete a single record
```sql
DELETE acm_record:SPECIFIC_RECORD_ID;
```

---

## Quick Cheat Sheet

| What | Query |
|------|-------|
| List all sources | `SELECT id, name FROM source ORDER BY created DESC LIMIT 10;` |
| How many records? | `SELECT count() AS t FROM acm_record WHERE source_id = source:X GROUP ALL;` |
| How many buildings? | `SELECT count() AS t FROM building_record WHERE source_id = source:X GROUP ALL;` |
| List buildings | `SELECT DISTINCT building_id, building_name FROM acm_record WHERE source_id = source:X;` |
| High risk items | `SELECT * FROM acm_record WHERE source_id = source:X AND risk_status = 'High';` |
| Friable items | `SELECT * FROM acm_record WHERE source_id = source:X AND friable = 'Friable';` |
| No access items | `SELECT * FROM acm_record WHERE source_id = source:X AND no_access = true;` |
| Data issues | `SELECT * FROM acm_record WHERE source_id = source:X AND array::len(data_issues) > 0;` |
| All tables | `INFO FOR DB;` |
| All indexes | `INFO FOR TABLE acm_record;` |

---

## Tips

- **Use the Query tab** (`</>` icon in left sidebar) — NOT the Record Explorer bar
- **Record ID format**: SurrealDB IDs look like `source:6of6s8u4oa3dhatmv4dp` — no quotes needed
- **Special char IDs**: Wrap in angle brackets: `source:⟨my-id-with-dashes⟩` or backticks: `source:\`my-id\``
- **`INFO FOR DB;`** shows all tables in the database
- **`INFO FOR TABLE acm_record;`** shows all fields, indexes, and events
- **Regex match**: Use `~` operator: `WHERE building_name ~ 'Admin'`
- **Case-insensitive**: SurrealDB string comparisons are case-sensitive — use `string::lowercase()` if needed
- **NULL vs NONE**: In SurrealQL, use `IS NONE` or `IS NOT NONE` (not `IS NULL`)
- **Run multiple queries**: Separate with `;` — Surrealist will run them sequentially and show each result
