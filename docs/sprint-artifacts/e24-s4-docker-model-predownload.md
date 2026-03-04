---
epic: Epic 24
story_id: E24-S4
title: Docker Model Weight Pre-Download
status: archived  # Superseded by E26 Docling Direct API. See ADR-001 D7.
priority: P1
effort: S (1 SP)
depends_on: E24-S1
---

As a DevOps engineer,
I want TableFormer model weights pre-downloaded during Docker image build,
So that containerized deployments work without requiring internet access at runtime.

## Acceptance Criteria

- [ ] `Dockerfile` includes a build step that pre-downloads TableFormer model weights
- [ ] Container startup does not require internet access for model download
- [ ] `docker-compose.yml` includes `DOCLING_TABLE_STRUCTURE=true` in API and worker service environment
- [ ] `docker-compose.yml` includes `DOCLING_TABLE_MODE=accurate` in API and worker service environment
- [ ] Health check endpoint (or startup log) confirms TableFormer model is available
- [ ] Docker image size increase documented (expected: ~500 MB for model weights)
- [ ] Build succeeds on CI with model weights cached

## Technical Notes

### Files to Modify

| File | Change |
|------|--------|
| `Dockerfile` | Add model pre-download RUN step |
| `docker-compose.yml` | Add `DOCLING_TABLE_STRUCTURE` and `DOCLING_TABLE_MODE` env vars to api/worker |

### Dockerfile Addition

```dockerfile
# Pre-download TableFormer model weights during build
# Cached in $HOME/.cache/docling/models/ (~500 MB)
RUN python -c "from docling.models import TableFormerModel; TableFormerModel()"
```

### Environment Strategy by Deployment

| Environment | Strategy |
|-------------|----------|
| Dev (local) | Auto-download on first `process_source` with flag enabled |
| Docker | Pre-download during image build (this story) |
| CI | Cache `$HOME/.cache/docling/` in CI artifact cache |
| Air-gapped | Pre-download and mount as Docker volume |

### docker-compose.yml Changes

Add to API and worker service `environment` sections:

```yaml
environment:
  DOCLING_TABLE_STRUCTURE: "${DOCLING_TABLE_STRUCTURE:-true}"
  DOCLING_TABLE_MODE: "${DOCLING_TABLE_MODE:-accurate}"
```

### Verification

After `docker compose build`:
1. `docker compose up -d api worker`
2. Process a PDF with TableFormer enabled
3. Confirm no model download occurs at runtime (check logs for download activity)
4. Confirm processing completes within expected time (~20-35s)

## Dependencies

- E24-S1 must be complete (TableFormer activation code must exist)

## References

- Technical Design Section 2B: `docs/architecture/tableformer-technical-design.md`
- ADR-001 "Model weight download fails" risk row

## Dev Notes

<!-- Implementation notes will be added by the dev agent -->
