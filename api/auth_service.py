"""
Authentication service for ACM-AI.
Handles JWT token creation/validation and password hashing.
"""

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import jwt
from loguru import logger

from open_notebook.database.repository import db_connection, parse_record_ids

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


def _first_row(result: list) -> Optional[dict[str, Any]]:
    """Extract the first row from a SurrealDB query result.

    SurrealDB returns different shapes: CREATE returns a single dict,
    SELECT returns a list of dicts. This normalizes both.
    """
    if not result:
        return None
    data = result[0]
    if isinstance(data, dict):
        return parse_record_ids(data)
    if isinstance(data, list) and data:
        return parse_record_ids(data[0])
    return None


def get_jwt_secret() -> str:
    secret = os.environ.get("ACM_JWT_SECRET")
    if not secret:
        raise RuntimeError(
            "ACM_JWT_SECRET is not set. Generate one with: openssl rand -hex 32"
        )
    return secret


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets minimum requirements: 8+ chars, mixed case, number."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    return True, ""


def create_access_token(user_data: dict[str, Any]) -> str:
    """Create a JWT access token for the given user."""
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": user_data["id"],
        "email": user_data["email"],
        "username": user_data.get("username", ""),
        "role": user_data.get("role", "user"),
        "name": user_data.get("name", ""),
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT access token. Returns None on failure."""
    try:
        payload = jwt.decode(
            token, get_jwt_secret(), algorithms=[JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"Invalid JWT token: {e}")
        return None


async def get_user_by_email(email: str) -> Optional[dict[str, Any]]:
    """Fetch a user by email from SurrealDB."""
    async with db_connection() as db:
        result = await db.query(
            "SELECT * FROM user WHERE email = $email LIMIT 1",
            {"email": email},
        )
        return _first_row(result)


async def get_user_by_id(user_id: str) -> Optional[dict[str, Any]]:
    """Fetch a user by ID from SurrealDB."""
    async with db_connection() as db:
        result = await db.query(
            "SELECT * FROM type::thing($id)",
            {"id": user_id},
        )
        return _first_row(result)


async def get_user_by_username(username: str) -> Optional[dict[str, Any]]:
    """Fetch a user by username from SurrealDB."""
    async with db_connection() as db:
        result = await db.query(
            "SELECT * FROM user WHERE username = $username LIMIT 1",
            {"username": username},
        )
        return _first_row(result)


async def authenticate_user(
    email: str, password: str
) -> Optional[dict[str, Any]]:
    """Authenticate a user by email + password. Returns user dict or None."""
    user = await get_user_by_email(email)
    if not user:
        logger.warning(f"auth.login email={email} status=failed reason=not_found")
        return None
    if user.get("status") != "active":
        logger.warning(f"auth.login email={email} status=failed reason=inactive")
        return None
    if not verify_password(password, user["password_hash"]):
        logger.warning(f"auth.login email={email} status=failed reason=bad_password")
        return None

    # Update last_login
    async with db_connection() as db:
        await db.query(
            "UPDATE type::thing($id) SET last_login = time::now()",
            {"id": user["id"]},
        )

    logger.info(f"auth.login email={email} status=success")
    return user


async def create_user(
    email: str,
    username: str,
    password: str,
    role: str = "user",
    name: Optional[str] = None,
) -> dict[str, Any]:
    """Create a new user in SurrealDB."""
    password_hash = hash_password(password)
    async with db_connection() as db:
        result = await db.query(
            """CREATE user CONTENT {
                email: $email,
                username: $username,
                password_hash: $password_hash,
                role: $role,
                name: $name,
                status: 'active',
                created_at: time::now(),
                updated_at: time::now()
            }""",
            {
                "email": email,
                "username": username,
                "password_hash": password_hash,
                "role": role,
                "name": name,
            },
        )
        row = _first_row(result)
        if row:
            return row
        raise RuntimeError("Failed to create user")


async def list_users() -> list[dict[str, Any]]:
    """List all users (admin function). Excludes password_hash."""
    async with db_connection() as db:
        result = await db.query(
            "SELECT id, email, username, role, status, name, "
            "created_at, updated_at, last_login FROM user ORDER BY created_at DESC"
        )
        if not result:
            return []
        # db.query() already unwraps to the statement result:
        # SELECT multi-row → list of dicts, single row → [dict], 0 rows → []
        if isinstance(result, dict):
            return [parse_record_ids(result)]
        return [parse_record_ids(r) for r in result]


async def update_user(
    user_id: str, updates: dict[str, Any]
) -> Optional[dict[str, Any]]:
    """Update user fields. Returns updated user or None."""
    allowed_fields = {"role", "status", "name", "email", "username"}
    filtered = {k: v for k, v in updates.items() if k in allowed_fields}
    if not filtered:
        return None

    filtered["updated_at"] = "time::now()"
    set_clauses = ", ".join(
        f"{k} = time::now()" if v == "time::now()" else f"{k} = ${k}"
        for k, v in filtered.items()
    )
    params = {k: v for k, v in filtered.items() if v != "time::now()"}
    params["id"] = user_id

    async with db_connection() as db:
        result = await db.query(
            f"UPDATE type::thing($id) SET {set_clauses}",
            params,
        )
        return _first_row(result)


async def reset_user_password(
    user_id: str, new_password: str
) -> bool:
    """Admin: reset a user's password."""
    password_hash = hash_password(new_password)
    async with db_connection() as db:
        result = await db.query(
            "UPDATE type::thing($id) SET password_hash = $hash, updated_at = time::now()",
            {"id": user_id, "hash": password_hash},
        )
        return _first_row(result) is not None


async def change_password(
    user_id: str, current_password: str, new_password: str
) -> tuple[bool, str]:
    """User: change own password. Validates current password first."""
    user = await get_user_by_id(user_id)
    if not user:
        return False, "User not found"
    if not verify_password(current_password, user["password_hash"]):
        return False, "Current password is incorrect"

    valid, msg = validate_password_strength(new_password)
    if not valid:
        return False, msg

    password_hash = hash_password(new_password)
    async with db_connection() as db:
        await db.query(
            "UPDATE type::thing($id) SET password_hash = $hash, updated_at = time::now()",
            {"id": user_id, "hash": password_hash},
        )
    logger.info(f"auth.password_change user_id={user_id} status=success")
    return True, ""


async def has_any_users() -> bool:
    """Check if any users exist in the database."""
    async with db_connection() as db:
        result = await db.query("SELECT count() FROM user GROUP ALL")
        row = _first_row(result)
        if row:
            return row.get("count", 0) > 0
    return False


async def assign_legacy_data_to_admin(admin_id: str) -> int:
    """Assign all unowned records to the admin user. Returns count of updated records."""
    total = 0
    async with db_connection() as db:
        for table in ["source", "notebook", "acm_record", "building_record"]:
            result = await db.query(
                f"UPDATE {table} SET owner = type::thing($admin_id) "
                f"WHERE owner IS NONE OR owner IS NULL",
                {"admin_id": admin_id},
            )
            # db.query() already unwraps: UPDATE multi-row → list, single → dict
            if not result:
                rows = []
            elif isinstance(result, dict):
                rows = [result]
            else:
                rows = result
            total += len(rows)
            if rows:
                logger.info(
                    f"Assigned {len(rows)} {table} records to admin {admin_id}"
                )
    return total
