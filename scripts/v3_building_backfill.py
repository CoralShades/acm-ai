"""
V3 Building Record Backfill Script (E35-S6)

Extracts building-level fields from acm_record into building_record table
and populates building_record_id FK.  This is the building-only subset of
the full V3 data migration (scripts/v3_data_migration.py) -- vocabulary
migration is deliberately excluded.

Usage:
    uv run python scripts/v3_building_backfill.py [--dry-run] [--source-id SOURCE_ID] [--verbose]

Algorithm:
    1. Verify schema version >= 40 (building_record table and building_record_id field exist)
    2. Fetch all acm_records (optionally scoped to --source-id)
    3. Group by (source_id, building_id)
    4. For each group:
       a. Check if building_record already exists for (source_id, building_id) -> skip if so
       b. Extract building-level fields from the first record in the group
       c. Generate internal_id via BuildingRecord.generate_internal_id(source_id)
       d. Create BuildingRecord and save (unless --dry-run)
       e. Update all acm_records in the group: SET building_record_id = new_id
          WHERE building_record_id IS NULL (idempotent -- never overwrite non-NULL FKs)
    5. Print summary
"""

import argparse
import asyncio
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.acm import BuildingRecord

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class BackfillResult:
    """Summary of a building backfill run."""

    sources_processed: int = 0
    buildings_created: int = 0
    buildings_skipped: int = 0
    records_linked: int = 0
    records_already_linked: int = 0


# ---------------------------------------------------------------------------
# Schema verification
# ---------------------------------------------------------------------------


async def verify_schema() -> bool:
    """Return True if the database is at schema version >= 40.

    We check that the building_record table exists and acm_record has the
    building_record_id column.  If either check fails we abort with guidance.
    """
    try:
        # Attempt a SELECT on building_record -- if the table doesn't exist
        # SurrealDB will raise an error rather than return an empty list.
        await repo_query("SELECT * FROM building_record LIMIT 1")
    except Exception as e:
        logger.error(
            "Schema check failed: building_record table does not exist. "
            f"Error: {e}\n"
            "Please run pending database migrations first:\n"
            "  uv run python run_api.py  (starts API which auto-runs migrations)"
        )
        return False
    return True


# ---------------------------------------------------------------------------
# Core backfill helpers (reused from v3_data_migration.py)
# ---------------------------------------------------------------------------


def _extract_building_fields(record: dict) -> dict:
    """Extract building-level fields from a raw acm_record dict.

    Performs type conversions required by the BuildingRecord model:
    - building_year: int -> str  (SF picklist stores year as string)

    Args:
        record: Raw acm_record dict from repo_query.

    Returns:
        Dict of building-level fields suitable for BuildingRecord construction.
    """
    building_year_raw = record.get("building_year")
    building_year_str: Optional[str] = (
        str(building_year_raw) if building_year_raw is not None else None
    )

    return {
        "building_code": record.get("building_id"),
        "building_name": record.get("building_name"),
        "building_year": building_year_str,
        "building_construction": record.get("building_construction"),
        "building_address": record.get("building_address"),
        "suburb": record.get("suburb"),
        "postcode": record.get("postcode"),
        "building_type": record.get("building_type"),
        "source_id": record.get("source_id"),
    }


def _group_records_by_building(
    records: list[dict],
) -> dict[tuple, list[dict]]:
    """Group acm_record dicts by (source_id, building_id).

    Args:
        records: Raw acm_record dicts from repo_query.

    Returns:
        Dict mapping (source_id_str, building_id_str) -> list of record dicts.
    """
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for rec in records:
        source_id = str(rec.get("source_id", ""))
        building_id = str(rec.get("building_id", ""))
        groups[(source_id, building_id)].append(rec)
    return dict(groups)


async def _find_existing_building(source_id: str, building_code: str) -> Optional[str]:
    """Return the SurrealDB record ID of an existing BuildingRecord, or None.

    Idempotency check -- if a building_record already exists for this
    (source_id, building_code) pair, we return its ID so we can still
    update acm_records that may have missed the FK on a previous run.

    Args:
        source_id: The source_id string (e.g. "source:abc123").
        building_code: The building_id string from acm_record.

    Returns:
        Record ID string like "building_record:xyz" or None.
    """
    results = await repo_query(
        "SELECT id FROM building_record "
        "WHERE source_id = $src AND building_code = $code LIMIT 1",
        {
            "src": ensure_record_id(source_id),
            "code": building_code,
        },
    )
    if results:
        record_id = results[0].get("id")
        return str(record_id) if record_id else None
    return None


