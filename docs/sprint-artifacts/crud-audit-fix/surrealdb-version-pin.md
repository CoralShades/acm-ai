# SurrealDB Version Pin — Compatibility Fix

## Problem

`docker-compose.yml` used `surrealdb/surrealdb:v2` with `pull_policy: always`.
The `v2` rolling tag advanced to **v2.6.3**, which introduces CBOR serialization
revision 157. The Python SDK `surrealdb==1.0.8` (latest as of 2026-03-16) cannot
deserialize that revision and raises:

```
Versioned error: A deserialization error occured: Invalid revision 157 for type Value
```

### Observed symptoms

| Table | Symptom |
|-------|---------|
| `source` (7 records) | Completely unreadable — every SELECT fails |
| `acm_record` (1224 records) | Intermittent failures at specific row offsets; individual field queries work |
| `model` (17 records) | Unaffected |

The error is **server-side** — it appears even on the SurrealDB HTTP/JSON endpoint,
meaning it is not a protocol-level fix.

## Fix Applied

Pinned the image in `docker-compose.yml`:

```yaml
image: surrealdb/surrealdb:v2.2.1
pull_policy: missing
```

`v2.2.1` is the last known SurrealDB release compatible with `surrealdb==1.0.8`.
`pull_policy: missing` prevents Docker from silently pulling a newer image on
`docker compose up`.

## Data Migration — Manual Steps Required

**CRITICAL: Do NOT recreate the Docker container before reading this section.**

The named volume `acm-ai-surreal-data` holds data written by v2.6.3. Downgrading
the container image while keeping that volume may cause v2.2.1 to reject or
corrupt the on-disk format.

### Option A — Export before downgrade (recommended)

1. While the v2.6.3 container is still running, export all readable data:

   ```bash
   # Export each working table via the HTTP endpoint
   curl -s -u root:root \
     -H "Accept: application/json" \
     -H "NS: open_notebook" -H "DB: development" \
     http://localhost:8000/sql \
     --data "SELECT * FROM model;" > export_model.json

   # Repeat for any other tables that are readable
   ```

2. Stop the container:

   ```bash
   docker compose stop surrealdb
   ```

3. Delete the corrupted volume:

   ```bash
   docker volume rm acm-ai-surreal-data
   ```

4. Start the container with the pinned v2.2.1 image (config already updated):

   ```bash
   docker compose up -d surrealdb
   ```

5. Re-import exported data and re-run the ACM extraction pipeline to regenerate
   `acm_record` rows from source documents.

### Option B — Fresh start (if export is not feasible)

1. Stop the container and remove the volume:

   ```bash
   docker compose stop surrealdb
   docker volume rm acm-ai-surreal-data
   ```

2. Start fresh with the pinned image:

   ```bash
   docker compose up -d surrealdb
   ```

3. Run migrations:

   ```bash
   uv run run_api.py   # migrations execute automatically on API start
   ```

4. Re-upload source PDFs and re-run extraction jobs.

## Preventing Future Upgrades

- The image is now pinned to `v2.2.1` — never change this without first verifying
  SDK compatibility.
- To upgrade SurrealDB in future, update the Python SDK first, confirm it handles
  the new CBOR revision, then update the image tag.
- Do not revert `pull_policy` to `always`.
