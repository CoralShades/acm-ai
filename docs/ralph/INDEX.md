# Ralph + BMAD v6 Knowledge Base

> Authoritative, AI-agent-readable reference for the Ralph autonomous coding loop framework.
> Supersedes `docs/ralph-PLAYBOOK.md` and `docs/ralph-research/`.

## Decision Tree

```
Q1: First time with Ralph?
  → Yes → 00-quickstart.md

Q2: Setting up a new project?
  → Copy from templates/ → Read 01-concepts.md for vocabulary

Q3: Which execution mode?
  → External bash loop      → 03-bash-loop.md
  → Interactive commands     → 04-slash-commands.md
  → In-session (Wiggum)     → 05-in-session-wiggum.md
  → Compare all three       → 02-execution-modes.md

Q4: Configuring agents or models?
  → Agent definitions       → 09-agent-roster.md
  → Model selection          → 10-model-strategy.md
  → BMAD workflow            → 06-bmad-integration.md

Q5: Working with hooks or gates?
  → Hook reference           → 08-hooks.md
  → prd.json / gates         → 07-prd-and-gates.md

Q6: Something broken?
  → 12-troubleshooting.md

Q7: ACM-AI specific?
  → 13-acm-ai-reference.md
```

## File Manifest

| File | Purpose | Lines |
|------|---------|-------|
| `INDEX.md` | This file — master directory, always read first | ~100 |
| `00-quickstart.md` | Human 5-min setup + AI architecture overview | ~200 |
| `01-concepts.md` | Glossary, completion protocol, state-on-disk, exit codes | ~100 |
| `02-execution-modes.md` | 3 modes compared side-by-side | ~250 |
| `03-bash-loop.md` | Mode 1: Simple + full-featured bash loops | ~240 |
| `04-slash-commands.md` | Mode 2: All 10 slash commands reference | ~220 |
| `05-in-session-wiggum.md` | Mode 3: Stop hook in-session loop | ~190 |
| `06-bmad-integration.md` | BMAD v6 agent roster → Ralph phase mapping | ~380 |
| `07-prd-and-gates.md` | prd.json schema, dependency graph, gates | ~160 |
| `08-hooks.md` | All hook types, events, patterns, exit codes | ~220 |
| `09-agent-roster.md` | Agent definitions, spawning, teams, cost control | ~400 |
| `10-model-strategy.md` | haiku/sonnet/opus guide + Ollama + OAuth | ~310 |
| `11-mcp-patterns.md` | Context7, chrome-devtools, Playwright, custom | ~200 |
| `12-troubleshooting.md` | Platform failures, recovery, diagnostics | ~640 |
| `13-acm-ai-reference.md` | ACM-AI specific config, absorbed research | ~320 |
| `templates/README.md` | Template manifest + usage guide | ~80 |
| `templates/*.template` | 7 config/script/prompt templates | — |
| `templates/hooks/*.sh` | 5 copy-paste ready hook scripts | — |
| `templates/agents/*.template` | 4 agent definition templates | — |

**Total**: 16 docs + 17 templates = 33 files

## Tag Index

| Tag | Files |
|-----|-------|
| `#quickstart` | 00 |
| `#concepts` | 01 |
| `#bash-loop` | 02, 03 |
| `#slash-commands` | 02, 04 |
| `#wiggum` | 02, 05 |
| `#bmad` | 06 |
| `#gates` | 07 |
| `#hooks` | 08 |
| `#agents` | 06, 09 |
| `#models` | 10 |
| `#mcp` | 11 |
| `#troubleshooting` | 12 |
| `#acm-ai` | 13 |
| `#templates` | templates/ |

## Absorption Note

This directory supersedes:
- `docs/ralph-PLAYBOOK.md` → split across 00, 06, 10, 13
- `docs/ralph-research/ralph-variants-comparison.md` → absorbed into 01, 13
- `docs/ralph-research/claude-hooks-patterns.md` → absorbed into 08
- `docs/ralph-research/agent-teams-patterns.md` → absorbed into 09
- `docs/ralph-research/quality-gates-and-backpressure.md` → absorbed into 07, 08
- `docs/ralph-research/acm-ai-loop-design.md` → absorbed into 13

Old files are left in place. `docs/ralph/` is the authoritative reference.
