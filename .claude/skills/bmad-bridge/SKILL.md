---
name: bmad-bridge
description: >
  Use when working on any BMAD-managed project. Bridges Superpowers skills with
  BMAD V6 methodology. Routes planning to BMAD agents, implementation to Superpowers
  skills. Mandatory for projects with _bmad/ or _bmad-output/ directories.
---

# BMAD x Superpowers Bridge

## When This Skill Activates
- Any project containing `_bmad/` or `_bmad-output/` directories
- When transitioning between planning and implementation phases
- When choosing between BMAD commands and Superpowers skills

## Workflow Routing Rules

### Planning Phase (USE BMAD)
- Product discovery: `/analyst` or `/party-mode`
- PRD creation: `/pm`
- Architecture: `/architect`
- Epic/Story creation: BMAD workflows
- Sprint planning: BMAD sprint-status.yaml
- Course corrections: BMAD change proposals

### Implementation Phase (USE SUPERPOWERS)
- Feature-level design refinement: `superpowers:brainstorming`
- Implementation planning from BMAD stories: `superpowers:writing-plans`
  - READ the BMAD story file first from `_bmad-output/`
  - Extract acceptance criteria into plan tasks
  - Save plan to `docs/plans/YYYY-MM-DD-<story-id>-<name>.md`
- Story implementation: `superpowers:executing-plans` or `superpowers:subagent-driven-development`
- ALL coding: `superpowers:test-driven-development` (mandatory, no exceptions)
- ALL debugging: `superpowers:systematic-debugging` (mandatory, no exceptions)
- Code review: `superpowers:requesting-code-review`
- Branch management: `superpowers:using-git-worktrees`
- Branch completion: `superpowers:finishing-a-development-branch`

### Ralph Loop Integration
When running Ralph autonomous loops:
- Ralph generates `@fix_plan.md` from BMAD stories (existing pattern)
- Each Ralph iteration MUST invoke `superpowers:test-driven-development`
- Ralph completion triggers `superpowers:requesting-code-review`
- After review passes, use `superpowers:finishing-a-development-branch`

## Artifact Locations
| Artifact Type | Location | Owner |
|---|---|---|
| PRD, Architecture, Epics | `_bmad-output/project-planning-artifacts/` | BMAD |
| Sprint Status | `_bmad-output/implementation-artifacts/sprint-status.yaml` | BMAD |
| Implementation Plans | `docs/plans/` | Superpowers |
| Story Specs | `docs/sprint-artifacts/` | BMAD |
| Design Docs | `docs/plans/*-design.md` | Superpowers |
| Change Proposals | `_bmad-output/` | BMAD |

## Protected Files (from pre-tool-use hook)
NEVER modify without explicit user approval:
- `migrations/` — database migrations
- Test files in `tests/` or `__tests__/`
- `.claude/hooks/` — hook scripts
- `_bmad/bmm/config.yaml` — BMAD config
- `sprint-status.yaml` — sprint tracking

## Project-Specific Rules
- API cost awareness: every extraction job triggers real OpenRouter API calls
- VAEA branding must be maintained on all user-facing components
- BAR format compliance is non-negotiable for export functionality
- Model: qwen2.5:7b (production), potential upgrade to qwen2.5:32b
