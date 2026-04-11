You are the FRONTEND-BROWSER-TESTER specialist added to the Phase 5 audit. READ-ONLY review via browser automation. No code changes.

Working directory: `/mnt/d/ailocal/acm-ai`. Branch `feat/sf-reconciliation-20260411`.

## Context to read first

1. `docs/cleanup/assumptions-and-decisions.md`
2. `docs/cleanup/session-log-2026-04-11.md`
3. `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md`
4. Invoke the `/agent-browser` skill for CLI reference (open, snapshot -i, click @ref, fill @ref "text")

## Running state

- Frontend: `http://127.0.0.1:8502` OR `http://127.0.0.1:8503` — started in background this turn (first attempt used port 8502, second used 8503 because package.json script `next dev -p 8503` is hardcoded and protected). Check BOTH ports.
- API: `http://127.0.0.1:5055` — also booting this turn at `logs/phase5-api-boot.log` (loads many commands/graphs, may take 60-120s to bind).
- SurrealDB: `ws://127.0.0.1:8000/rpc` — up, has data.

## First step — find the frontend port

Before any browser work:
```bash
FRONTEND_URL=""
for i in $(seq 1 45); do
  if curl -sS -m 2 http://127.0.0.1:8502/ > /dev/null 2>&1; then
    FRONTEND_URL="http://127.0.0.1:8502"
    echo "Frontend ready at 8502 after ${i} checks"
    break
  fi
  if curl -sS -m 2 http://127.0.0.1:8503/ > /dev/null 2>&1; then
    FRONTEND_URL="http://127.0.0.1:8503"
    echo "Frontend ready at 8503 after ${i} checks"
    break
  fi
  sleep 2
done

if [[ -z "$FRONTEND_URL" ]]; then
  echo "Frontend never bound — check logs/phase5-frontend-boot.log and phase5-frontend-boot2.log"
  # Fall through to static code review
fi
```

If after ~90 seconds the frontend is still not responding, STOP browser work and do pure code-only review of `frontend/src/app/(dashboard)/jobs/[id]/page.tsx`, `frontend/src/components/acm/BuildingGrid.tsx`, `ACMGrid.tsx`, `BuildingViewDialog.tsx`. Report the frontend failure clearly.

## Your mission — browser verification

Use the `agent-browser` CLI. Core workflow: `agent-browser open <url>`, then `agent-browser snapshot -i` to get interactive refs (@e1, @e2), then `agent-browser click @e1` / `agent-browser fill @e2 "text"` to interact. Re-snapshot after each navigation.

1. **Frontend boot test**: `agent-browser open http://localhost:8502` → snapshot. Does the landing page load? Any red errors in the DOM?

2. **Jobs page (/jobs)** — the primary dashboard:
   ```
   agent-browser open http://localhost:8502/jobs
   agent-browser snapshot -i
   ```
   Does it render? Are there job cards? Or empty state? Capture the top-level DOM structure.

3. **Job detail (/jobs/[id])** — primary detail view. If jobs exist, click into the first one and snapshot. Check for the tabs: Overview, Buildings, ACM Records, Content, Raw Tables, Log. Capture which tabs render and which error.

4. **ACM Records grid**: if it loads, inspect the AG Grid column headers. They should match the new SF field set from `config/sf-schema-snapshot.json`. Report any column header that references a fabricated SF field name.

5. **Fabricated field names in console errors**: Capture the browser console (via agent-browser if available, or page-text) for JS errors mentioning `Room_ID__c`, `ACM_Name__c`, `Extent__c`, `Risk_Status__c`, `Department__c`, `Agency__c`. These indicate stale references in frontend code.

6. **Chat panel**: Open chat, verify it renders (no crash). Don't send a message — just verify the UI doesn't error on mount.

7. **Screenshot of key pages** if the CLI supports it: save to `docs/cleanup/phase-5-screenshots/`.

## Output

1. Write findings to `docs/cleanup/phase-5-audit-frontend.md` with sections: Scope, Pages Visited, DOM Observations, Column Header Audit (AG Grid), Console Errors, Fabricated Field Hits, Screenshots (if any), Recommendations.
2. Print final ≤300-word summary starting with "=== FRONTEND SUMMARY ===". Include pass/fail for each of the 6 checks above.

If the frontend never boots, report it clearly and fall back to static code review of `frontend/src/components/acm/*` and `frontend/src/app/(dashboard)/jobs/[id]/page.tsx`. Do not claim "tested" for anything you couldn't actually interact with. Exit cleanly when done.
