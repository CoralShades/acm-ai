# MCS Post-Validation Fix Index — Pipeline Persistence & Real-Time UX
# Generated from MCS7 validation session (2026-03-19) + Pipeline Audit

**Total SP: 22 | 6 prompt packs | Execution order matters**

## Background

MCS7 validation (commit fa1ff9a4) ran 4 PDFs across 3 consultant formats using Ollama llama3.1:8b. The extraction logic works perfectly — 246 records extracted and persisted. However, a pipeline persistence timing audit revealed **6 gaps** that prevent the frontend from showing real-time extraction progress.

## Dependency Graph

```
MCS8 (P0, SP:5) ── Ghost save fix (base.py + checkpointer)
  │
  ├──► MCS11 (P1, SP:3) ── Restore building_record_id FK
  │
  ├──► MCS13 (P1, SP:3) ── Fix schema inference DocumentMeta bug
  │
  └──► MCS9 (P0, SP:5) ── Add SSE events to save node
        │
        ├──► MCS10 (P1, SP:3) ── Fix building/items query invalidation timing
        │
        └──► MCS12 (P2, SP:3) ── Wire extraction.* events to main pipeline
```

## Execution Order

| # | Pack | SP | Priority | What It Fixes |
|---|------|----|----------|--------------|
| 1 | **MCS8** | 5 | P0 | Ghost save in base.py, re-enable LangGraph checkpointer |
| 2 | **MCS9** | 5 | P0 | Add SSE events to save node, fix terminal event race |
| 3 | **MCS10** | 3 | P1 | Fix building query invalidation + items query timing |
| 4 | **MCS11** | 3 | P1 | Restore building_record_id FK (remove NULL workaround) |
| 5 | **MCS13** | 3 | P1 | Fix schema inference DocumentMeta bug + cache verification | **DONE** (2026-03-20) |
| 6 | **MCS12** | 3 | P2 | Wire extraction.* events to dead SSE endpoint |

## Files

| Pack | Prompt File |
|------|------------|
| MCS8 | `docs/sprint-artifacts/prompt-packs/2026-03-19-mcs8-fix-ghost-save-base-py.md` |
| MCS9 | `docs/sprint-artifacts/prompt-packs/2026-03-19-mcs9-sse-save-events-realtime.md` |
| MCS10 | `docs/sprint-artifacts/prompt-packs/2026-03-19-mcs10-building-query-invalidation.md` |
| MCS11 | `docs/sprint-artifacts/prompt-packs/2026-03-19-mcs11-building-record-id-fk-fix.md` |
| MCS12 | `docs/sprint-artifacts/prompt-packs/2026-03-19-mcs12-extraction-events-dead-endpoint.md` |
| MCS13 | `docs/sprint-artifacts/prompt-packs/2026-03-19-mcs13-schema-inference-documentmeta-fix.md` |

## Skills Required Across All Packs

| Skill | Used In |
|-------|---------|
| /systematic-debugging | MCS8, MCS11, MCS13 |
| /langgraph-fundamentals | MCS8, MCS9, MCS12 |
| /langgraph-persistence | MCS8 |
| /frontend-design | MCS9, MCS10, MCS12 |
| /ui-ux-pro-max | MCS9, MCS10, MCS12 |
| /uncodixfy | MCS9, MCS10, MCS12 |
| /sse-streaming | MCS9, MCS12 |
| /react-best-practices | MCS10 |
| /planning-with-files | All |
| /e2e-test | All |
| /acm-observability | All |
| /verification-before-completion | All |
| /test-driven-development | MCS8, MCS11, MCS13 |

## Agent Teams per Pack

Every pack requires a minimum team of 3 opus agents:

| Pack | Team Name | Agents |
|------|-----------|--------|
| MCS8 | `mcs8-ghost-save` | debugger, graph-fixer, validator |
| MCS9 | `mcs9-sse-save` | backend-events, frontend-ux, e2e-verifier |
| MCS10 | `mcs10-building-timing` | hook-fixer, ui-builder, e2e-tester |
| MCS11 | `mcs11-fk-fix` | backend-fixer, frontend-verifier, test-writer |
| MCS12 | `mcs12-extraction-events` | backend-events, frontend-status, verifier |
| MCS13 | `mcs13-schema-inference` | inference-fixer, cache-tester, verifier |

## Reference: Last 13 Commits

```
fa1ff9a4 test(extraction): validate multi-consultant format support with 3+ PDF formats
80267917 feat(ux): add HITL column mapping confirmation UI
cd5f919b feat(prompts): make extraction prompts format-agnostic
6ab5abb3 refactor(extraction): make row segmenter and recovery format-adaptive
881f04f1 feat(extraction): add consultant format profile registry
167f0c43 feat: add schema inference node for multi-consultant format adaptability
35abe382 refactor(detectors): rename detectors by structure not consultant
3157249f docs(prompt-packs): add 7 multi-consultant story prompt packs
5d560d06 feat(ux): Live extraction UX with SSE streaming, job lifecycle
e7223a87 docs(architecture): design multi-consultant PDF format adaptability
0febe5f9 refactor: complete SAMP→ARA terminology rename
513790dd refactor: rename SAMP→ARA terminology across codebase
4e555555 Refactor code structure for improved readability
```

## Reference: MCS7 Validation Results

| Source | Format | Records | Target | Status |
|--------|--------|---------|--------|--------|
| Broadmeadows | Standard DET | 32 | 31 | PASS |
| Alexander | ARA/Prensa | 95 | ≥36 | PASS |
| Clutch_Alexander | Clutch/Greencap | 90 | N/A | PASS |
| Clutch_BM_2 | Clutch/Greencap | 29 | N/A | PASS |

Total: 246 records, 17 buildings, 100% Ollama llama3.1:8b
