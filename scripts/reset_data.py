"""Reset ACM data in SurrealDB.

Usage:
    uv run python scripts/reset_data.py          # ACM data only (keep sources/notebooks)
    uv run python scripts/reset_data.py --full    # Delete EVERYTHING except model/field_schema config
"""
import argparse
import asyncio

from dotenv import load_dotenv

load_dotenv()

from open_notebook.database.repository import repo_query

ACM_TABLES = [
    "acm_record",
    "building_record",
    "acm_table_section",
    "raw_extraction",
    "source_intelligence",
    "extraction_progress",
    "site_config",
    "agui_events",
]

ALL_TABLES = ACM_TABLES + [
    "source",
    "source_embedding",
    "source_insight",
    "notebook",
    "reference",
    "note",
    "note_embedding",
    "command",
]


async def reset(full: bool) -> None:
    tables = ALL_TABLES if full else ACM_TABLES
    print(f"\nResetting {'ALL' if full else 'ACM'} data...\n")

    for t in tables:
        r = await repo_query(f"DELETE FROM {t} RETURN BEFORE;")
        count = len(r) if r else 0
        print(f"  Deleted {count} rows from {t}")

    if not full:
        await repo_query(
            "UPDATE command SET status = 'failed' WHERE status IN ['running', 'pending'];"
        )
        print("  Marked stale commands as failed")

    print("\nDone. Restart services to continue.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Reset ACM data in SurrealDB")
    p.add_argument(
        "--full",
        action="store_true",
        help="Delete ALL data including sources/notebooks",
    )
    asyncio.run(reset(p.parse_args().full))
