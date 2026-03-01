# E29 Gate 2 Recovery — SM Findings

## Status Drift Detected

### sprint-status.yaml vs story files vs reality

| Story | sprint-status.yaml | Story file | Actual state | PM guidance |
|-------|-------------------|------------|--------------|-------------|
| S3 | `ready-for-dev` | `drafted` | Code complete, merged, Gate 2 evaluated | `done` per PM sign-off |
| S4 | `drafted` | `review` | Code complete, merged, Gate 2 evaluated | `done` per PM sign-off |
| S5-S8 | `drafted` | `drafted` | Blocked by Gate 2 FAIL | `drafted` + blocked note |

### Key discrepancy — SM recommendation

PM (John) explicitly stated in e29-gate-decisions.md Gate 2 PM Sign-Off:
> "S3: Code complete and merged. Status should be `done`."
> "S4: Code complete and merged. Status should be `done`."
> "S3's AC-6/AC-7 benchmark thresholds are evaluated at Gate 2, which is a gate-level concern not a story-level defect."

User request asks S3/S4 → `review`. PM says → `done`. **SM recommendation**: follow PM guidance, set to `done` with a gate-2-fail annotation note. Rationale: all story-level ACs (AC-1 through AC-5 for S3, AC-1 through AC-6 for S4) are verified by QA. The benchmark thresholds (AC-6/AC-7 on S3, AC-7/AC-8 on S4) are gate-level criteria per PM decision.

## e29-story-specs.md Gate Table

Currently shows Gate 1 and Gate 2 as `PENDING` — needs update to `PASS` and `FAIL` respectively.

## Gate 2 Root Causes (from gate-decisions.md)

1. **No Docling tables in benchmark DB** — F2 fallback fired for all buildings (G2.3 untestable)
2. **LLM inventory compilation typing bug** — rooms as strings instead of `RoomMeta` objects
3. **Matching algorithm strictness** — normalization differences cause false-negative matches

## Recovery Stories (PM-authorized)

- **E29-R1** (2 SP): Benchmark fidelity — seed Docling tables, improve matching normalization, pin baselines
- **E29-R2** (2 SP): Match-gap remediation — fix RoomMeta typing, normalize room/location names

Execution order: R1 → R2 (R2 depends on R1 for accurate measurement).

## Pre-existing Test Failures (not from S3/S4)

- 7x graph wiring tests (invalidated by S3 unconditional edge — scheduled for S7 cleanup)
- 4x `test_field_config_api` (unrelated API/DB)
- 1x `test_source_commands_docling` (E27-S2 RecordID issue)
- 1x `test_building_inventory` (graph state change)
