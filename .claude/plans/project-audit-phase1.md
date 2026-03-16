# ACM-AI Project Audit — Phase 1: Discovery Report

**Date**: 2026-03-05
**Auditor**: Senior Systems Architect
**Scope**: Full project structure, BMAD/agent framework, orchestration, context architecture

---

## 1.1 Project Structure Map

### Tech Stack & Versions
| Layer | Tech | Version |
|-------|------|---------|
| Backend | Python + FastAPI | 3.11+ / pyproject.toml v1.2.3 |
| Frontend | Next.js + React | 15.5.9 / React 19.1.0 |
| CSS | Tailwind CSS | 4.x |
| State | Zustand + React Query | 5.0.6 |
| Database | SurrealDB | Docker (port 8000) |
| AI | LangChain/LangGraph + Esperanto | multi-provider |
| Package Mgr | uv (backend) / npm (frontend) | |

### Root Directory Map (3 levels, noise filtered)

```
acm-ai/
├── api/                          # FastAPI routers, services, utils
├── commands/                     # Background job handlers
├── frontend/src/                 # Next.js 15 app (app/, components/, hooks/, lib/)
├── open_notebook/                # Domain layer (database/, domain/, extractors/, graphs/)
├── migrations/                   # SurrealDB schema migrations
├── prompts/                      # Jinja2 AI prompt templates
├── tests/                        # pytest + e2e (Playwright)
├── scripts/                      # Utility scripts + research
├── docs/                         # Comprehensive documentation tree
├── V3/                           # V3 architecture prompts + SF field definitions
├── benchmarks/                   # Ground truth + results
├── schemas/                      # Generated JSON schemas
│
├── .claude/                      # Claude Code configuration (PRIMARY)
│   ├── agents/       (24 files)  # Agent definitions
│   ├── commands/     (85 files)  # Slash commands (incl. BMAD + Ralph)
│   ├── hooks/        (10 files)  # Event-driven shell hooks
│   ├── rules/        (6 files)   # Domain-scoped context rules
│   ├── skills/       (62 dirs)   # Installable skills
│   ├── plans/                    # Active plan files
│   ├── worktrees/    (2 stale)   # Git worktrees with full .venvs
│   └── settings.json             # Permissions, env, hook config
│
├── _bmad/                        # BMAD framework v6.0.2
│   ├── core/                     # Master agent, tasks, brainstorming/party workflows
│   ├── bmm/                      # BMM module (9 agents, 34 workflows, team configs)
│   └── tea/                      # TEA testing module (1 agent, testarch knowledge base)
├── _bmad-output/                 # Generated BMAD artifacts (24 tracked files)
│
├── .agents/skills/   (111 dirs)  # DUPLICATE: superset of .claude/skills + BMAD skills
├── .codex/skills/    (57 dirs)   # DUPLICATE: subset of .claude/skills (for Codex)
├── .opencode/skills/ (57 dirs)   # DUPLICATE: subset of .claude/skills (for OpenCode)
├── .agent/workflows/ (10 files)  # DUPLICATE: BMAD agent defs for .agent format
├── .cursor/commands/ (5+ files)  # DUPLICATE: BMAD agent defs for Cursor
├── .gemini/commands/ (5+ files)  # DUPLICATE: BMAD agent defs for Gemini
├── .github/agents/   (5+ files)  # DUPLICATE: BMAD agent defs for GitHub Copilot
├── .github/prompts/  (5+ files)  # DUPLICATE: BMAD prompt defs for GitHub
├── .qwen/skills/     (3 dirs)    # Minimal Qwen config
├── .rovodev/         (10 files)  # NOT gitignored, 0 tracked (orphaned)
│
├── .auto-claude/                 # Auto-Claude framework (gitignored, stale)
├── .ralph/                       # Ralph loop logs (6+ sprint logs)
├── .langgraph_api/               # LangGraph API config
├── .vscode/                      # VS Code settings
│
├── google-cloud-sdk/             # STALE: Full GCloud SDK installation
├── marketing-site/               # STALE: Separate Next.js marketing site
├── tui/                          # STALE: Textual TUI prototype (4 .py files)
├── setup_guide/                  # STALE: Docker setup guide (4 files)
├── surreal_data/                 # DATA: 220MB SurrealDB data directory
├── _debug/                       # STALE: Debug scripts
├── pulls/                        # STALE: PR review artifacts
├── output/                       # Generated SF schema artifacts
├── research-output/              # Research spike outputs (517KB)
├── logs/                         # Runtime logs
├── data/                         # SQLite DB, tiktoken cache, uploads
```

