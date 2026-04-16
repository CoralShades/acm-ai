"""
Authentication router for ACM-AI API.
Provides login, profile, password change, and auth status endpoints.
"""

import os
from typing import Any

from fastapi import APIRouter, Depends
from loguru import logger
from pydantic import BaseModel, EmailStr

from api.auth_dependencies import get_current_user
from api.auth_service import (
    authenticate_user,
    change_password,
    create_access_token,
    has_any_users,
    validate_password_strength,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    token: str
    user: dict[str, Any]


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.get("/status")
async def get_auth_status():
    """Check if authentication is enabled and which mode is active."""
    legacy_enabled = bool(os.environ.get("OPEN_NOTEBOOK_PASSWORD"))
    jwt_enabled = bool(os.environ.get("ACM_JWT_SECRET"))
    users_exist = False
    if jwt_enabled:
        try:
            users_exist = await has_any_users()
        except Exception:
            pass

    auth_enabled = legacy_enabled or (jwt_enabled and users_exist)
    mode = "legacy" if legacy_enabled else ("jwt" if jwt_enabled else "none")

    return {
        "auth_enabled": auth_enabled,
        "mode": mode,
        "message": "Authentication is required"
        if auth_enabled
        else "Authentication is disabled",
    }


@router.post("/login")
async def login(request: LoginRequest):
    """Authenticate with email + password and receive a JWT token."""
    user = await authenticate_user(request.email, request.password)
    if not user:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user)

    # Return user info without sensitive fields
    safe_user = {
        "id": user["id"],
        "email": user["email"],
        "username": user.get("username", ""),
        "role": user.get("role", "user"),
        "name": user.get("name", ""),
    }

    logger.info(f"auth.login email={request.email} status=success")
    return {"token": token, "user": safe_user}


@router.get("/me")
async def get_me(user: dict[str, Any] = Depends(get_current_user)):
    """Get current authenticated user's profile."""
    return {
        "id": user["id"],
        "email": user["email"],
        "username": user.get("username", ""),
        "role": user.get("role", "user"),
        "name": user.get("name", ""),
        "status": user.get("status", "active"),
        "last_login": user.get("last_login"),
        "created_at": user.get("created_at"),
    }


@router.post("/change-password")
async def change_user_password(
    request: ChangePasswordRequest,
    user: dict[str, Any] = Depends(get_current_user),
):
    """Change the current user's password."""
    # Validate new password strength
    valid, msg = validate_password_strength(request.new_password)
    if not valid:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=msg)

    success, error = await change_password(
        user["id"], request.current_password, request.new_password
    )
    if not success:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=error)

    return {"message": "Password changed successfully"}
