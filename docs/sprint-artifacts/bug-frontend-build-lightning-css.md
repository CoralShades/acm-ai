# Bug: Frontend Build — Lightning CSS Native Module (Windows)

**Status:** done
**Priority:** P1 (Blocking all frontend work)
**Discovered:** 2026-02-26 (Post-audit fix sprint)
**Completed:** 2026-02-26
**Commit:** `7ea7544` — fix(frontend): resolve Lightning CSS native module for Windows build

---

## Description

`npm run build` in `frontend/` failed with:

```
Cannot find module '../lightningcss.linux-x64-gnu.node'
```

This blocked all frontend builds and caused the HTTP 500 on `localhost:8502`.

## Root Cause

`lightningcss-linux-x64-gnu` was explicitly listed as a **direct dependency** in `package-lock.json`. On the Windows x64 platform, `lightningcss/node/index.js` loads the platform binary via:

```js
try {
  module.exports = require(`lightningcss-${parts.join('-')}`);   // e.g. lightningcss-win32-x64-msvc
} catch (err) {
  module.exports = require(`../lightningcss.${parts.join('-')}.node`);  // fallback — fails on wrong platform
}
```

Because `lightningcss-linux-x64-gnu` was pinned in the lock file, npm resolved it as a required package. The fallback path `../lightningcss.linux-x64-gnu.node` does not exist on Windows → **crash**.

The platform-specific packages (`lightningcss-linux-x64-gnu`, `lightningcss-win32-x64-msvc`, etc.) are **optional dependencies** declared inside `lightningcss`'s own `package.json`. They must NOT be listed as direct dependencies — npm selects the correct one for the current platform at install time.

## Fix

| File | Change |
|------|--------|
| `frontend/package-lock.json` | Removed `lightningcss-linux-x64-gnu` and `lightningcss-win32-x64-msvc` from explicit direct-dep section; `lightningcss-win32-x64-msvc@1.31.1` now resolved correctly as optional dep of `@tailwindcss/node` |
| `frontend/next.config.ts` | Added `pdfjs-dist` webpack alias (`pdf.mjs` → `legacy/build/pdf.mjs`) for build compatibility |

## Verification

- `npm run build` → ✓ Compiled successfully in 12.7s, 27/27 static pages generated
- `npm run lint` → ✓ No ESLint warnings or errors
- `http://localhost:8503` → HTTP 200 (Playwright confirmed page renders, API-error boundary works correctly when backend is offline)

## Related

- SCP-20260226: Post-Audit Fix Sprint + UX Loading States
- `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260226-post-audit-fixes.md`