### Flagged Artifacts

| Item | Type | Status | Notes |
|------|------|--------|-------|
| `google-cloud-sdk/` | Orphaned | **RED** | Full SDK installation at project root. Not in .gitignore. |
| `marketing-site/` | Stale | **YELLOW** | Separate Next.js app. Last meaningful activity unknown. |
| `tui/` | Dead code | **RED** | 4 Python files, Textual TUI prototype, never integrated |
| `setup_guide/` | Stale | **YELLOW** | Docker setup docs, superseded by CLAUDE.md |
| `_debug/` | Stale | **RED** | Debug scripts and prompt dumps |
| `pulls/45/` | Stale | **RED** | PR review artifact, should not be tracked |
| `surreal_data/` | Data | **YELLOW** | 220MB local DB data at root, should be gitignored |
| `.claude/worktrees/fervent-elion` | Stale | **RED** | Full .venv with site-packages inside worktree |
| `.claude/worktrees/fix-a-no-access-markers` | Stale | **YELLOW** | Leftover worktree |
| `.rovodev/` | Orphaned | **RED** | Not gitignored, 0 tracked files, unused |
| `.auto-claude/` | Stale | **YELLOW** | gitignored, old specs framework |
| `open_notebook.egg-info/` | Build artifact | **YELLOW** | Should be gitignored |
| `_MANIFEST.md` | Missing | **RED** | No centralized file inventory exists |

---

## 1.2 BMAD / Agent Framework Audit

### Agent Definitions (`.claude/agents/` — 24 files)

| Agent | Purpose | Trigger | Model | Rating |
|-------|---------|---------|-------|--------|
| `orchestrator` | Ralph Loop coordinator, delegates to specialists | Manual / Ralph commands | sonnet | WORKING |
| `backend-specialist` | Python/FastAPI implementation | Delegated by orchestrator | sonnet | WORKING |
| `frontend-specialist` | Next.js/React implementation | Delegated by orchestrator | sonnet | WORKING |
| `docs-specialist` | Documentation updates post-story | Delegated by orchestrator | sonnet | WORKING |
| `qa-specialist` | Test validation, AC coverage | Delegated by orchestrator | sonnet | WORKING |
| `acm-extraction-core` | MinerU/regex extraction core | Delegated for E1-S* stories | sonnet | WORKING |
| `acm-extraction-post` | Corrective RAG, BAR validation | Delegated for E1-S14/15 stories | sonnet | WORKING |
| `acm-extraction-pre` | Doc structure analysis, TOC extraction | Delegated for E1-S16-19 stories | sonnet | WORKING |
| `acm-rag-strategist` | RAG design and implementation | Delegated for RAG stories | sonnet | WORKING |
| `acm-research-lead` | Research team coordination | Team lead for research | sonnet | WORKING |
| `acm-schema-expert` | SurrealDB migrations, schema design | Delegated for DB stories | sonnet | WORKING |
| `acm-sprint-lead` | Sprint execution coordination | Team lead for sprints | sonnet | WORKING |
| `acm-ui-tester` | UI testing with browser automation | Delegated for UI testing | sonnet | WORKING |
| `acm-e2e-tester` | Full-stack E2E testing | Delegated for E2E stories | sonnet | WORKING |
| `e36-lead` | E36 verification team orchestrator | E36 sprint | sonnet | WORKING |
| `e36-browser-tester` | UI testing via agent-browser CLI | E36 team member | sonnet | WORKING |
| `e36-log-sentinel` | Log monitoring during extraction | E36 team member | sonnet | WORKING |
| `e36-devils-advocate` | Adversarial code/test review | E36 team member | sonnet | WORKING |
| `e36-bmad-scribe` | BMAD documentation updates | E36 team member | haiku | WORKING |
| `e36-ux-auditor` | Visual/responsive/a11y audit | E36 team member | sonnet | WORKING |
| `ralph-sm` | Ralph Scrum Master agent | Ralph run workflow | sonnet | WORKING |
| `ralph-architect` | Ralph Architecture agent | Ralph run workflow | sonnet | WORKING |
| `ralph-qa` | Ralph QA agent | Ralph run workflow | sonnet | WORKING |
| `ralph-reviewer` | Ralph Code Review agent | Ralph run workflow | sonnet | WORKING |

