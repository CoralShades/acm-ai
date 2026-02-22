# E17-S2: Incremental Record Streaming to AG Grid

## Story Info
- **Epic**: E17 — Live Extraction Intelligence
- **Status**: done
- **Priority**: P0
- **Size**: M (Medium)
- **Created**: 2026-02-22
- **Dependencies**: E17-S1
- **Blocks**: None

## Description

Stream extracted records incrementally to the AG Grid as each chunk is processed, instead of waiting for the full extraction to complete. Uses AG-UI StateDelta events with RFC 6902 JSON Patch format.

## Acceptance Criteria

- [ ] Records appear in AG Grid within 2s of each chunk being processed
- [ ] Preview records visually distinguished (italic/ghost styling)
- [ ] On completion, preview records replaced by final saved records
- [ ] Grid maintains scroll position during incremental updates
- [ ] Chunk progress counter visible (e.g., "Chunk 3/8")

## Dev Agent Record
- **Completed**: 2026-02-22
- **Build**: PASS (ruff, frontend build)
- **Files verified**: use-extraction-agent.ts, ACMGrid.tsx, ACMTab.tsx
- **Notes**: AG-UI StateDelta events with RFC 6902 JSON Patch streaming to AG Grid.

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/lib/hooks/use-extraction-agent.ts` | CREATE | useExtractionAgent hook connecting useCoAgent to extraction stream |
| `frontend/src/components/acm/PreviewRecordBadge.tsx` | CREATE | Visual indicator for preview/streaming records |
| `frontend/src/app/copilot/route.ts` | MODIFY | Add extraction agent alongside supervisor |
| `frontend/src/components/acm/ACMGrid.tsx` | MODIFY | Add previewRecords prop, merge with final records, preview styling |
| `frontend/src/components/acm/ACMTab.tsx` | MODIFY | Use useExtractionAgent alongside existing hooks |
| `frontend/src/lib/types/pipeline.ts` | MODIFY | Add ExtractionAgentState interface |
