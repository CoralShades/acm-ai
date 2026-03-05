"""
V3 Data Migration Rollback Script (E30-S5)

Reverses the V3 data migration:
1. Nulls out building_record_id on all acm_record rows
2. Deletes all building_record rows
3. Optionally reverts material_condition 'Stable' -> 'Good' (--revert-vocab)

NOTE: acm_record rows are NOT deleted — only the FK and building_records are removed.

Usage:
    uv run python scripts/v3_data_migration_rollback.py [--source-id SOURCE_ID] [--revert-vocab]
"""

import argparse
import asyncio
import sys
from typing import Optional

from loguru import logger

from open_notebook.database.repository import ensure_record_id, repo_query

# ---------------------------------------------------------------------------
# Rollback helpers (importable for testing)
# ---------------------------------------------------------------------------


async def rollback_source(
    source_id: str,
    revert_vocab: bool = False,
    verbose: bool = False,
) -> dict:
    """Rollback migration for a single source.

    1. Null out building_record_id on acm_records for this source.
    2. Delete all building_records for this source.
    3. Optionally revert material_condition 'Stable' -> 'Good' for this source.

    Args:
        source_id: The SurrealDB source ID (e.g. "source:abc123").
        revert_vocab: If True, also revert 'Stable' -> 'Good' for this source.
        verbose: If True, log per-record details.

    Returns:
        Summary dict with keys: fks_nulled, buildings_deleted, vocab_reverted.
    """
    summary = {
        "fks_nulled": 0,
        "buildings_deleted": 0,
        "vocab_reverted": 0,
    }

    src_record_id = ensure_record_id(source_id)

    # 1. Null out building_record_id on acm_records
    null_result = await repo_query(
        "UPDATE acm_record SET building_record_id = NONE "
        "WHERE source_id = $src AND building_record_id != NONE "
        "RETURN BEFORE",
        {"src": src_record_id},
    )
    summary["fks_nulled"] = len(null_result) if null_result else 0
    if verbose:
        logger.info(
            f"  Nulled building_record_id on {summary['fks_nulled']} acm_records "
            f"for source {source_id}"
        )

    # 2. Delete all building_records for this source
    del_result = await repo_query(
        "DELETE building_record WHERE source_id = $src RETURN BEFORE",
        {"src": src_record_id},
    )
    summary["buildings_deleted"] = len(del_result) if del_result else 0
    if verbose:
        logger.info(
            f"  Deleted {summary['buildings_deleted']} building_records "
            f"for source {source_id}"
        )

    # 3. Optional vocabulary revert for this source
    if revert_vocab:
        count_result = await repo_query(
            "SELECT count() AS total FROM acm_record "
            "WHERE source_id = $src AND material_condition = 'Stable' GROUP ALL",
            {"src": src_record_id},
        )
        count = count_result[0].get("total", 0) if count_result else 0
        if count > 0:
            await repo_query(
                "UPDATE acm_record SET material_condition = 'Good' "
                "WHERE source_id = $src AND material_condition = 'Stable'",
                {"src": src_record_id},
            )
            summary["vocab_reverted"] = count
            if verbose:
                logger.info(
                    f"  Reverted {count} records: material_condition 'Stable' -> 'Good' "
                    f"for source {source_id}"
                )

    return summary


async def rollback_all(
    revert_vocab: bool = False,
    verbose: bool = False,
) -> dict:
    """Rollback migration for all sources.

    1. Null out building_record_id on ALL acm_records.
    2. Delete ALL building_records.
    3. Optionally revert 'Stable' -> 'Good' globally.

    Args:
        revert_vocab: If True, also revert 'Stable' -> 'Good' across all sources.
        verbose: If True, log per-step details.

    Returns:
        Overall summary dict.
    """
    summary = {
        "fks_nulled": 0,
        "buildings_deleted": 0,
        "vocab_reverted": 0,
    }

    # 1. Null out all FKs across all acm_records
    null_result = await repo_query(
        "UPDATE acm_record SET building_record_id = NONE "
        "WHERE building_record_id != NONE RETURN BEFORE"
    )
    summary["fks_nulled"] = len(null_result) if null_result else 0
    if verbose:
        logger.info(f"Nulled building_record_id on {summary['fks_nulled']} acm_records")

    # 2. Delete all building_records
    del_result = await repo_query("DELETE building_record RETURN BEFORE")
    summary["buildings_deleted"] = len(del_result) if del_result else 0
    if verbose:
        logger.info(f"Deleted {summary['buildings_deleted']} building_records")

    # 3. Optional global vocabulary revert
    if revert_vocab:
        count_result = await repo_query(
            "SELECT count() AS total FROM acm_record "
            "WHERE material_condition = 'Stable' GROUP ALL"
        )
        count = count_result[0].get("total", 0) if count_result else 0
        if count > 0:
            await repo_query(
                "UPDATE acm_record SET material_condition = 'Good' "
                "WHERE material_condition = 'Stable'"
            )
            summary["vocab_reverted"] = count
            if verbose:
                logger.info(
                    f"Reverted {count} records: material_condition 'Stable' -> 'Good'"
                )
        else:
            logger.info(
                "Vocabulary revert: no 'Stable' values found "
                "(already reverted or never migrated)"
            )

    return summary


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _print_summary(summary: dict, source_id: Optional[str]) -> None:
    """Print a formatted rollback summary."""
    scope = f"source {source_id}" if source_id else "ALL sources"
    print()
    print("=" * 60)
    print(f"V3 DATA MIGRATION ROLLBACK SUMMARY ({scope})")
    print("=" * 60)
    print(f"  ACM record FKs nulled:     {summary['fks_nulled']}")
    print(f"  Building records deleted:  {summary['buildings_deleted']}")
    print(f"  Vocab reverted (Stable->Good): {summary['vocab_reverted']}")
    print("=" * 60)
    print()


async def _main(args: argparse.Namespace) -> int:
    """Async main function for the CLI."""
    logger.remove()
    log_level = "DEBUG" if args.verbose else "INFO"
    logger.add(sys.stderr, level=log_level)

    source_id: Optional[str] = args.source_id
    revert_vocab: bool = args.revert_vocab
    verbose: bool = args.verbose

    logger.warning(
        "ROLLBACK: This will delete all building_record rows and null out "
        "building_record_id on acm_records. acm_record rows are NOT deleted."
    )

    if source_id:
        logger.info(f"Rolling back source: {source_id}")
        summary = await rollback_source(
            source_id, revert_vocab=revert_vocab, verbose=verbose
        )
    else:
        logger.info("Rolling back ALL sources")
        summary = await rollback_all(revert_vocab=revert_vocab, verbose=verbose)

    _print_summary(summary, source_id)
    return 0


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="V3 Data Migration Rollback: remove building_records and null FKs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--source-id",
        metavar="SOURCE_ID",
        default=None,
        help="Rollback only a single source (e.g. 'source:abc123'). "
        "If omitted, all sources are rolled back.",
    )
    parser.add_argument(
        "--revert-vocab",
        action="store_true",
        default=False,
        help="Also revert material_condition 'Stable' -> 'Good' (use with caution)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable detailed logging",
    )

    args = parser.parse_args()
    exit_code = asyncio.run(_main(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
