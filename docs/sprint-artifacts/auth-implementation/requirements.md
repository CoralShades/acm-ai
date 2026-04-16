# User Authentication — Requirements (Interview Summary)

**Date:** 2026-04-16
**Branch:** feat/user-auth
**Interviewer rounds:** 10/10

## Decisions

### Authentication Model
- **Method:** Email + Password (per-user accounts)
- **Registration:** Admin-only (no self-registration)
- **Roles:** Admin + User (2-tier)

### Session Management
- **Token storage:** JWT in localStorage (current pattern), sent via Authorization header
- **Token expiry:** 24 hours
- **JWT signing:** HS256 with `ACM_JWT_SECRET` env var
- **Password policy:** Standard (8+ chars, mixed case + number)

### SurrealDB Architecture
- **Auth layer:** Application-level only (FastAPI validates JWT, DB stays root-access)
- **Fallback:** Keep `OPEN_NOTEBOOK_PASSWORD` as backward-compatible fallback
- **Worker/LLM access:** Root DB access preserved for LangGraph, LangChain, worker processes

### Data Isolation
- **Scope:** Per-user data isolation (users see only their own data)
- **Future:** Team-based isolation planned
- **Owner tables:** source, notebook, acm_item, acm_register
- **Legacy data:** Assigned to first admin user on migration
- **Filtering:** Repository/query level with `current_user` context
- **Admin bypass:** Admins see all data

### Admin Capabilities
- **Scope:** Essential admin API only (no admin UI in v1)
- **Endpoints:** Create user, list users, update role/status, reset password, deactivate
- **Bootstrap:** Seed script + env vars for first admin

### Frontend
- **Login page:** Upgrade existing form with new design + branding
- **Route protection:** Next.js middleware.ts (server-side)
- **User profile:** Sidebar avatar + dropdown (hide settings from non-admin users)
- **Password change:** Self-service change-password dialog
- **Force change on first login:** No

### Security & Deployment
- **Rate limiting:** None (simple for now)
- **Account deactivation:** Soft delete + immediate session invalidation
- **Audit logging:** Basic Python logger (auth events with IP)
- **CORS:** Keep wildcard CORS with token in Authorization header
- **Env template:** .env.example with placeholders
- **SSE endpoints:** Stay public (no auth required)

### First Admin
- **Username:** demi
- **Email:** demi.thathsara@silvatron.com
- **Password:** (set in .env, never committed)

## Non-Goals (explicitly out of scope)
- OAuth / SSO / Magic link
- Admin UI panel
- Email notifications
- 2FA / MFA
- Rate limiting / brute force protection
- Team/organization hierarchy
- SurrealDB DEFINE ACCESS scoped auth