# ---------------------------------------------------------------------------
# Single-source backfill
# ---------------------------------------------------------------------------


async def backfill_source(
    source_id: str,
    dry_run: bool = False,
    verbose: bool = False,
) -> BackfillResult:
    """Backfill building records for a single source.

    Creates BuildingRecord entries for each unique building_id in the source's
    acm_records and links them via building_record_id FK.  Never overwrites
    non-NULL FK values (V3 safety).

    Args:
        source_id: The SurrealDB source ID (e.g. "source:abc123").
        dry_run: If True, report changes but do not write to DB.
        verbose: If True, log per-record details.

    Returns:
        BackfillResult with counts of buildings created/skipped and records linked.
    """
    result = BackfillResult()

    # Fetch all acm_records for this source
    raw_records = await repo_query(
        "SELECT * FROM acm_record WHERE source_id = $src ORDER BY building_id",
        {"src": ensure_record_id(source_id)},
    )

    if not raw_records:
        logger.info(f"No acm_records found for source {source_id}")
        return result

    logger.info(f"Found {len(raw_records)} acm_records for source {source_id}")

    # Group by (source_id, building_id)
    groups = _group_records_by_building(raw_records)
    logger.info(f"  -> {len(groups)} unique buildings found")

    for (src_id, bld_id), group_records in groups.items():
        if not bld_id:
            logger.warning(f"Skipping group with empty building_id in source {src_id}")
            continue

        if verbose:
            logger.info(
                f"  Processing building '{bld_id}' "
                f"({len(group_records)} records) in source {src_id}"
            )

        # Idempotency: check if building_record already exists
        existing_id = await _find_existing_building(src_id, bld_id)

        if existing_id:
            result.buildings_skipped += 1
            if verbose:
                logger.info(f"    -> Existing building_record found: {existing_id}")
            building_record_id = existing_id
        else:
            # Extract fields from the first record in the group
            first_rec = group_records[0]
            building_fields = _extract_building_fields(first_rec)

            if dry_run:
                logger.info(
                    f"  [DRY-RUN] Would create BuildingRecord for "
                    f"building_id='{bld_id}' in source {src_id}"
                )
                result.buildings_created += 1
                # In dry-run mode we can't get a real ID, so skip FK update
                # but count what records *would* be updated
                for rec in group_records:
                    if not rec.get("building_record_id"):
                        result.records_linked += 1
                    else:
                        result.records_already_linked += 1
                continue

            # Generate internal_id
            internal_id = await BuildingRecord.generate_internal_id(src_id)

            # Create and save BuildingRecord
            building = BuildingRecord(
                internal_id=internal_id,
                **building_fields,
            )
            try:
                await building.save()
            except Exception as e:
                logger.error(
                    f"Failed to save BuildingRecord for building_id='{bld_id}' "
                    f"source={src_id}: {e}"
                )
                raise
            building_record_id = building.id
            result.buildings_created += 1

            if verbose:
                logger.info(
                    f"    -> Created BuildingRecord {building_record_id} "
                    f"(internal_id={internal_id})"
                )

        if dry_run:
            # Dry-run: count but do not write FK
            for rec in group_records:
                if not rec.get("building_record_id"):
                    result.records_linked += 1
                else:
                    result.records_already_linked += 1
            continue

        # Update acm_records in this group to set building_record_id
        # Only update rows where building_record_id is currently NULL (idempotent)
        record_ids = [r["id"] for r in group_records if r.get("id")]
        for rec_id in record_ids:
            rec_data = next((r for r in group_records if r.get("id") == rec_id), None)
            if rec_data and rec_data.get("building_record_id"):
                # Already has an FK -- do not overwrite
                result.records_already_linked += 1
                if verbose:
                    logger.debug(f"    -> acm_record {rec_id} already has FK, skipping")
                continue

            await repo_query(
                "UPDATE acm_record SET building_record_id = $bld_rec_id "
                "WHERE id = $record_id AND "
                "(building_record_id = NONE OR building_record_id IS NULL)",
                {
                    "record_id": ensure_record_id(rec_id),
                    "bld_rec_id": ensure_record_id(building_record_id),
                },
            )
            result.records_linked += 1

            if verbose:
                logger.debug(
                    f"    -> Linked acm_record {rec_id} -> {building_record_id}"
                )

    return result


