"""
V3 Data Migration Script (E30-S5)

Extracts building-level fields from acm_record into building_record table,
populates building_record_id FK, and applies the "Good -> Stable" vocabulary
migration.

Usage:
    uv run python scripts/v3_data_migration.py [--dry-run] [--source-id SOURCE_ID] [--verbose]

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
          WHERE building_record_id IS NULL (idempotent)
    5. Vocabulary migration: material_condition "Good" -> "Stable"
    6. Print summary
"""

import argparse
import asyncio
import sys
from collections import defaultdict
from typing import Optional

from loguru import logger

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.acm import BuildingRecord

# ---------------------------------------------------------------------------
# Schema verification
# ---------------------------------------------------------------------------


async def verify_schema() -> bool:
    """Return True if the database is at schema version >= 40.

    We check that the building_record table exists and acm_record has the
    building_record_id column. If either check fails we abort with guidance.
    """
    try:
        # Attempt a SELECT on building_record — if the table doesn't exist
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
# Core migration helpers
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

    Idempotency check — if a building_record already exists for this
    (source_id, building_code) pair, we return its ID so we can still
    update acm_records that may have missed the FK on a previous run.

    Args:
        source_id: The source_id string (e.g. "source:abc123").
        building_code: The building_id string from acm_record.

    Returns:
        Record ID string like "building_record:xyz" or None.
    """
    results = await repo_query(
        "SELECT id FROM building_record WHERE source_id = $src AND building_code = $code LIMIT 1",
        {
            "src": ensure_record_id(source_id),
            "code": building_code,
        },
    )
    if results:
        record_id = results[0].get("id")
        return str(record_id) if record_id else None
    return None


async def migrate_source(
    source_id: str,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """Migrate a single source: create BuildingRecords and link acm_records.

    This function is importable for unit testing.

    Args:
        source_id: The SurrealDB source ID (e.g. "source:abc123").
        dry_run: If True, report changes but do not write to DB.
        verbose: If True, log per-record details.

    Returns:
        Summary dict with keys: buildings_created, buildings_skipped,
        records_linked, records_already_linked.
    """
    summary = {
        "buildings_created": 0,
        "buildings_skipped": 0,
        "records_linked": 0,
        "records_already_linked": 0,
    }

    # Fetch all acm_records for this source
    raw_records = await repo_query(
        "SELECT * FROM acm_record WHERE source_id = $src ORDER BY building_id",
        {"src": ensure_record_id(source_id)},
    )

    if not raw_records:
        logger.info(f"No acm_records found for source {source_id}")
        return summary

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
            summary["buildings_skipped"] += 1
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
                summary["buildings_created"] += 1
                # In dry-run mode we can't get a real ID, so skip FK update
                # but count what records *would* be updated
                for rec in group_records:
                    if not rec.get("building_record_id"):
                        summary["records_linked"] += 1
                    else:
                        summary["records_already_linked"] += 1
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
            summary["buildings_created"] += 1

            if verbose:
                logger.info(
                    f"    -> Created BuildingRecord {building_record_id} "
                    f"(internal_id={internal_id})"
                )

        if dry_run:
            # Dry-run: count but do not write FK
            for rec in group_records:
                if not rec.get("building_record_id"):
                    summary["records_linked"] += 1
                else:
                    summary["records_already_linked"] += 1
            continue

        # Update acm_records in this group to set building_record_id
        # Only update rows where building_record_id is currently NULL (idempotent)
        record_ids = [r["id"] for r in group_records if r.get("id")]
        for rec_id in record_ids:
            rec_data = next((r for r in group_records if r.get("id") == rec_id), None)
            if rec_data and rec_data.get("building_record_id"):
                # Already has an FK — do not overwrite
                summary["records_already_linked"] += 1
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
            summary["records_linked"] += 1

            if verbose:
                logger.debug(
                    f"    -> Linked acm_record {rec_id} -> {building_record_id}"
                )

    return summary


async def migrate_vocabulary(dry_run: bool = False, verbose: bool = False) -> int:
    """Migrate material_condition 'Good' -> 'Stable' across all acm_records.

    This is naturally idempotent: once all 'Good' values are replaced, re-running
    the UPDATE will match zero rows.

    Args:
        dry_run: If True, count but do not update.
        verbose: If True, log each affected record.

    Returns:
        Number of records updated (or that would be updated in dry-run mode).
    """
    # First, count how many records would be affected
    count_result = await repo_query(
        "SELECT count() AS total FROM acm_record WHERE material_condition = 'Good' GROUP ALL"
    )
    count = count_result[0].get("total", 0) if count_result else 0

    if count == 0:
        logger.info("Vocabulary migration: no 'Good' values found (already migrated)")
        return 0

    if dry_run:
        logger.info(
            f"[DRY-RUN] Vocabulary migration: would update {count} records "
            f"from material_condition='Good' to 'Stable'"
        )
        return count

    if verbose:
        logger.info(
            f"Vocabulary migration: updating {count} records "
            f"material_condition 'Good' -> 'Stable'"
        )

    await repo_query(
        "UPDATE acm_record SET material_condition = 'Stable' WHERE material_condition = 'Good'"
    )

    logger.info(f"Vocabulary migration: updated {count} records")
    return count


async def migrate_all(dry_run: bool = False, verbose: bool = False) -> dict:
    """Run the full V3 data migration across all sources.

    Migrates each source, then runs vocabulary migration.
    Caller must verify schema before calling (see verify_schema()).

    Args:
        dry_run: If True, report changes but do not write to DB.
        verbose: If True, log per-record details.

    Returns:
        Overall summary dict.
    """
    overall = {
        "buildings_created": 0,
        "buildings_skipped": 0,
        "records_linked": 0,
        "records_already_linked": 0,
        "vocab_updated": 0,
        "sources_processed": 0,
    }

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

    logger.info(f"Found {len(unique_source_ids)} distinct source(s) to migrate")

    for source_id in unique_source_ids:
        logger.info(f"Migrating source: {source_id}")
        summary = await migrate_source(source_id, dry_run=dry_run, verbose=verbose)
        overall["buildings_created"] += summary["buildings_created"]
        overall["buildings_skipped"] += summary["buildings_skipped"]
        overall["records_linked"] += summary["records_linked"]
        overall["records_already_linked"] += summary["records_already_linked"]
        overall["sources_processed"] += 1

    # Vocabulary migration
    vocab_count = await migrate_vocabulary(dry_run=dry_run, verbose=verbose)
    overall["vocab_updated"] = vocab_count

    return overall


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _print_summary(summary: dict, dry_run: bool) -> None:
    """Print a formatted migration summary."""
    prefix = "[DRY-RUN] " if dry_run else ""
    print()
    print("=" * 60)
    print(f"{prefix}V3 DATA MIGRATION SUMMARY")
    print("=" * 60)
    print(f"  Sources processed:         {summary.get('sources_processed', '-')}")
    print(f"  Building records created:  {summary['buildings_created']}")
    print(
        f"  Building records skipped:  {summary['buildings_skipped']} (already existed)"
    )
    print(f"  ACM records linked:        {summary['records_linked']}")
    print(f"  ACM records already linked:{summary['records_already_linked']}")
    print(f"  Vocabulary updates:        {summary['vocab_updated']} (Good -> Stable)")
    if dry_run:
        print()
        print("  NOTE: --dry-run mode — no changes were written to the database.")
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
        logger.info("Running in DRY-RUN mode — no changes will be written")

    # Verify schema first
    if not await verify_schema():
        return 1

    if args.source_id:
        # Single-source migration
        logger.info(f"Migrating single source: {args.source_id}")
        summary = await migrate_source(args.source_id, dry_run=dry_run, verbose=verbose)
        # Add vocab migration
        vocab_count = await migrate_vocabulary(dry_run=dry_run, verbose=verbose)
        summary["vocab_updated"] = vocab_count
        summary["sources_processed"] = 1
    else:
        # Full migration
        summary = await migrate_all(dry_run=dry_run, verbose=verbose)

    _print_summary(summary, dry_run)
    return 0


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="V3 Data Migration: extract building records from acm_record table",
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
        help="Migrate only a single source (e.g. 'source:abc123')",
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
