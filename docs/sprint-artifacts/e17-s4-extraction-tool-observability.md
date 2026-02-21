# E17-S4: Extraction Tool Call Observability

## Story Info
- **Epic**: E17 — Live Extraction Intelligence
- **Status**: drafted
- **Priority**: P1
- **Size**: S (Small)
- **Created**: 2026-02-22
- **Dependencies**: E17-S1
- **Blocks**: None

## Description

Map LangGraph node executions to AG-UI ToolCallStart/Args/End/Result events and display as a live feed in the extraction progress panel.

## Acceptance Criteria

- [ ] Each graph node transition shows as a tool call entry
- [ ] In-flight calls show spinner + elapsed time
- [ ] Completed calls show check + result summary + duration
- [ ] Args displayed: chunk_index, page_range, model_id, content_length
- [ ] Results displayed: records_found, duration_ms

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/components/acm/ExtractionToolCallFeed.tsx` | CREATE | Live feed of active operations with spinner/check icons |
| `frontend/src/components/acm/ExtractionProgressPanel.tsx` | MODIFY | Add ExtractionToolCallFeed in "Active Operations" section |