**Assessment**: All 24 agents have proper name, description, tools list, and model specified. Scoping is generally good — agents declare their working directories. However, there is no standard for `maxTurns` (ranges from unset to 50) and no error escalation protocol defined in any agent.

### Hooks (`.claude/hooks/` — 10 files)

| Hook | Event | Purpose | Side Effects | Rating |
|------|-------|---------|--------------|--------|
| `session-start.sh` | SessionStart | Path normalization, env check | Sets vars | WORKING |
| `auto-commit.sh` | Stop | Auto-commit WIP | Git commit | NEEDS-IMPROVEMENT (disabled) |
| `pre-commit-gate.sh` | PreToolUse:Bash | Block commits without verification | Blocks git commit | WORKING |
| `pre-tool-use.sh` | PreToolUse | Block modifications to protected files | Blocks Write/Edit | WORKING |
| `ralph-gate-guard.sh` | PreToolUse:Bash | Block commits for unmet dependencies | Blocks git commit | WORKING |
| `ralph-progress.sh` | PostToolUse:Write/Edit | Show story progress | Informational | WORKING |
| `ralph-stop-gate.sh` | Stop | Prevent premature stop during Ralph | Blocks stop | WORKING |
| `scope-guard.sh` | PreToolUse:Write/Edit | Block writes to protected paths | Blocks Write/Edit | WORKING |
| `story-done-check.sh` | PostToolUse:Write/Edit | Auto-commit+push+PR on story done | Git commit, push, PR | NEEDS-IMPROVEMENT |
| `task-quality-gate.sh` | TaskCompleted | Run lint+build before task done | Blocks completion | WORKING |

**Assessment**: Hooks are well-structured with clear trigger conditions. Two concerns:
1. `auto-commit.sh` is disabled (replaced with echo) — the Stop hook config still references it implicitly
2. `story-done-check.sh` creates PRs automatically — no rollback if PR creation fails
3. No hooks log their actions to a persistent file — debugging hook failures requires manual investigation

### Rules (`.claude/rules/` — 6 files)

| Rule | Applies To | Rating |
|------|-----------|--------|
| `docker-compose.md` | `docker-compose*.yml` | WORKING |
| `langgraph-ai.md` | `open_notebook/graphs/**`, `prompts/**` | WORKING |
| `mcp-servers.md` | `.claude/settings*.json` | WORKING |
| `nextjs-frontend.md` | `frontend/**/*.ts`, `frontend/**/*.tsx` | WORKING |
| `python-backend.md` | `**/*.py`, `api/**`, `open_notebook/**` | WORKING |
| `surrealdb.md` | `migrations/**`, `open_notebook/database/**` | WORKING |

**Assessment**: Good domain-scoped context. Missing: tests rule, scripts rule, docs rule, agent definition rule.

### Skills (`.claude/skills/` — 62 directories)

