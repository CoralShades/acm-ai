"""
Admin router for ACM-AI API.
Provides user management endpoints (admin-only).
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, EmailStr

from api.auth_dependencies import require_admin
from api.auth_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    list_users,
    reset_user_password,
    update_user,
    validate_password_strength,
)

router = APIRouter(prefix="/admin", tags=["admin"])


class CreateUserRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: str = "user"
    name: Optional[str] = None


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None
    name: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    new_password: str


@router.post("/users")
async def admin_create_user(
    request: CreateUserRequest,
    admin: dict[str, Any] = Depends(require_admin),
):
    """Create a new user (admin only)."""
    # Validate password
    valid, msg = validate_password_strength(request.password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    # Check for duplicate email
    existing = await get_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Check for duplicate username
    existing = await get_user_by_username(request.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")

    # Validate role
    if request.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'")

    user = await create_user(
        email=request.email,
        username=request.username,
        password=request.password,
        role=request.role,
        name=request.name,
    )

    logger.info(
        f"auth.admin action=create_user target={request.email} by={admin['email']}"
    )

    return {
        "id": user["id"],
        "email": user["email"],
        "username": user["username"],
        "role": user["role"],
        "status": user["status"],
        "name": user.get("name"),
    }


@router.get("/users")
async def admin_list_users(
    admin: dict[str, Any] = Depends(require_admin),
):
    """List all users (admin only)."""
    users = await list_users()
    return {"users": users, "total": len(users)}


@router.patch("/users/{user_id}")
async def admin_update_user(
    user_id: str,
    request: UpdateUserRequest,
    admin: dict[str, Any] = Depends(require_admin),
):
    """Update a user's role or status (admin only)."""
    # Resolve the full user ID if just the key part was provided
    if ":" not in user_id:
        user_id = f"user:{user_id}"

    # Check user exists
    target = await get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate role if provided
    if request.role and request.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'")

    # Validate status if provided
    if request.status and request.status not in ("active", "inactive"):
        raise HTTPException(
            status_code=400, detail="Status must be 'active' or 'inactive'"
        )

    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    updated = await update_user(user_id, updates)

    logger.info(
        f"auth.admin action=update_user target={user_id} updates={updates} by={admin['email']}"
    )

    return updated


@router.post("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: str,
    request: ResetPasswordRequest,
    admin: dict[str, Any] = Depends(require_admin),
):
    """Reset a user's password (admin only)."""
    if ":" not in user_id:
        user_id = f"user:{user_id}"

    # Validate new password
    valid, msg = validate_password_strength(request.new_password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    target = await get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    success = await reset_user_password(user_id, request.new_password)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reset password")

    logger.info(
        f"auth.admin action=reset_password target={user_id} by={admin['email']}"
    )

    return {"message": f"Password reset for {target['email']}"}


@router.delete("/users/{user_id}")
async def admin_deactivate_user(
    user_id: str,
    admin: dict[str, Any] = Depends(require_admin),
):
    """Deactivate a user account (soft delete, admin only)."""
    if ":" not in user_id:
        user_id = f"user:{user_id}"

    target = await get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-deactivation
    if target["id"] == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    updated = await update_user(user_id, {"status": "inactive"})

    logger.info(
        f"auth.admin action=deactivate_user target={user_id} by={admin['email']}"
    )

    return {"message": f"User {target['email']} deactivated", "user": updated}
