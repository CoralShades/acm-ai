# E25 Plan Artifacts — How to Use

## Quick Start

**Option 1: Single prompt (fastest)**
Copy `docs/sprint-artifacts/e25-prompt1-mary-environment-setup.md` and paste it directly into Claude Code. It contains the complete environment setup workflow in one go.

**Option 2: Slash commands (interactive)**
Copy the `.claude/commands/e25-*.md` files into your project's `.claude/commands/` directory, then run them in sequence:
```
/e25-preflight       → Audit current state (read-only)
/e25-setup-docling   → Install Docling Direct API + TableFormer weights
/e25-setup-mineru    → (OPTIONAL) Install paddle + MinerU
/e25-verify-all      → Final verification + audit report
```

**Option 3: Reference docs**
Use `docs/research/e25-environment-setup-plan.md` as the master reference and run commands manually.

## File Map

```
e25-plan/
├── .claude/commands/
│   ├── e25-preflight.md           ← Slash command: audit current env
│   ├── e25-setup-docling.md       ← Slash command: install Docling Direct API
│   ├── e25-setup-mineru.md        ← Slash command: install MinerU (optional)
│   └── e25-verify-all.md          ← Slash command: final verification
├── docs/
│   ├── research/
│   │   └── e25-environment-setup-plan.md  ← Master plan document
│   └── sprint-artifacts/
│       ├── e25-epic-table-extraction-spike.md  ← BMAD epic + 3 stories
│       └── e25-prompt1-mary-environment-setup.md  ← Standalone Claude Code prompt
└── README.md                      ← This file
```

## Installation

Copy these files into your ACM-AI project:

```powershell
# From the downloaded e25-plan folder:
Copy-Item -Recurse ".claude\commands\e25-*.md" "C:\path\to\acm-ai\.claude\commands\"
Copy-Item -Recurse "docs\research\*" "C:\path\to\acm-ai\docs\research\"
Copy-Item -Recurse "docs\sprint-artifacts\e25-*" "C:\path\to\acm-ai\docs\sprint-artifacts\"
```

## What Each Artifact Does

| Artifact | Format | Purpose |
|----------|--------|---------|
| `e25-environment-setup-plan.md` | Reference doc | Complete technical plan — sections 1-8 covering problem, approaches, setup steps, success criteria |
| `e25-preflight.md` | Claude Code command | Read-only audit: Python, GPU, packages, Broadmeadows PDF |
| `e25-setup-docling.md` | Claude Code command | Install Docling Direct API, download TableFormer weights, run functional test |
| `e25-setup-mineru.md` | Claude Code command | OPTIONAL: Install paddlepaddle-gpu + upgrade magic-pdf |
| `e25-verify-all.md` | Claude Code command | Full verification script, generate audit report, commit |
| `e25-epic-table-extraction-spike.md` | BMAD artifact | Epic definition with 3 stories (S1: setup, S2: spike, S3: architecture) |
| `e25-prompt1-mary-environment-setup.md` | Standalone prompt | Complete Phase 1 workflow — paste into Claude Code for one-shot execution |

## Session Plan

| Session | What | Commands | Output |
|---------|------|----------|--------|
| **1 (NOW)** | Environment setup | `/e25-preflight` → `/e25-setup-docling` → `/e25-verify-all` | `docs/research/e25-environment-audit.md` |
| **2 (NEXT)** | Research spike | Prompt 2 (Amelia) — not included yet | `docs/reviews/e25-table-extraction-comparison.md` |
| **3 (AFTER)** | Architecture decision | Prompt 3 (Winston) — not included yet | Updated ADR-001 + E26 tech design |
