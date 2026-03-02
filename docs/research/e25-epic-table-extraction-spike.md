---
epic: Epic 25
title: Table Extraction Research Spike — Comparative Analysis
status: in-progress
priority: P0
total_effort: 5 SP
s1_completed: 2026-02-27
s2_completed: 2026-02-27
depends_on: E24 (complete)
trigger: E24 validation proved content-core markdown serialization destroys TableFormer output (17/31 regression)
---

# Epic 25: Table Extraction Research Spike

## Goal

Run a controlled head-to-head comparison of table extraction methods on the Broadmeadows benchmark PDF, using Docling's Direct API to bypass content-core's broken serialization. Produce empirical evidence for the E26 architecture decision.

## Key Insight

E24 proved that **content-core's markdown serializer** is the bottleneck, not TableFormer itself. The Docling Direct API (`table.export_to_dataframe()`) bypasses this entirely, giving native Pandas DataFrames with perfect row/column structure. This is the single most important insight driving this spike.

## Stories

| Story | Title | Priority | Effort | Status | Phase |
|-------|-------|----------|--------|--------|-------|
| E25-S1 | Environment Setup & Dependency Audit | P0 | S (1 SP) | done | 1 |
| E25-S2 | Research Spike Execution | P0 | M (2 SP) | done | 2 |
| E25-S3 | Architecture Decision & E26 Design | P0 | M (2 SP) | backlog | 3 |

## Phase Dependencies

```
E25-S1 (Environment) ──→ E25-S2 (Spike Execution) ──→ E25-S3 (Architecture Decision)
         │                         │                            │
         ▼                         ▼                            ▼
  All 3 tools ready         Comparison report           ADR-001 D5 + E26 design
  Audit report written      Tables analyzed             Story breakdown for E26
```

## Success Criteria

After E25 completes:
1. Empirical evidence comparing PyMuPDF vs Docling Direct API (vs MinerU if available)
2. Clear recommendation for which approach gets closest to 31/31
3. Updated ADR-001 with D5 decision
4. E26 technical design document with implementation stories
5. Evidence of whether DataFrame extraction preserves "As Per" and "Not Sampled" rows

## Key Files

- Benchmark PDF: `docs/samplePDF/Clutch_Broadmeadows.pdf` (31 ground truth records)
- Ground truth: `docs/samplePDF/Clutch_Broadmeadows.csv`
- E24 failure report: `docs/reviews/e24-validation-results.md`
- E23 baseline: `docs/reviews/e23-validation-results.md` (28/31 with PyMuPDF)
- ADR to update: `docs/architecture/adr-tableformer-integration.md`

---

## E25-S1: Environment Setup & Dependency Audit

```yaml
epic: Epic 25
story_id: E25-S1
title: Environment Setup & Dependency Audit
status: done
priority: P0
effort: S (1 SP)
depends_on: none
agent: Mary (BA)
claude_commands:
  - /e25-preflight
  - /e25-setup-docling
  - /e25-setup-mineru (optional)
  - /e25-verify-all
```

**As a** researcher,
**I want** all extraction tools verified and ready on my local Windows + NVIDIA environment,
**So that** I can run the research spike comparison in the next session without setup delays.

### Acceptance Criteria

- [x] Pre-flight audit completed (Python, torch, CUDA, PyMuPDF verified)
- [x] Docling Direct API importable (`from docling.document_converter import DocumentConverter`)
- [x] TableFormer ACCURATE mode accessible (`TableFormerMode.ACCURATE`)
- [x] TableFormer model weights pre-downloaded (~500MB cached, loads in <1s)
- [x] Docling functional test passes: 8 tables from Broadmeadows in 14.9s
- [x] `table.export_to_dataframe(doc=doc)` returns valid Pandas DataFrame (67 rows total)
- [x] pandas 2.3.3 + tabulate 0.9.0 installed for DataFrame export
- [x] MinerU decision documented: SKIPPED (Docling Direct API strong enough for 2-way comparison)
- [x] N/A — MinerU skipped, no torch/paddle conflict to resolve
- [x] Environment audit report written: `docs/research/e25-environment-audit.md`
- [x] Verification script committed: `scripts/research/e25_verify_tools.py`

### Technical Notes