**Categorization**:
- **Project-specific** (5): `e2e-test`, `baseline-ui`, `planning-with-files`, `agent-browser`, `dogfood`
- **General dev** (~30): `commit`, `create-pr`, `code-review`, `find-bugs`, `systematic-debugging`, etc.
- **Security** (~8): `clawsec-*`, `openclaw-*`, `differential-review`, `insecure-defaults`
- **BMAD** (~40 in `.agents/skills/`, not in `.claude/skills/`): bmad-agent-*, bmad-bmm-*
- **Document** (4): `docx`, `pdf`, `pptx`, `xlsx`

**Rating**: NEEDS-IMPROVEMENT
- Most skills have a `SKILL.md` file with proper structure
- Massive duplication: same skills exist in `.agents/skills/`, `.codex/skills/`, `.opencode/skills/` (4x copies)
- No skill inventory or classification system
- No usage tracking to know which skills are actually used

### BMAD Framework (`_bmad/` — 3 modules)

| Module | Contents | Rating |
|--------|----------|--------|
| `core` | bmad-master agent, 6 tasks (editorial, review, shard, etc.), 3 workflows (brainstorming, party-mode, elicitation) | WORKING |
| `bmm` | 9 agents (analyst, architect, dev, pm, qa, sm, tech-writer, ux-designer, quick-flow-solo-dev), 34 workflows across 6 phases, team configs | WORKING |
| `tea` | 1 agent (tea), testarch knowledge base (15+ .md files), team config | WORKING |

**Assessment**: BMAD v6.0.2 is a comprehensive framework. The `_bmad/` source directory is well-organized with clear module boundaries. However, the distribution to different IDE formats (`.cursor/`, `.gemini/`, `.github/`, `.agent/`, `.rovodev/`, `.opencode/`) creates massive duplication without a clear sync mechanism.

---

## 1.3 Orchestration Assessment

### Central Orchestrator
**Yes** — `orchestrator.md` is the central coordinator for the Ralph Loop pattern.

**Flow**: `/ralph-run` command → orchestrator reads `docs/sprint-artifacts/` → finds next story → delegates to specialist agent (backend/frontend/qa/docs) → specialist implements → orchestrator verifies → marks done.

### Communication Model
| Channel | Type | Used By |
|---------|------|---------|
| `docs/sprint-artifacts/` | File-based | Orchestrator reads story files |
| `prd.json` | File-based | Ralph bridge generates, all agents reference |
| `.claude/hooks/` | Event-driven | Hook system fires on tool use, stop, start |
| Agent Teams (`SendMessage`) | Direct invocation | E36 team, sprint teams |
| `TaskCreate/TaskUpdate` | Task queue | Team coordination |
| `docs/sprint-artifacts/sprint-status.yaml` | File-based | Status tracking across sprints |

### Task Queue / Scheduling
- **Ralph Loop**: `/ralph-init` → `/ralph-run` → `/ralph-status` provides story-level scheduling
- **Agent Teams**: `TaskCreate`/`TaskList`/`TaskUpdate` provides within-sprint task coordination
- **No external scheduler**: Everything runs within Claude Code sessions

### Subagent Pattern
- Context scoping: Agents declare working directories in their `.md` files
- Model selection rules in CLAUDE.md: sonnet for teams, opus for single complex tasks
- `maxTurns` caps: ranges from unset to 50, inconsistent
- **Gap**: No inter-agent communication protocol beyond file-based handoffs and `SendMessage`

---

## 1.4 Context Architecture Audit

### Global Instructions
| File | Scope | Lines | Rating |
|------|-------|-------|--------|
| `CLAUDE.md` | ALL sessions, ALL agents | ~450 | **NEEDS-IMPROVEMENT** — too large, loaded every time |
| `~/.claude/rules/context7.md` | Global (user-level) | ~15 | WORKING |
| `~/.claude/projects/.../memory/MEMORY.md` | Persistent across sessions | ~200 | WORKING |

### Project-Specific Context
| File | Scope | Rating |
|------|-------|--------|
| `.claude/rules/*.md` (6 files) | Pattern-matched to file globs | WORKING |
| `.claude/agents/*.md` (24 files) | Agent-specific scoping | WORKING |
| `_bmad/bmm/config.yaml` | BMAD configuration | WORKING |
| `docs/sprint-artifacts/sprint-status.yaml` | Sprint state | WORKING |
| `prd.json` | Product backlog | WORKING |

