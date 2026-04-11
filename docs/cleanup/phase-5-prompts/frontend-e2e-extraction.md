You are the FRONTEND-E2E-EXTRACTION specialist in the Phase 5 audit. This is a LIVE end-to-end test — upload a real sample PDF, run extraction through the full stack, verify the output in the grid. Other agents are auditing in parallel; you report back to the parent session (the lead) when done.

Working directory: `/mnt/d/ailocal/acm-ai`. Branch `feat/sf-reconciliation-20260411`.

## Context to read first

1. `docs/cleanup/assumptions-and-decisions.md` — 20 durable decisions
2. `docs/cleanup/session-log-2026-04-11.md`
3. `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md`
4. `CLAUDE.md` — especially the `/jobs` and `/jobs/[id]` primary route rules
5. Invoke the `/agent-browser` skill for CLI reference (commands: `open`, `snapshot -i`, `click @ref`, `fill @ref "text"`, `screenshot`)
6. Invoke the `/acm-observability` skill for the observability tool stack

## Sample PDF to use

Primary target: `docs/samplePDF/Clutch_Broadmeadows.pdf` (1.8 MB, 31 expected records — the canonical Broadmeadows Police Station ARA report the project has been benchmarked against).

Ground-truth CSV for comparison: `docs/samplePDF/Clutch_Broadmeadows.csv` (41 columns, 31 rows — consultant's actual extraction).

## Live services

- SurrealDB: `ws://127.0.0.1:8000/rpc` — up, has data (root/root, namespace `open_notebook`, database `development`)
- API: `http://127.0.0.1:5055` — booting at `logs/phase5-api-boot.log`. May take 60-120 seconds to bind.
- Frontend: try `http://127.0.0.1:8502` and `http://127.0.0.1:8503`. The package.json script is hardcoded to `-p 8503`; a spawn attempt this turn tried 8502. Check both.

## First step — wait for readiness

```bash
# Wait up to 180s for API
API_READY=""
for i in $(seq 1 90); do
  if curl -sS -m 2 http://127.0.0.1:5055/health 2>&1 | grep -q -i "ok\|healthy\|status"; then
    API_READY="1"; echo "API ready after ${i} checks"; break
  fi
  sleep 2
done

# Wait up to 180s for frontend
FRONTEND_URL=""
for i in $(seq 1 90); do
  for port in 8502 8503; do
    if curl -sS -m 2 "http://127.0.0.1:$port/" 2>&1 | head -1 | grep -q -i "html\|doctype\|next"; then
      FRONTEND_URL="http://127.0.0.1:$port"
      echo "Frontend ready at $FRONTEND_URL after ${i} checks"; break 2
    fi
  done
  sleep 2
done
```

If API or frontend never come up after ~3 minutes, report the failure and fall back to API-only extraction via curl (skip the browser upload step).

## Your mission — E2E extraction run

### Phase A — Browser upload (preferred path)

1. `agent-browser open $FRONTEND_URL/jobs`
2. `agent-browser snapshot -i` — capture interactive element refs
3. Find the upload button / drag-drop zone via the snapshot. Click it.
4. Trigger file upload with `docs/samplePDF/Clutch_Broadmeadows.pdf`. If agent-browser supports file input, use it; otherwise fall back to direct API upload via curl:
   ```bash
   curl -sS -X POST http://127.0.0.1:5055/sources \
     -F "file=@docs/samplePDF/Clutch_Broadmeadows.pdf" \
     -F "type=upload" \
     -F "notebook_name=Phase5 E2E Broadmeadows Test"
   ```
5. Capture the returned source_id.
6. Watch the extraction run: `agent-browser open $FRONTEND_URL/jobs/{source_id}` → re-snapshot every 10s until the status reaches "Extracted" or "Failed", or 10 minutes pass.
7. While waiting, tail `logs/api.log` for the extraction pipeline stage progress (`stage_enter` / `stage_complete` events from PipelineEventBus).

### Phase B — Grid verification

Once extraction completes:

1. Navigate to `/jobs/{source_id}` → click "ACM Records" tab → snapshot
2. Read the AG Grid column headers. Compare them against `config/sf-schema-snapshot.json` → `objects.Item__c.extractable_fields` keys. Report any grid column that references a fabricated SF field name or is missing a real one.
3. Navigate to "Buildings" tab → snapshot. Same audit for `BUILDING_SF_MAPPING`.
4. Click "View" on the first Building row → snapshot the detail dialog. Verify the form shows only real SF fields.
5. Capture console errors (agent-browser `console` subcommand if available) — look for JS errors mentioning fabricated field names (`Room_ID__c`, `ACM_Name__c`, `Extent__c`, `Department__c`, `Agency__c`).

### Phase C — DB vs grid cross-check

Run SurrealDB queries to verify the DB actually got the extracted records:

```bash
docker exec acm-ai-db /surreal sql \
  --conn http://localhost:8000 \
  --user root --pass root \
  --ns open_notebook --db development \
  --pretty \
  -q "SELECT count() FROM acm_record WHERE source_id = type::thing('{source_id}') GROUP ALL"
```

Expected: 31 records (ground truth). Report the actual count and any validation errors.

### Phase D — SF export sanity

Call the SF export endpoint:
```bash
curl -sS "http://127.0.0.1:5055/api/acm/export/sf/building?source_id={source_id}" > /tmp/phase5-building-export.csv
curl -sS "http://127.0.0.1:5055/api/acm/export/sf/item?source_id={source_id}" > /tmp/phase5-item-export.csv
```

Parse each CSV header row. Every column name should match a real SF field per `config/sf-schema-snapshot.json`. Grep for `Department__c`, `Agency__c`, `Room_ID__c`, etc. — any hit is a failure.

## Output

1. Write findings to `docs/cleanup/phase-5-audit-frontend-e2e.md` with sections:
   - Service readiness (how long each took, whether any failed)
   - Upload result (source_id, upload method used)
   - Extraction timeline (stage events + elapsed time)
   - Record count (expected 31 / actual / validation errors)
   - Grid column header audit (headers vs snapshot)
   - Console errors (fabricated field hits)
   - CSV export header audit
   - Screenshots (save to `docs/cleanup/phase-5-screenshots/` if agent-browser supports it)
   - Verdict (PASS / PARTIAL / FAIL) with specific findings
2. Print final ≤400-word summary starting with "=== FRONTEND-E2E SUMMARY ===". Include: services_ready, upload_source_id, extracted_count, validation_errors, fabricated_field_hits, screenshots_count.

If anything blocks you beyond a reasonable fallback, say so clearly. Do not claim you tested something you couldn't actually interact with. The lead needs honest signal to drive E38 decisions.

Exit cleanly when done.
