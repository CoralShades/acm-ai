"""Repository for consultant format profiles (SurrealDB).

CRUD operations for the consultant_format_profile table, which caches
column header → SF field mappings keyed by header signature hash.

Story: Multi-Consultant Story 3 — Format Profile Registry
"""

from typing import Any, Optional

from loguru import logger

from open_notebook.database.repository import repo_create, repo_delete, repo_query


async def get_profile_by_signature(
    header_signature: str,
) -> Optional[dict[str, Any]]:
    """Look up a cached format profile by header signature.

    Returns the first matching profile dict, or None on cache miss.
    """
    results = await repo_query(
        "SELECT * FROM consultant_format_profile WHERE header_signature = $sig LIMIT 1",
        {"sig": header_signature},
    )
    if results and len(results) > 0:
        return results[0]
    return None


async def save_profile(profile_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Save a new format profile to the database.

    Args:
        profile_data: Dict with header_signature, column_mapping,
            canonical_mapping, confidence, consultant_name, etc.

    Returns:
        List with the created record.
    """
    return await repo_create("consultant_format_profile", profile_data)


async def increment_sample_count(profile_id: str) -> list[dict[str, Any]]:
    """Increment sample_count and update updated_at for a cached profile.

    Called on cache hits to track how many documents matched this profile.
    """
    return await repo_query(
        "UPDATE $id SET sample_count += 1, updated_at = time::now()",
        {"id": profile_id},
    )


async def delete_profile(profile_id: str) -> None:
    """Delete a format profile by record ID."""
    await repo_delete(profile_id)


async def list_profiles() -> list[dict[str, Any]]:
    """List all format profiles, ordered by sample_count descending."""
    return await repo_query(
        "SELECT * FROM consultant_format_profile ORDER BY sample_count DESC"
    )