**Critical path**: Docling Direct API must be importable SEPARATELY from content-core. content-core wraps Docling but serializes tables poorly. We need the raw `DocumentConverter` class.

**Package relationships**:
```
content-core ──→ docling (wraps it, serializes poorly)
                    │
                    └──→ Docling Direct API (what we want — bypasses content-core)
                           ├── DocumentConverter
                           ├── table.export_to_dataframe()
                           ├── table.export_to_html()
                           └── TableFormerMode.ACCURATE
```

**Windows-specific notes**:
- Python runs directly on Windows (not Docker)
- Use PowerShell or WSL for commands
- Forward slashes work in Python even on Windows
- `uv pip install --break-system-packages` may be needed

### Claude Code Workflow

```
Session 1: Run these commands in sequence:
1. /e25-preflight          → Captures baseline, identifies gaps
2. /e25-setup-docling      → Installs Docling, downloads models, functional test
3. /e25-setup-mineru       → (OPTIONAL) If Demi decides to include MinerU
4. /e25-verify-all         → Final verification, generates audit report, commits
```

### Output Artifacts

| Artifact | Path |
|----------|------|
| Environment audit report | `docs/research/e25-environment-audit.md` |
| Verification script | `scripts/research/e25_verify_tools.py` |
| Setup plan (reference) | `docs/research/e25-environment-setup-plan.md` |

---

## E25-S2: Research Spike Execution (NEXT SESSION)

```yaml
epic: Epic 25
story_id: E25-S2
title: Research Spike Execution
status: done
priority: P0
effort: M (2 SP)
depends_on: E25-S1
agent: Amelia (Developer)
completed: 2026-02-27
```

**As a** researcher,
**I want** a head-to-head comparison of extraction methods on the Broadmeadows PDF,
**So that** I have empirical evidence for choosing the best table extraction approach.

### Acceptance Criteria

- [x] Research spike script created: `scripts/research/e25_table_comparison.py`
- [x] PyMuPDF baseline captured (text-only, page markers) — 0.09s, 34,369 chars
- [x] Docling Direct API results captured (DataFrames, HTML, markdown per table) — 22.41s, 8 tables
- [x] MinerU results: SKIPPED (2-way comparison)
- [x] Comparison report generated: `docs/reviews/e25-table-extraction-comparison.md`
- [x] Table-by-table quality analysis: 3 register tables, 30 rows, row coherence PRESERVED
- [x] ACM-specific validation: 9/9 "As Per", 4/6 "Not Sampled", 16/16 NATA — **29/31 (93.5%)**
- [x] Individual table outputs saved: `research-output/e25/{method}/table_*.{md,html,csv,json}`
- [x] Structured comparison JSON: `research-output/e25/comparison_summary.json`

### Key Results

- **Docling DataFrames: 29/31 (93.5%)** — beats E23 baseline of 28/31 (90.3%)
- **Record #9 (Switch Room / Battery Charger)**: FOUND in DataFrames — previously missed by LLM
- **Records #30, #31 (No Access)**: Still missing — on page 8, which Docling doesn't detect as a table
- **Row coherence**: PRESERVED — each DataFrame row = one complete ACM register entry
- **Recommendation**: Approach A (Hybrid PyMuPDF + Docling Direct API)

### CRITICAL: This is READ-ONLY Research

- Do NOT modify `source.full_text`
- Do NOT trigger extraction pipelines
- Do NOT use API budget (no LLM calls)
- This is LOCAL-ONLY — reads PDF, outputs comparison data

---

## E25-S3: Architecture Decision & E26 Design (AFTER SPIKE)

```yaml
epic: Epic 25
story_id: E25-S3
title: Post-Spike Architecture Decision
status: backlog
priority: P0
effort: M (2 SP)
depends_on: E25-S2
agent: Winston (Architect)
```

**As an** architect,
**I want** the ADR updated with the winning approach and an E26 technical design,
**So that** implementation can begin with a clear blueprint.

### Acceptance Criteria

- [ ] ADR-001 updated with D5 decision (winning extraction approach)
- [ ] E26 technical design created: `docs/architecture/e26-table-extraction-technical-design.md`
- [ ] Story breakdown for E26 implementation
- [ ] Decision rationale backed by empirical spike data
- [ ] Risk assessment for chosen approach
