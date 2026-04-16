"""
Dual-mode authentication middleware for ACM-AI.

Resolution order:
1. If OPEN_NOTEBOOK_PASSWORD is set -> legacy shared-password mode (backward compat)
2. Else if ACM_JWT_SECRET is set   -> per-user JWT auth mode
3. Else                            -> no auth (dev mode, unprotected)
"""

import os
from typing import Optional

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from api.auth_service import decode_access_token, get_user_by_id


class AuthMiddleware(BaseHTTPMiddleware):
    """Unified auth middleware supporting legacy password and JWT modes."""

    def __init__(self, app, excluded_paths: Optional[list] = None):
        super().__init__(app)
        self.legacy_password = os.environ.get("OPEN_NOTEBOOK_PASSWORD")
        self.jwt_secret = os.environ.get("ACM_JWT_SECRET")
        self.excluded_paths = excluded_paths or []

    def _is_excluded(self, path: str) -> bool:
        """Check if path is in the excluded list or matches a prefix."""
        for excluded in self.excluded_paths:
            if excluded.endswith("*"):
                if path.startswith(excluded[:-1]):
                    return True
            elif path == excluded:
                return True
        return False

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip for excluded paths
        if self._is_excluded(path):
            return await call_next(request)

        # Skip CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        # Mode 1: Legacy shared password
        if self.legacy_password:
            return await self._legacy_auth(request, call_next)

        # Mode 2: JWT per-user auth
        if self.jwt_secret:
            return await self._jwt_auth(request, call_next)

        # Mode 3: No auth configured — allow all
        return await call_next(request)

    async def _legacy_auth(self, request: Request, call_next):
        """Original shared-password authentication."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            scheme, credentials = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                raise ValueError("Invalid scheme")
        except ValueError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authorization header format"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        if credentials != self.legacy_password:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid password"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)

    async def _jwt_auth(self, request: Request, call_next):
        """JWT-based per-user authentication."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                raise ValueError("Invalid scheme")
        except ValueError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authorization header format"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Decode JWT
        payload = decode_access_token(token)
        if not payload:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify user is still active (soft delete check)
        user = await get_user_by_id(payload["sub"])
        if not user or user.get("status") != "active":
            return JSONResponse(
                status_code=401,
                content={"detail": "Account deactivated"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Inject user into request state for downstream handlers
        request.state.user = user
        return await call_next(request)


# Keep for backward compatibility (OpenAPI docs)
security = HTTPBearer(auto_error=False)


def check_api_password(
    credentials: Optional[HTTPAuthorizationCredentials] = None,
) -> bool:
    """Legacy utility for individual route password checks."""
    password = os.environ.get("OPEN_NOTEBOOK_PASSWORD")
    if not password:
        return True
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if credentials.credentials != password:
        raise HTTPException(
            status_code=401,
            detail="Invalid password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True
