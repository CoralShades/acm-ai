"""
V3 Building Record Rollback Script (E35-S6, AC4)

Reverses the building backfill: removes building_record_id FK from acm_records
and deletes the corresponding building_record entries.

Usage:
    uv run python scripts/v3_building_rollback.py --source-id SOURCE_ID [--dry-run] [--verbose]
    uv run python scripts/v3_building_rollback.py --all [--dry-run] [--verbose]

Algorithm:
    1. Fetch building_records for source (or all sources)
    2. For each building_record:
       a. UPDATE acm_record SET building_record_id = NONE WHERE building_record_id = $bld_id
       b. DELETE building_record WHERE id = $bld_id
    3. Print summary

Safety:
    Requires either --source-id or --all flag to prevent accidental execution.
"""

import argparse
import asyncio
import sys
from dataclasses import dataclass
from typing import Optional

from loguru import logger

from open_notebook.database.repository import ensure_record_id, repo_query

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class RollbackResult:
    """Summary of a building rollback run."""

    sources_processed: int = 0
    buildings_deleted: int = 0
    records_unlinked: int = 0


# ---------------------------------------------------------------------------
# Single-source rollback
# ---------------------------------------------------------------------------


async def rollback_source(
    source_id: str,
    dry_run: bool = False,
    verbose: bool = False,
) -> RollbackResult:
    """Rollback building records for a single source.

    Unlinks all acm_records from their building_records and then deletes
    the building_record entries.

    Args:
        source_id: The SurrealDB source ID (e.g. "source:abc123").
        dry_run: If True, report changes but do not write to DB.
        verbose: If True, log per-record details.

    Returns:
        RollbackResult with counts of buildings deleted and records unlinked.
    """
    result = RollbackResult()

    # Fetch building_records for this source
    buildings = await repo_query(
        "SELECT id FROM building_record WHERE source_id = $src",
        {"src": ensure_record_id(source_id)},
    )

    if not buildings:
        logger.info(f"No building_records found for source {source_id}")
        return result

    logger.info(f"Found {len(buildings)} building_record(s) for source {source_id}")

    for bld in buildings:
        bld_id = bld.get("id")
        if not bld_id:
            continue

        bld_id_str = str(bld_id)

        if verbose:
            logger.info(f"  Processing building_record {bld_id_str}")

        # Count acm_records that reference this building_record
        count_result = await repo_query(
            "SELECT count() AS total FROM acm_record "
            "WHERE building_record_id = $bld_id GROUP ALL",
            {"bld_id": ensure_record_id(bld_id_str)},
        )
        linked_count = count_result[0].get("total", 0) if count_result else 0

        if dry_run:
            logger.info(
                f"  [DRY-RUN] Would unlink {linked_count} acm_record(s) "
                f"and delete building_record {bld_id_str}"
            )
            result.records_unlinked += linked_count
            result.buildings_deleted += 1
            continue

        # Unlink acm_records: SET building_record_id = NONE
        await repo_query(
            "UPDATE acm_record SET building_record_id = NONE "
            "WHERE building_record_id = $bld_id",
            {"bld_id": ensure_record_id(bld_id_str)},
        )
        result.records_unlinked += linked_count

        if verbose:
            logger.info(
                f"    -> Unlinked {linked_count} acm_record(s) from {bld_id_str}"
            )

        # Delete the building_record
        await repo_query(
            "DELETE building_record WHERE id = $bld_id",
            {"bld_id": ensure_record_id(bld_id_str)},
        )
        result.buildings_deleted += 1

        if verbose:
            logger.info(f"    -> Deleted building_record {bld_id_str}")

    return result


# ---------------------------------------------------------------------------
# Full rollback (all sources)
# ---------------------------------------------------------------------------


async def rollback_all(
    dry_run: bool = False,
    verbose: bool = False,
) -> RollbackResult:
    """Rollback building records across all sources.

    Args:
        dry_run: If True, report changes but do not write to DB.
        verbose: If True, log per-record details.

    Returns:
        Aggregated RollbackResult across all sources.
    """
    overall = RollbackResult()

    # Fetch all distinct source_ids from building_record
    source_rows = await repo_query("SELECT DISTINCT source_id FROM building_record")

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

    logger.info(f"Found {len(unique_source_ids)} distinct source(s) to rollback")

    for source_id in unique_source_ids:
        logger.info(f"Rolling back source: {source_id}")
        source_result = await rollback_source(
            source_id, dry_run=dry_run, verbose=verbose
        )
        overall.sources_processed += 1
        overall.buildings_deleted += source_result.buildings_deleted
        overall.records_unlinked += source_result.records_unlinked

    return overall


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _print_summary(result: RollbackResult, dry_run: bool) -> None:
    """Print a formatted rollback summary."""
    prefix = "[DRY-RUN] " if dry_run else ""
    print()
    print("=" * 60)
    print(f"{prefix}V3 BUILDING ROLLBACK SUMMARY")
    print("=" * 60)
    print(f"  Sources processed:         {result.sources_processed}")
    print(f"  Building records deleted:  {result.buildings_deleted}")
    print(f"  ACM records unlinked:      {result.records_unlinked}")
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

    if args.source_id:
        logger.info(f"Rolling back single source: {args.source_id}")
        result = await rollback_source(args.source_id, dry_run=dry_run, verbose=verbose)
        result.sources_processed = 1
    elif args.all:
        result = await rollback_all(dry_run=dry_run, verbose=verbose)
    else:
        logger.error("Must specify either --source-id SOURCE_ID or --all flag")
        return 1

    _print_summary(result, dry_run)
    return 0


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="V3 Building Rollback: remove building_record entries and unlink acm_records",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--source-id",
        metavar="SOURCE_ID",
        default=None,
        help="Rollback only a single source (e.g. 'source:abc123')",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Rollback ALL sources (required if --source-id not given)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Report what would change without writing to the database",
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
