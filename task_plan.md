# Task Plan — E29: Pipeline Unification Story Specs (S1-S8)

## Objective
Convert Epic 29 into 8 execution-ready story specs with user stories, ACs, tasks, dependencies, test strategy, and touched files.

## Phases

### Phase 1: Research & Analysis
- [x] Read reconciled YAML (V3/epic-29-pipeline-unification.reconciled.yaml)
- [x] Read execution contract (V3/epic-29-execution-contract.md)
- [x] Read architecture delta (docs/architecture/e29-architecture-delta.md)
- [ ] Verify codebase state for referenced files
- [ ] Cross-reference gaps and identify ambiguities

### Phase 2: Story Spec Generation
- [x] E29-S1: JSON Parser Resilience
- [x] E29-S2: Benchmark Harness + Baseline Capture
- [x] E29-S3: Unified Orchestrator Path
- [x] E29-S4: Capability Registry + Fallback Contract
- [x] E29-S5: Agent Decomposition I (Table Parser + BAR Mapper)
- [x] E29-S6: Agent Decomposition II (Enricher/Classifier/Validator)
- [x] E29-S7: Dual-Benchmark Validation + Legacy Cleanup
- [x] E29-S8: Export Hardening + Integration Tests + Doc Alignment

### Phase 3: Cross-Cutting Outputs
- [x] Go/No-Go checklist per decision gate (4 gate checklists)
- [x] Parallelization opportunities (confirmed: S1||S2, within-story parallelism)
- [x] Quality rules compliance review

## Output
- File: `docs/sprint-artifacts/e29-story-specs.md`
- Format: Markdown, one section per story (S1-S8)

## Quality Rules
- Every story has measurable acceptance checks
- Cleanup stories (S7) reference gate criteria explicitly
- Validation stories call out Broadmeadows and Alexander targets
- Benchmark stories include repeatable command entrypoints
