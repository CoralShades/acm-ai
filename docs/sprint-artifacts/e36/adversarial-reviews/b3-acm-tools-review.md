# Adversarial Review: B3 — FK-Based Record Counts in list_acm_buildings

## Fix Summary
`list_acm_buildings` in `open_notebook/graphs/chat_tools/acm_tools.py` was updated to
query `acm_record.building_record_id` (the FK) to compute per-building record counts and
risk stats, instead of grouping by `building_name` (which produced mismatches when names
differed between tables). A name-based fallback is retained when no FK-matched stats
exist.

## Files Reviewed
- `open_notebook/graphs/chat_tools/acm_tools.py` (lines 364–480)

## Findings

### [CONCERN] FK-Based Fallback Condition Is Inverted — Fallback Never Fires for Partial FK Coverage
**What**: The name-based fallback (`stats_by_name`) is only populated when
`not stats_by_id` (line 415). If even one `acm_record` has a `building_record_id`, the
`stats_by_id` dict is non-empty, and the fallback name query is skipped entirely. Records
without a `building_record_id` (i.e., `building_record_id = NONE`) are silently excluded
from the FK stats query (line 403: `AND building_record_id != NONE`), and the name
fallback is not invoked to cover them.
**Why it matters**: In a partially-migrated dataset where some records have FKs and some
do not, buildings with only unlinked records will show `record_count: 0` in the chat tool
output, understating the true count and potentially misleading the user about risk.
**Evidence**: `acm_tools.py` lines 394–431. The fk_stats query excludes NULL FKs; the
name fallback is guarded by `if buildings and not stats_by_id`.
**Recommendation**: Remove the `not stats_by_id` guard from the name-based fallback.
Always run both queries and merge, with FK-based stats taking precedence per building
where available, and name-based stats filling in gaps.

### [CONCERN] `_build_source_filter` Applied to `building_record` Without Field Verification
**What**: The `building_query` on line 380 applies `filter_clause` (which expands to
`source_id = $source_id`) directly to `building_record`. The comment on line 385 has a
no-op replace: `.replace("source_id", "source_id")`. This is dead code that adds noise
but does not verify that `building_record` actually has a `source_id` column.
**Why it matters**: If `building_record` does not have a `source_id` field with that name,
SurrealDB will silently return zero rows (schema-less behaviour), and the tool reports no
buildings exist when they do.
**Evidence**: `acm_tools.py` line 385. The `.replace()` call is a self-assignment and
should be removed. The field name assumption is untested in this path.
**Recommendation**: Verify `building_record` schema has `source_id`. Remove the dead
`.replace()` call to avoid misleading future readers.

### [CONCERN] `notebook_id` Filter Not Supported on `building_record`
**What**: `_build_source_filter` returns `source_id IN (SELECT out FROM reference WHERE
in = $notebook_id)` when `notebook_id` is set instead of `source_id`. This subquery is
designed for `acm_record`. If `building_record` uses a different relation schema, the
notebook-scoped filter would silently return zero buildings.
**Why it matters**: Users accessing the tool via notebook context (AI-Editor, not a job
page) would always see an empty building list.
**Evidence**: `acm_tools.py` lines 50–56 (`_build_source_filter`), lines 380–390
(building query applying the same filter).
**Recommendation**: Verify that the notebook-based subquery works for `building_record`.
If not, add a notebook-specific building query path.

### [NITPICK] No Total Record Count Returned for Buildings Without FK Match
**What**: When `stats_by_id.get(bid)` misses (bid not in FK stats) and
`stats_by_name.get(name)` also misses, the building entry gets `record_count: 0` with no
indicator that data might exist but was unmatched. The LLM will report "0 records" for
that building.
**Why it matters**: Silent zero vs. true zero are indistinguishable in the tool output.
**Recommendation**: Add an optional `"stats_matched": false` field to the output dict so
callers can detect unmatched buildings.

## Verdict: PASS WITH CONCERNS

The FK-first approach is the correct direction and fixes the primary name-mismatch bug.
The partial-coverage gap (CONCERN 1) is the most likely real-world issue since mixed FK
populations are expected during incremental extraction. The dead `.replace()` call should
be cleaned up.
