# Superpowers x BMAD Integration Guide

This document describes how [obra/superpowers](https://github.com/obra/superpowers) integrates with the ACM-AI project's BMAD V6 methodology, and how to set it up across Claude Code, ChatGPT Codex, and OpenCode.

## What Superpowers Provides

Superpowers is a composable skills framework for coding agents. It enforces disciplined development workflows:

- **Brainstorming** — structured requirement discovery before coding
- **Writing Plans** — creates bite-sized implementation tasks with verification steps
- **Executing Plans** — autonomous task execution with checkpoints
- **Test-Driven Development** — mandatory RED-GREEN-REFACTOR for all coding
- **Systematic Debugging** — 4-phase root cause analysis (never guess)
- **Code Review** — pre-review checklist before marking work complete
- **Git Worktrees** — isolated development branches
- **Subagent-Driven Development** — dispatch fresh agents per task

## How It Integrates with BMAD

BMAD handles project-level planning (epics, stories, architecture). Superpowers handles story-level implementation workflows. They complement each other:

### Workflow Routing

| Phase | Tool | Skills/Commands |
|---|---|---|
| Product Discovery | BMAD | `/analyst`, `/party-mode` |
| PRD Creation | BMAD | `/pm` |
| Architecture | BMAD | `/architect` |
| Epic/Story Creation | BMAD | Sprint planning workflows |
| Feature Brainstorm | Superpowers | `superpowers:brainstorming` |
| Implementation Planning | Superpowers | `superpowers:writing-plans` |
| Coding | Superpowers | `superpowers:test-driven-development` |
| Debugging | Superpowers | `superpowers:systematic-debugging` |
| Code Review | Superpowers | `superpowers:requesting-code-review` |
| Branch Completion | Superpowers | `superpowers:finishing-a-development-branch` |
| Sprint Tracking | BMAD | `sprint-status.yaml` |

### Artifact Locations

| Artifact | Location | Owner |
|---|---|---|
| PRD, Architecture, Epics | `_bmad-output/project-planning-artifacts/` | BMAD |
| Sprint Status | `docs/sprint-artifacts/sprint-status.yaml` | BMAD |
| Story Specs | `docs/sprint-artifacts/` | BMAD |
| Implementation Plans | `docs/plans/` | Superpowers |
| Ralph Fix Plans | `.ralph/@fix_plan.md` | Ralph |

### Mandatory Skills

These superpowers skills are **always** invoked — no exceptions:

1. `superpowers:test-driven-development` — before ANY coding task
2. `superpowers:systematic-debugging` — before ANY debugging
3. `superpowers:requesting-code-review` — before marking ANY story complete

## Setup Instructions

### Claude Code

```bash
# 1. Clone superpowers
git clone https://github.com/obra/superpowers.git ~/.claude/superpowers

# 2. Symlink skills for native discovery
mkdir -p ~/.claude/skills
ln -sf ~/.claude/superpowers/skills ~/.claude/skills/superpowers

# 3. (Optional) Create project-specific bridge skill
mkdir -p ~/.claude/skills/acm-ai/bmad-bridge
# Copy SKILL.md from the template (see below)

# 4. Verify
ls -la ~/.claude/skills/superpowers
# Should show symlink pointing to ~/.claude/superpowers/skills
```

The project's `.claude/hooks/session-start.sh` automatically displays the superpowers bridge routing when skills are detected.

### ChatGPT Codex

```bash
# 1. Clone superpowers
git clone https://github.com/obra/superpowers.git ~/.codex/superpowers

# 2. Symlink skills
mkdir -p ~/.agents/skills
ln -s ~/.codex/superpowers/skills ~/.agents/skills/superpowers

# 3. Restart Codex for skill discovery
```

Project-level config is in `.codex/`:
- `.codex/AGENTS.md` — project context and superpowers bootstrap
- `.codex/skills/acm-ai-context/SKILL.md` — ACM-AI specific context

### OpenCode

```bash
# 1. Clone superpowers
git clone https://github.com/obra/superpowers.git ~/.config/opencode/superpowers

# 2. Plugin symlink
mkdir -p ~/.config/opencode/plugins
ln -s ~/.config/opencode/superpowers/.opencode/plugins/superpowers.js \
  ~/.config/opencode/plugins/superpowers.js

# 3. Skills symlink
mkdir -p ~/.config/opencode/skills
ln -s ~/.config/opencode/superpowers/skills \
  ~/.config/opencode/skills/superpowers

# 4. Restart OpenCode
```

Project-level config is in `.opencode/`:
- `.opencode/skills/acm-ai-context/SKILL.md` — ACM-AI specific context

## Ralph Loop Integration

The Ralph autonomous loop includes superpowers skill invocations in `.ralph/PROMPT.md`:

1. Each iteration invokes `superpowers:test-driven-development` before implementation
2. Debugging failures invoke `superpowers:systematic-debugging`
3. After all tasks complete, `superpowers:requesting-code-review` runs before outputting `<promise>COMPLETE</promise>`

## Bridge Skill

The BMAD bridge skill at `~/.claude/skills/acm-ai/bmad-bridge/SKILL.md` teaches agents how to route between BMAD and Superpowers. It activates automatically for any project with `_bmad/` or `_bmad-output/` directories.

## Updating Superpowers

```bash
# Claude Code
cd ~/.claude/superpowers && git pull

# Codex
cd ~/.codex/superpowers && git pull

# OpenCode
cd ~/.config/opencode/superpowers && git pull
```

Updates apply immediately via symlinks — no restart needed.

## Rollback

If superpowers conflicts with existing workflows:

```bash
# Claude Code
rm ~/.claude/skills/superpowers

# Codex
rm ~/.agents/skills/superpowers

# OpenCode
rm ~/.config/opencode/plugins/superpowers.js
rm -rf ~/.config/opencode/skills/superpowers
```

Bridge skills are isolated — delete the `bmad-bridge/` directory from each skill location.

## Troubleshooting

| Issue | Solution |
|---|---|
| Skills not loading on session start | Verify symlink: `ls -la ~/.claude/skills/superpowers` |
| BMAD commands not working | BMAD commands are in `.claude/commands/bmad/` — independent of superpowers |
| Protected files hook blocking | Expected behavior — `pre-tool-use.sh` protects tests/, migrations/, etc. |
| Bridge skill not activating | Check `_bmad/` or `_bmad-output/` directories exist in project root |
| Implementation plans not saving | Create `docs/plans/` directory: `mkdir -p docs/plans` |

## Quick Reference Card

| I want to... | Use... | Platform |
|---|---|---|
| Plan a new epic | BMAD `/party-mode` | Claude Code |
| Design a feature within an epic | `superpowers:brainstorming` | All 3 |
| Create implementation tasks | `superpowers:writing-plans` | All 3 |
| Implement a story autonomously | Ralph loop + superpowers TDD | Claude Code |
| Implement tasks with checkpoints | `superpowers:executing-plans` | All 3 |
| Debug an issue | `superpowers:systematic-debugging` | All 3 |
| Review code before merge | `superpowers:requesting-code-review` | All 3 |
| Complete a branch | `superpowers:finishing-a-development-branch` | All 3 |
| Track sprint progress | BMAD `sprint-status.yaml` | Claude Code |
| Course correct | BMAD change proposal | Claude Code |