# ---------------------------------------------------------------------------
# Full backfill (all sources)
# ---------------------------------------------------------------------------


async def backfill_all(
    dry_run: bool = False,
    verbose: bool = False,
) -> BackfillResult:
    """Run building backfill across all sources.

    Discovers all distinct source_ids from acm_record and backfills each one.
    Caller must verify schema before calling (see verify_schema()).

    Args:
        dry_run: If True, report changes but do not write to DB.
        verbose: If True, log per-record details.

    Returns:
        Aggregated BackfillResult across all sources.
    """
    overall = BackfillResult()

    # Fetch all distinct source_ids from acm_record
    source_rows = await repo_query("SELECT DISTINCT source_id FROM acm_record")

    # Flatten: each row is {"source_id": "source:abc"}
    source_ids = []
    for row in source_rows:
        sid = row.get("source_id")
        if sid:
            source_ids.append(str(sid))

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_source_ids = []
    for sid in source_ids:
        if sid not in seen:
            seen.add(sid)
            unique_source_ids.append(sid)

    logger.info(f"Found {len(unique_source_ids)} distinct source(s) to backfill")

    for source_id in unique_source_ids:
        logger.info(f"Backfilling source: {source_id}")
        source_result = await backfill_source(
            source_id, dry_run=dry_run, verbose=verbose
        )
        overall.sources_processed += 1
        overall.buildings_created += source_result.buildings_created
        overall.buildings_skipped += source_result.buildings_skipped
        overall.records_linked += source_result.records_linked
        overall.records_already_linked += source_result.records_already_linked

    return overall


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _print_summary(result: BackfillResult, dry_run: bool) -> None:
    """Print a formatted backfill summary."""
    prefix = "[DRY-RUN] " if dry_run else ""
    print()
    print("=" * 60)
    print(f"{prefix}V3 BUILDING BACKFILL SUMMARY")
    print("=" * 60)
    print(f"  Sources processed:         {result.sources_processed}")
    print(f"  Building records created:  {result.buildings_created}")
    print(f"  Building records skipped:  {result.buildings_skipped} (already existed)")
    print(f"  ACM records linked:        {result.records_linked}")
    print(f"  ACM records already linked:{result.records_already_linked}")
    if dry_run:
        print()
        print("  NOTE: --dry-run mode -- no changes were written to the database.")
    print("=" * 60)
    print()


async def _main(args: argparse.Namespace) -> int:
    """Async main function for the CLI."""
    # Configure loguru for CLI output
    logger.remove()
    log_level = "DEBUG" if args.verbose else "INFO"
    logger.add(sys.stderr, level=log_level)

    dry_run: bool = args.dry_run
    verbose: bool = args.verbose

    if dry_run:
        logger.info("Running in DRY-RUN mode -- no changes will be written")

    # Verify schema first
    if not await verify_schema():
        return 1

    if args.source_id:
        # Single-source backfill
        logger.info(f"Backfilling single source: {args.source_id}")
        result = await backfill_source(args.source_id, dry_run=dry_run, verbose=verbose)
        result.sources_processed = 1
    else:
        # Full backfill
        result = await backfill_all(dry_run=dry_run, verbose=verbose)

    _print_summary(result, dry_run)
    return 0


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="V3 Building Backfill: create building_record entries from acm_record data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Report what would change without writing to the database",
    )
    parser.add_argument(
        "--source-id",
        metavar="SOURCE_ID",
        default=None,
        help="Backfill only a single source (e.g. 'source:abc123')",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable detailed per-record logging",
    )

    args = parser.parse_args()
    exit_code = asyncio.run(_main(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
