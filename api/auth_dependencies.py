"""
FastAPI authentication dependencies.
Use these as Depends() in route handlers to enforce auth.
"""

from typing import Any, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.auth_service import decode_access_token, get_user_by_id

security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict[str, Any]]:
    """Extract current user from JWT if present. Returns None if no auth.
    Use this for endpoints that work with or without auth."""
    # Check if user was injected by middleware (legacy or JWT mode)
    if hasattr(request.state, "user") and request.state.user:
        return request.state.user
    # Fallback: try extracting from Authorization header directly
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None
    user = await get_user_by_id(payload["sub"])
    if user and user.get("status") == "active":
        return user
    return None


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict[str, Any]:
    """Extract and validate current user from JWT. Raises 401 if not authenticated."""
    user = await get_current_user_optional(request, credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def require_admin(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Require authenticated user with admin role. Raises 403 if not admin."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
