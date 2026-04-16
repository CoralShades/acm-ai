# User Authentication — Technical Specification

**Date:** 2026-04-16
**Branch:** feat/user-auth

## Architecture

```
Browser (8502)                     FastAPI (5055)                    SurrealDB (8000)
┌──────────────┐    JWT header    ┌──────────────────┐    root      ┌────────────┐
│ Next.js App  │─────────────────▶│ AuthMiddleware   │─────────────▶│ user table │
│              │                  │  ↓ validates JWT  │              │ source     │
│ middleware.ts│ redirect /login  │  ↓ loads user     │              │ notebook   │
│ auth-store   │◀─────────────────│  ↓ injects user   │              │ acm_item   │
│ LoginForm    │                  │                    │              │ acm_register│
└──────────────┘                  └──────────────────┘              └────────────┘
                                       │
                                  LangGraph/Worker ──────── root access (unchanged)
```

## Auth Resolution Order

```
1. If OPEN_NOTEBOOK_PASSWORD is set → old shared-password mode (backward compat)
2. Else if user table has records   → per-user JWT auth mode
3. Else                             → no auth (dev mode, unprotected)
```

## Database Schema

### Migration: DEFINE TABLE user

```surrealql
-- Migration XX: User authentication table
DEFINE TABLE IF NOT EXISTS user SCHEMAFULL;

DEFINE FIELD username ON user TYPE string;
DEFINE FIELD email ON user TYPE string ASSERT string::is::email($value);
DEFINE FIELD password_hash ON user TYPE string;
DEFINE FIELD role ON user TYPE string ASSERT $value IN ['admin', 'user'] DEFAULT 'user';
DEFINE FIELD status ON user TYPE string ASSERT $value IN ['active', 'inactive'] DEFAULT 'active';
DEFINE FIELD name ON user TYPE option<string>;
DEFINE FIELD created_at ON user TYPE datetime DEFAULT time::now();
DEFINE FIELD updated_at ON user TYPE datetime DEFAULT time::now();
DEFINE FIELD last_login ON user TYPE option<datetime>;

DEFINE INDEX idx_user_email ON user FIELDS email UNIQUE;
DEFINE INDEX idx_user_username ON user FIELDS username UNIQUE;
```

### Migration: Add owner field to existing tables

```surrealql
-- Migration XX+1: Add owner field for per-user data isolation
DEFINE FIELD IF NOT EXISTS owner ON TABLE source TYPE option<record<user>>;
DEFINE FIELD IF NOT EXISTS owner ON TABLE notebook TYPE option<record<user>>;
DEFINE FIELD IF NOT EXISTS owner ON TABLE acm_item TYPE option<record<user>>;
DEFINE FIELD IF NOT EXISTS owner ON TABLE acm_register TYPE option<record<user>>;

DEFINE INDEX IF NOT EXISTS idx_source_owner ON source FIELDS owner;
DEFINE INDEX IF NOT EXISTS idx_notebook_owner ON notebook FIELDS owner;
DEFINE INDEX IF NOT EXISTS idx_acm_item_owner ON acm_item FIELDS owner;
DEFINE INDEX IF NOT EXISTS idx_acm_register_owner ON acm_register FIELDS owner;
```

## Backend API

### New Dependencies
- `PyJWT>=2.8.0` — JWT encode/decode
- `passlib[bcrypt]>=1.7.4` — Password hashing (bcrypt)

### New Files

| File | Purpose |
|------|---------|
| `api/auth_service.py` | JWT creation, password hashing, user validation |
| `api/auth_dependencies.py` | FastAPI Depends() for get_current_user, require_admin |
| `api/routers/auth.py` | Extended: login, me, change-password endpoints |
| `api/routers/admin.py` | Admin user management endpoints |
| `commands/create_admin.py` | CLI seed script for first admin |
| `migrations/XX_user_auth.surrealql` | User table migration |
| `migrations/XX_owner_fields.surrealql` | Owner field migration |

### Modified Files

| File | Change |
|------|--------|
| `api/main.py` | Replace PasswordAuthMiddleware with JWTAuthMiddleware |
| `api/auth.py` | Refactor: dual-mode auth (legacy password OR JWT) |
| `api/routers/sources.py` | Add `user = Depends(get_current_user)`, filter by owner |
| `api/routers/notebooks.py` | Add owner filtering |
| `api/routers/acm.py` | Add owner filtering |
| `open_notebook/domain/notebook.py` | Add owner field to model |
| `open_notebook/domain/base.py` | Handle owner RecordID conversion |

### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/login` | Public | Email + password login, returns JWT |
| GET | `/api/auth/me` | JWT | Get current user profile |
| POST | `/api/auth/change-password` | JWT | Change own password |
| GET | `/api/auth/status` | Public | Check if auth is enabled (existing) |
| POST | `/api/auth/admin/users` | Admin | Create new user |
| GET | `/api/auth/admin/users` | Admin | List all users |
| PATCH | `/api/auth/admin/users/{id}` | Admin | Update user role/status |
| POST | `/api/auth/admin/users/{id}/reset-password` | Admin | Reset user password |

### JWT Payload

```json
{
  "sub": "user:abc123",
  "email": "demi@silvatron.com",
  "role": "admin",
  "username": "demi",
  "exp": 1713484800,
  "iat": 1713398400
}
```

### Auth Middleware Logic

```python
class JWTAuthMiddleware:
    async def dispatch(self, request, call_next):
        # 1. Check if OPEN_NOTEBOOK_PASSWORD mode
        if self.legacy_password:
            return self._legacy_check(request, call_next)
        
        # 2. Skip public endpoints
        if self._is_public(request.url.path):
            return await call_next(request)
        
        # 3. Validate JWT from Authorization header
        token = self._extract_token(request)
        user = self._validate_jwt(token)
        
        # 4. Check user status (soft delete check)
        if user.status != 'active':
            return JSONResponse(401, {"detail": "Account deactivated"})
        
        # 5. Inject user into request state
        request.state.user = user
        return await call_next(request)
```

## Frontend

### New Files

| File | Purpose |
|------|---------|
| `frontend/src/middleware.ts` | Next.js route protection middleware |
| `frontend/src/components/auth/ChangePasswordDialog.tsx` | Change password modal |
| `frontend/src/components/auth/UserMenu.tsx` | Sidebar user avatar + dropdown |

### Modified Files

| File | Change |
|------|--------|
| `frontend/src/components/auth/LoginForm.tsx` | Add email field, new branding |
| `frontend/src/lib/stores/auth-store.ts` | Store user object, JWT with claims |
| `frontend/src/lib/types/auth.ts` | Add User, LoginCredentials types |
| `frontend/src/lib/hooks/use-auth.ts` | Return user object, update login flow |
| `frontend/src/lib/api/client.ts` | No change needed (already sends Bearer) |
| `frontend/src/components/layout/AppSidebar.tsx` | Add UserMenu, hide admin items for non-admins |
| `frontend/src/app/(dashboard)/layout.tsx` | Simplify (middleware.ts handles redirect) |

### Next.js Middleware

```typescript
// frontend/src/middleware.ts
import { NextRequest, NextResponse } from 'next/server'

const publicPaths = ['/login', '/_next', '/favicon.ico']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Skip public paths
  if (publicPaths.some(p => pathname.startsWith(p))) {
    return NextResponse.next()
  }
  
  // Check for token in cookie or localStorage-synced cookie
  const token = request.cookies.get('acm_token')?.value
  
  if (!token) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }
  
  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|.*\\.png$|.*\\.ico$).*)']
}
```

## Environment Variables

```bash
# New in .env
ACM_JWT_SECRET=<64-char-hex>          # JWT signing key
ACM_ADMIN_EMAIL=demi.thathsara@silvatron.com
ACM_ADMIN_PASSWORD=<initial-password>  # Used by seed script only
ACM_ADMIN_USERNAME=demi

# Existing (kept as fallback)
# OPEN_NOTEBOOK_PASSWORD=              # Unset to use per-user auth
```

## Verification Checklist
- [ ] `uv run pytest` passes
- [ ] `uv run ruff check .` passes
- [ ] `cd frontend && npm run build` passes
- [ ] Login with email + password works
- [ ] Admin can create new users via API
- [ ] Non-admin cannot access admin endpoints
- [ ] Users only see their own sources/notebooks
- [ ] Admin sees all data
- [ ] Change password works
- [ ] Deactivated user cannot login
- [ ] Legacy OPEN_NOTEBOOK_PASSWORD still works when set
- [ ] SSE/extraction events work without auth
- [ ] Existing LangGraph/worker processes unaffected
