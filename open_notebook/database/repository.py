import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypeVar, Union

from loguru import logger
from surrealdb import AsyncSurreal, RecordID  # type: ignore

T = TypeVar("T", Dict[str, Any], List[Dict[str, Any]])


def get_database_url():
    """Get database URL with backward compatibility"""
    surreal_url = os.getenv("SURREAL_URL")
    if surreal_url:
        return surreal_url

    # Fallback to old format - WebSocket URL format
    address = os.getenv("SURREAL_ADDRESS", "localhost")
    port = os.getenv("SURREAL_PORT", "8000")
    return f"ws://{address}/rpc:{port}"


def get_database_password():
    """Get password with backward compatibility"""
    return os.getenv("SURREAL_PASSWORD") or os.getenv("SURREAL_PASS")


def parse_record_ids(obj: Any) -> Any:
    """Recursively parse and convert RecordIDs into strings."""
    if isinstance(obj, dict):
        return {k: parse_record_ids(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [parse_record_ids(item) for item in obj]
    elif isinstance(obj, RecordID):
        return str(obj)
    return obj


def ensure_record_id(value: Union[str, RecordID]) -> RecordID:
    """Ensure a value is a RecordID."""
    if isinstance(value, RecordID):
        return value
    return RecordID.parse(value)


@asynccontextmanager
async def db_connection():
    db = AsyncSurreal(get_database_url())
    await db.signin(
        {
            "username": os.environ.get("SURREAL_USER"),
            "password": get_database_password(),
        }
    )
    await db.use(
        os.environ.get("SURREAL_NAMESPACE"), os.environ.get("SURREAL_DATABASE")
    )
    try:
        yield db
    finally:
        await db.close()


async def repo_query(
    query_str: str, vars: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Execute a SurrealQL query and return the results"""

    async with db_connection() as connection:
        try:
            result = parse_record_ids(await connection.query(query_str, vars))
            if isinstance(result, str):
                raise RuntimeError(result)
            return result
        except RuntimeError as e:
            # RuntimeError is raised for retriable transaction conflicts - log without stack trace
            logger.error(str(e))
            raise
        except Exception as e:
            logger.exception(e)
            raise


async def repo_create(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new record in the specified table"""
    # Remove 'id' attribute if it exists in data
    data.pop("id", None)
    data["created"] = datetime.now(timezone.utc)
    data["updated"] = datetime.now(timezone.utc)
    try:
        async with db_connection() as connection:
            raw_result = await connection.insert(table, data)
            parsed = parse_record_ids(raw_result)
            # Ghost save diagnostic: log if result is not a list of dicts
            if table in ("acm_record", "building_record", "acm_table_section"):
                if isinstance(parsed, list) and parsed and not isinstance(parsed[0], dict):
                    logger.error(
                        f"[GHOST-SAVE] {table} insert returned non-dict: "
                        f"type={type(parsed[0]).__name__} value={repr(parsed[0])[:200]}"
                    )
                elif isinstance(parsed, str):
                    logger.error(
                        f"[GHOST-SAVE] {table} insert returned string: {repr(parsed)[:200]}"
                    )
                elif isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                    logger.info(
                        f"[SAVE-OK] {table} insert succeeded: id={parsed[0].get('id', 'NO-ID')}"
                    )
            return parsed
    except RuntimeError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        logger.exception(e)
        raise RuntimeError("Failed to create record")


async def repo_relate(
    source: str, relationship: str, target: str, data: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Create a relationship between two records with optional data"""
    if data is None:
        data = {}
    query = f"RELATE {source}->{relationship}->{target} CONTENT $data;"
    # logger.debug(f"Relate query: {query}")

    return await repo_query(
        query,
        {
            "data": data,
        },
    )


async def repo_upsert(
    table: str, id: Optional[str], data: Dict[str, Any], add_timestamp: bool = False
) -> List[Dict[str, Any]]:
    """Create or update a record in the specified table"""
    data.pop("id", None)
    if add_timestamp:
        data["updated"] = datetime.now(timezone.utc)
    query = f"UPSERT {id if id else table} MERGE $data;"
    return await repo_query(query, {"data": data})


async def repo_update(
    table: str, id: str, data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Update an existing record by table and id"""
    # If id already contains the table name, use it as is
    try:
        if isinstance(id, RecordID) or (":" in id and id.startswith(f"{table}:")):
            record_id = id
        else:
            record_id = f"{table}:{id}"
        data.pop("id", None)
        if "created" in data and isinstance(data["created"], str):
            data["created"] = datetime.fromisoformat(data["created"])
        data["updated"] = datetime.now(timezone.utc)
        query = f"UPDATE {record_id} MERGE $data;"
        # logger.debug(f"Update query: {query}")
        result = await repo_query(query, {"data": data})
        # if isinstance(result, list):
        #     return [_return_data(item) for item in result]
        return parse_record_ids(result)
    except Exception as e:
        raise RuntimeError(f"Failed to update record: {str(e)}")


async def repo_delete(record_id: Union[str, RecordID]):
    """Delete a record by record id"""

    try:
        async with db_connection() as connection:
            return await connection.delete(ensure_record_id(record_id))
    except Exception as e:
        logger.exception(e)
        raise RuntimeError(f"Failed to delete record: {str(e)}")


async def repo_insert(
    table: str, data: List[Dict[str, Any]], ignore_duplicates: bool = False
) -> List[Dict[str, Any]]:
    """Create a new record in the specified table"""
    try:
        async with db_connection() as connection:
            return parse_record_ids(await connection.insert(table, data))
    except Exception as e:
        if ignore_duplicates and "already contains" in str(e):
            return []
        logger.exception(e)
        raise RuntimeError("Failed to create record")


async def save_source_intelligence(
    source_id: str, data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Upsert pre-extraction intelligence for a source (E30-S9).

    Keyed on source_id — creates on first call, merges on subsequent calls.

    Only fields that are explicitly present and non-None in *data* are written.
    This prevents a partial update (e.g. only document_meta supplied) from
    nullifying fields that already exist in the database row (BUG-REREV-NULLIFY).
    source_id and updated_at are always included because the WHERE clause
    depends on source_id.
    """
    data["source_id"] = ensure_record_id(source_id)
    data["updated_at"] = datetime.now(timezone.utc)

    # Filter out None values so that unset fields are not overwritten with NULL.
    set_fields = {k: v for k, v in data.items() if v is not None}

    # Build a dynamic SET clause from the surviving keys only.
    set_clauses = ", ".join(f"{k} = $data.{k}" for k in set_fields)

    query = (
        f"UPSERT source_intelligence SET "
        f"{set_clauses} "
        "WHERE source_id = $data.source_id;"
    )
    return await repo_query(query, {"data": set_fields})


async def get_source_intelligence(source_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve persisted pre-extraction intelligence for a source (E30-S9)."""
    sid = ensure_record_id(source_id)
    result = await repo_query(
        "SELECT * FROM source_intelligence WHERE source_id = $sid LIMIT 1;",
        {"sid": sid},
    )
    if result and isinstance(result, list) and len(result) > 0:
        rows = result[0] if isinstance(result[0], list) else result
        return rows[0] if rows else None
    return None
