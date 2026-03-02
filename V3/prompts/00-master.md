# ACM-AI V3 Prompt Pack — Master Index

> **Created:** 2026-03-02
> **Scope:** Full V3 course correction — Salesforce alignment + multi-provider extraction + new UI + SSE streaming
> **Branch:** ACMV3
> **Status:** Ready for execution

---

## Decision Summary (from planning session)

| Decision | Choice |
|----------|--------|
| E29/E30 | Archive E29 S5-S8 + E30 SCP. E29 S1-S4 retained. Fresh V3 epics. |
| Extraction Providers | Design for 3 (Docling + Google Doc AI + PaddleOCR), implement 2 now |
| SF Alignment | Approved — carry forward from E30 SCP + multi-agent audit |
| AI Model Strategy | Debate in Party Mode — no pre-decided lock-in |
| Provenance | Full extraction lineage (page, bbox, provider, model, confidence, edit history) |
| New Requirements | Multi-provider consensus, raw table editor, wizard UI, AI batching, SSE streaming |
| SF Field Data | Use summaries only (V3/output/*_fields_summary.md) |
| HTML Docs | Extract to markdown first (P0 pre-step) |
| Context7 MCP | Tech research + dev prompts only |

---

## V3 Input Documents

### Approved Requirements (carry forward)
- `V3/SCP-20260301-SF-salesforce-alignment.md` — Salesforce schema alignment proposal
- `V3/output/e30-multi-agent-audit-unified.md` — Multi-agent audit findings
- `V3/output/item_fields_summary.md` — SF Item__c field reference (154 fields)
- `V3/output/building_fields_summary.md` — SF Building__c field reference (143 fields)

### Architecture & Analysis (extract to markdown via P0)
- `V3/acm-ai-solution-architecture-v3.html` — Client solution architecture
- `V3/heuristic-rules-reference.html` — Extraction heuristic rules
- `V3/bmad-architecture-audit.html` — Architecture audit findings

### Current Planning Artifacts
- `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` — Current PRD
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` — Current architecture
- `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` — Current epics
- `docs/sprint-artifacts/sprint-status.yaml` — Sprint tracking
- `docs/architecture/e29-architecture-delta.md` — E29 architecture delta

### Raw SF Data (for Schema Config Loader implementation only)
- `V3/building-list.txt` (179KB) — Raw Building__c field definitions
- `V3/item-list.txt` (205KB) — Raw Item__c field definitions

---

## Execution Sequence

```
P0: Extract HTML to Markdown (pre-step)
 |
 ├── 01: Correct Course (archive E29/E30)
 |        can run in parallel ↕
 ├── 02: Technical Research (Google Doc AI + PaddleOCR)
 |
 v
03: Party Mode (V3 multi-agent planning) ← needs 01 + 02 outputs
 |
 v
04: Edit PRD ← needs Party Mode output
 |
 v
05: Create Architecture ← needs updated PRD
 |     can run in parallel ↕
06: Create UX Design ← needs updated PRD
 |
 v
07: Create Epics & Stories ← needs architecture + UX
 |
 v
08: Check Implementation Readiness ← gate check
 |
 v
08b: Readiness Fixes ← resolve CONDITIONAL GO issues (if any)
 |
 v
09: Sprint Planning ← needs approved readiness
 |
 v
[IMPLEMENTATION CYCLE — repeat per story]
10: Create Story → 11: Dev Story → 12: QA Automation → 13: Code Review
 |
 v
14: Tech Writer Doc Update (after story completion)
 |
 v
15: Retrospective (after epic completion)
```

### Parallel Opportunities
- **P0 + 01 + 02** can all start immediately
- **05 + 06** can run in parallel after PRD is updated
- **10-13** repeat for each story in the sprint plan

---

## Prompt Files

### Pre-Steps
| # | File | BMAD Command | Agent | Purpose |
|---|------|-------------|-------|---------|
| P0 | [P0-extract-html.md](./P0-extract-html.md) | (manual) | Any | Convert V3 HTML docs to markdown |

### Planning Phase (Phase 2-3)
| # | File | BMAD Command | Agent | Purpose |
|---|------|-------------|-------|---------|
| 01 | [01-correct-course.md](./01-correct-course.md) | `/bmad-bmm-correct-course` | Bob (SM) | Archive E29/E30, document V3 course correction |
| 02 | [02-tech-research.md](./02-tech-research.md) | `/bmad-bmm-technical-research` | Mary (BA) | Evaluate Google Doc AI + PaddleOCR |
| 03 | [03-party-mode.md](./03-party-mode.md) | `/bmad-party-mode` | All Agents | V3 multi-agent planning session |
| 04 | [04-edit-prd.md](./04-edit-prd.md) | `/bmad-bmm-edit-prd` | John (PM) | Update PRD with V3 requirements |
| 05 | [05-create-architecture.md](./05-create-architecture.md) | `/bmad-bmm-create-architecture` | Winston (Arch) | V3 architecture document |
| 06 | [06-create-ux.md](./06-create-ux.md) | `/bmad-bmm-create-ux-design` | Sally (UX) | UI/UX for wizard, raw tables, provenance |
| 07 | [07-create-epics.md](./07-create-epics.md) | `/bmad-bmm-create-epics-and-stories` | John (PM) | V3 epic structure |
| 08 | [08-readiness-check.md](./08-readiness-check.md) | `/bmad-bmm-check-implementation-readiness` | Winston (Arch) | Gate: all artifacts aligned |
| 08b | [08b-readiness-fixes.md](./08b-readiness-fixes.md) | (direct edits) | Any | Resolve CONDITIONAL GO issues |

### Implementation Phase (Phase 4)
| # | File | BMAD Command | Agent | Purpose |
|---|------|-------------|-------|---------|
| 09 | [09-sprint-planning.md](./09-sprint-planning.md) | `/bmad-bmm-sprint-planning` | Bob (SM) | Generate sprint plan |
| 10 | [10-create-story.md](./10-create-story.md) | `/bmad-bmm-create-story` | Bob (SM) | Story creation (reusable template) |
| 11 | [11-dev-story.md](./11-dev-story.md) | `/bmad-bmm-dev-story` | Amelia (Dev) | Story implementation (reusable template) |
| 12 | [12-qa-automation.md](./12-qa-automation.md) | `/bmad-bmm-qa-automate` | Quinn (QA) | Test generation (reusable template) |
| 13 | [13-code-review.md](./13-code-review.md) | `/bmad-bmm-code-review` | Amelia (Dev) | Code review (reusable template) |

### Post-Implementation
| # | File | BMAD Command | Agent | Purpose |
|---|------|-------------|-------|---------|
| 14 | [14-doc-update.md](./14-doc-update.md) | (agent-based) | Paige (Writer) | Documentation updates |
| 15 | [15-retrospective.md](./15-retrospective.md) | `/bmad-bmm-retrospective` | Bob (SM) | Epic retrospective |

---

## How to Use

1. **Open a fresh Claude Code context window** for each prompt
2. **Copy the prompt text** from the individual file
3. **Run the BMAD command first** (e.g., type `/bmad-bmm-correct-course`)
4. **Paste the prompt context** when the agent asks for input or after the workflow loads
5. **Save outputs** to the location specified in each prompt
6. **Feed outputs forward** — each step's output is input for subsequent steps

### Important Notes
- Always run in a **fresh context window** — prevents context pollution between steps
- For **validation workflows** (08-readiness-check): use a different LLM if available
- **Context7 MCP** is available for library documentation lookups in tech research + dev prompts
- **Chrome DevTools MCP** is available for UI verification in dev stories
- Prompts reference files with `{project-root}/` prefix — this resolves to the repo root