### Context Scoping Problems
1. **CLAUDE.md is monolithic** — 450+ lines loaded for EVERY session regardless of task. Contains: project overview, commands, architecture, patterns, environment vars, code style, sub-agent rules, story verification, V3 architecture, MinerU details, Docker overrides, custom commands reference, Ralph config, agent team rules, E36 team reference. A developer fixing a CSS bug gets the full MinerU extraction pipeline documentation.

2. **No folder-level context files** — The `frontend/` directory has no `CLAUDE.md` or context file. Neither does `api/`, `open_notebook/`, `tests/`, or `scripts/`. The `.claude/rules/` files partially fill this gap but only for file-type matching, not directory-scoped instructions.

3. **Skills are not scoped** — All 62+ skills are available in every session. Many are irrelevant to ACM-AI (claw-release, clawtributor, openclaw-audit-watchdog, soul-guardian).

4. **Agent memory is centralized** — Single `MEMORY.md` file grows over time. No per-domain or per-sprint memory partitioning.

5. **_bmad-output is checked in** — Generated planning artifacts (24 files) are tracked in git, mixing generated and authored content.

### Persistent Context Compounding
- `MEMORY.md` has ~200 lines and is actively maintained with version-specific notes
- `prd.json` is 1805 lines and growing (all epics/stories)
- `sprint-status.yaml` tracks all sprints since inception
- **No archival mechanism** — completed sprint artifacts stay in `docs/sprint-artifacts/` indefinitely

---

## Summary Scorecard

| Area | Score | Key Issues |
|------|-------|------------|
| Project Structure | 5/10 | Orphaned dirs, no manifest, root-level data files |
| Agent Definitions | 8/10 | Well-scoped, but no error escalation or maxTurns consistency |
| Hooks | 7/10 | Good coverage, but no logging or rollback |
| Rules | 7/10 | Good pattern, but missing coverage for tests/scripts/docs |
| Skills | 4/10 | Massive 4x duplication, no inventory, many irrelevant |
| BMAD Framework | 7/10 | Solid source, but distribution duplication is extreme |
| Orchestration | 7/10 | Ralph Loop is well-designed, but no external scheduler |
| Context Architecture | 5/10 | Monolithic CLAUDE.md, no folder-level scoping, no archival |
| **Overall** | **6.25/10** | **Functional but significant structural debt** |

---

## Critical Findings (Top 5)

1. **Skills/Agent duplication across 7+ IDE directories** — `.claude/skills/` (62), `.agents/skills/` (111), `.codex/skills/` (57), `.opencode/skills/` (57), plus BMAD agents in `.cursor/`, `.gemini/`, `.github/`, `.agent/`, `.rovodev/`. Estimated 500+ duplicate files. No sync mechanism. UNCERTAIN: whether the BMAD installer (`_bmad`) auto-generates these or they were manually copied.

2. **Monolithic CLAUDE.md** — 450+ lines loaded every session. Contains information irrelevant to most tasks (MinerU internals, Docker overrides, E36 team roster). Should be decomposed into tiered context files.

3. **Orphaned directories at root** — `google-cloud-sdk/`, `tui/`, `_debug/`, `pulls/`, `setup_guide/` are dead weight. `surreal_data/` (220MB) and `.claude/worktrees/fervent-elion` (full .venv) are disk bloat.

4. **No error escalation paths** — When an agent fails or a hook blocks, there's no defined recovery protocol. Hooks exit with codes 0/1/2 but no fallback action. Agents have no "I'm stuck" protocol beyond the Ralph `BLOCKED` signal.

5. **No _MANIFEST.md or centralized file inventory** — With 500+ configuration files across 10+ directories, there's no single source of truth for what exists, what's active, and what's deprecated.

---

**Ready for Phase 2 when you approve these findings.**
