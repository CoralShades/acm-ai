---
epic: Epic 25
title: Table Extraction Research Spike — Comparative Analysis
status: in-progress
priority: P0
total_effort: 5 SP
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
| E25-S1 | Environment Setup & Dependency Audit | P0 | S (1 SP) | in-progress | 1 |
| E25-S2 | Research Spike Execution | P0 | M (2 SP) | backlog | 2 |
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
status: in-progress
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
- [ ] Docling Direct API importable (`from docling.document_converter import DocumentConverter`)
- [ ] TableFormer ACCURATE mode accessible (`TableFormerMode.ACCURATE`)
- [ ] TableFormer model weights pre-downloaded (~500MB cached)
- [ ] Docling functional test passes: `converter.convert()` produces tables from Broadmeadows PDF
- [ ] `table.export_to_dataframe(doc=doc)` returns valid Pandas DataFrame
- [ ] pandas + tabulate installed for DataFrame export
- [ ] MinerU decision documented (install or skip, with rationale)
- [ ] If MinerU installed: torch/paddle conflict resolved
- [ ] Environment audit report written: `docs/research/e25-environment-audit.md`
- [ ] Verification script committed: `scripts/research/e25_verify_tools.py`

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
status: backlog
priority: P0
effort: M (2 SP)
depends_on: E25-S1
agent: Amelia (Developer)
```

**As a** researcher,
**I want** a head-to-head comparison of extraction methods on the Broadmeadows PDF,
**So that** I have empirical evidence for choosing the best table extraction approach.

### Acceptance Criteria

- [ ] Research spike script created: `scripts/research/e25_table_comparison.py`
- [ ] PyMuPDF baseline captured (text-only, page markers)
- [ ] Docling Direct API results captured (DataFrames, HTML, markdown per table)
- [ ] MinerU results captured (if available — HTML tables)
- [ ] Comparison report generated: `docs/reviews/e25-table-extraction-comparison.md`
- [ ] Table-by-table quality analysis (rows, columns, coherence, merged cells)
- [ ] ACM-specific validation: "As Per" rows, "Not Sampled" rows, NATA numbers
- [ ] Individual table outputs saved: `research-output/e25/{method}/table_*.{md,html,csv}`
- [ ] Structured comparison JSON: `research-output/e25/comparison_report.json`

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
