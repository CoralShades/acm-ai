# OpenCode Setup Plan — ACM-AI Project

**Created:** 2026-02-25  
**Status:** READY TO EXECUTE  
**Context:** OpenCode runs from **PowerShell on Windows** (`C:\nvm4w\nodejs\opencode.ps1`). The project lives on WSL at `/mnt/d/ailocal/acm-ai` (Windows: `D:\ailocal\acm-ai`).

---

## Executive Summary

Two deliverables:
1. **`opencode.json`** — project-level OpenCode config (MCP servers + agents + instructions)
2. **`CLAUDE.md` additions** — 5 new sections documenting agents, hooks, key reference files, AG Grid pattern, BMAD env vars

Plus a **compatibility layer** because Claude Code hooks (bash scripts) are not a feature in OpenCode — OpenCode uses a JS/TS **plugin system** instead.

---

## Environment Facts (verified)

| Item | Value |
|------|-------|
| OpenCode executable | `C:\nvm4w\nodejs\opencode.ps1` |
| OpenCode runs in | PowerShell (Windows), NOT WSL |
| `node` / `npx` on Windows PATH | Node v22.21.0, npx v10.9.4 |
| `uv.exe` on Windows PATH | `C:\Users\User\.local\bin\uv.exe` |
| `uvx.exe` on Windows PATH | `C:\Users\User\.local\bin\uvx.exe` |
| `gh.exe` on Windows PATH | `C:\Program Files\GitHub CLI\gh.exe` |
| `bash.exe` on Windows PATH | `C:\Windows\System32\bash.exe` (WSL bridge) |
| `docker.exe` on Windows PATH | `C:\Program Files\Docker\Docker\resources\bin\docker.exe` |
| `ruff` on Windows PATH | NOT directly — use `uv run ruff` or `uvx ruff` |
| Windows project path | `D:\ailocal\acm-ai` |
| WSL project path | `/mnt/d/ailocal/acm-ai` |
| GITHUB_TOKEN set? | Not set in Windows env — must use `{env:GITHUB_TOKEN}` (will be empty if not set) |
| OpenCode agents dir | `.opencode/agents/` (project) or `~/.config/opencode/agents/` (global) |
| OpenCode plugins dir | `.opencode/plugins/` (project) or `~/.config/opencode/plugins/` (global) |
| OpenCode commands dir | `.opencode/commands/` (project) |
| OpenCode config file | `opencode.json` in project root |

---

## Critical Difference: Claude Code Hooks vs OpenCode Plugins

**Claude Code** has a native hook system (`.claude/settings.json` → `hooks:`) that runs shell commands on lifecycle events (SessionStart, Stop, PreToolUse, PostToolUse, TaskCompleted).

**OpenCode has NO equivalent hook system.** It uses a JavaScript/TypeScript **plugin system** in `.opencode/plugins/`. Plugins subscribe to events like `tool.execute.before`, `tool.execute.after`, `session.idle`, `shell.env`, etc.

### Hook Migration Strategy

The 7 bash hooks need to either:
- **Be migrated** to OpenCode JS plugins (for hooks that add real value in OpenCode sessions)  
- **Be documented as Claude Code only** (for hooks that only make sense in Claude Code context, e.g., `ralph-stop-gate.sh`)

| Claude Code Hook | Migration for OpenCode |
|-----------------|----------------------|
| `session-start.sh` | **Plugin**: `session-banner.js` — subscribe to `session.created`, print banner via `tui.toast.show`; inject BMAD env vars via `shell.env` |
| `scope-guard.sh` | **Plugin**: `scope-guard.js` — subscribe to `tool.execute.before` for write/edit tools, block protected paths |
| `pre-commit-gate.sh` | **Plugin**: `pre-commit-gate.js` — subscribe to `tool.execute.before` for bash tool, intercept `git commit` commands, run lint/build checks via `$` (Bun shell) using `wsl bash -c` or Windows-native commands |
| `story-done-check.sh` | **Plugin**: `story-done-check.js` — subscribe to `tool.execute.after` for write/edit, detect story status=done, auto-commit+push+PR using Windows `gh.exe` |
| `task-quality-gate.sh` | **Plugin**: `task-quality-gate.js` — subscribe to `session.idle`, run quality checks (but note: no TaskCompleted equivalent in OpenCode) |
| `auto-commit.sh` | **Plugin**: `auto-commit.js` — subscribe to `session.idle`, auto-commit WIP using `wsl bash -c "git add -u && git commit ..."` |
| `ralph-stop-gate.sh` | **Claude Code only** — not applicable to OpenCode (Ralph loop is a Claude Code concept) |

### Windows Command Strategy for Plugins

All plugin `$` shell calls run via Bun's shell API (Unix-like). Since OpenCode runs on Windows, use:
- **For git/npm/uv commands**: Call the Windows executables directly (they're on PATH)
  - `$\`git status\`` — git.exe is on Windows PATH
  - `$\`npm run lint\`` — npm.exe is on Windows PATH  
  - `$\`uv run ruff check .\`` — uv.exe is on Windows PATH
- **For complex bash logic**: Use `wsl bash -c "..."` or `bash.exe -c "..."`
  - `$\`bash -c "cd /mnt/d/ailocal/acm-ai && uv run ruff check . --quiet"\``
- **For paths**: Use Windows paths (`D:\ailocal\acm-ai`) in commands, or rely on CWD

---

## Deliverable 1: `opencode.json`

**File:** `/mnt/d/ailocal/acm-ai/opencode.json`

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": ["CLAUDE.md", "MEMORY.md"],
  "mcp": {
    "filesystem": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "D:\\ailocal\\acm-ai"],
      "enabled": true
    },
    "memory": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-memory"],
      "enabled": true
    },
    "playwright": {
      "type": "local",
      "command": ["npx", "-y", "@playwright/mcp@latest"],
      "enabled": true
    },
    "chrome-devtools": {
      "type": "local",
      "command": ["npx", "-y", "chrome-devtools-mcp@latest"],
      "enabled": true
    },
    "github": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
      "enabled": true,
      "environment": {
        "GITHUB_TOKEN": "{env:GITHUB_TOKEN}"
      }
    },
    "vercel": {
      "type": "local",
      "command": ["npx", "-y", "@vercel/mcp-adapter"],
      "enabled": true,
      "environment": {
        "VERCEL_TOKEN": "{env:VERCEL_TOKEN}"
      }
    },
    "context7": {
      "type": "remote",
      "url": "https://mcp.context7.com/mcp",
      "enabled": true
    },
    "gh_grep": {
      "type": "remote",
      "url": "https://mcp.grep.app",
      "enabled": true
    }
  }
}
```

### Notes on MCP Commands (PowerShell/Windows)

| Server | Command | Notes |
|--------|---------|-------|
| `filesystem` | `npx -y @modelcontextprotocol/server-filesystem D:\ailocal\acm-ai` | Path must be Windows-style. Use `\\` in JSON. |
| `memory` | `npx -y @modelcontextprotocol/server-memory` | No path needed, stateless |
| `playwright` | `npx -y @playwright/mcp@latest` | Playwright must be installed on Windows (or via npm) |
| `chrome-devtools` | `npx -y chrome-devtools-mcp@latest` | Requires Chrome running with `--remote-debugging-port=9222` |
| `github` | `npx -y @modelcontextprotocol/server-github` | GITHUB_TOKEN env var required; warn if not set |
| `vercel` | `npx -y @vercel/mcp-adapter` | VERCEL_TOKEN env var required; warn if not set |
| `context7` | Remote: `https://mcp.context7.com/mcp` | No auth needed for free tier |
| `gh_grep` | Remote: `https://mcp.grep.app` | No auth needed |

### Pre-flight: Verify npx packages work on Windows

Before relying on these, run from PowerShell:
```powershell
npx -y @modelcontextprotocol/server-filesystem --help
npx -y @modelcontextprotocol/server-memory --help
npx -y @playwright/mcp@latest --help
```

If any fail with ENOENT or module errors, consider using `bun x` instead of `npx -y` (both are available on Windows PATH). Alternative command array: `["bun", "x", "<package>"]`.

---

## Deliverable 2: OpenCode Agents in `.opencode/agents/`

OpenCode loads agents from `.opencode/agents/` automatically. The existing Claude Code agents in `.claude/agents/` use a compatible markdown frontmatter format — but OpenCode uses different frontmatter keys.

### Claude Code vs OpenCode Agent Frontmatter

| Claude Code | OpenCode |
|-------------|----------|
| No frontmatter convention | `description`, `mode`, `model`, `tools`, `permissions`, `temperature`, `steps` |
| System prompt in body | System prompt in body (same) |
| `subagent_type` used by Task tool | `mode: subagent` — invokable via `@mention` |

### Action: Create `.opencode/agents/` directory with port of key agents

Port the most useful agents from `.claude/agents/` to `.opencode/agents/`. Not all 14 agents need porting — focus on those useful in an interactive OpenCode session.

**Agents to port (6 core):**

1. `backend-specialist.md` — Python/FastAPI/SurrealDB work
2. `frontend-specialist.md` — Next.js/React/Tailwind work  
3. `qa-specialist.md` — Testing and quality
4. `docs-specialist.md` — Documentation
5. `acm-extraction-core.md` — ACM data extraction
6. `acm-rag-strategist.md` — RAG/AI strategy

**Agents to skip (Claude Code team-orchestration specific):**
- `orchestrator.md` — Uses TeamCreate, Claude Code teams feature
- `acm-sprint-lead.md` — Sprint orchestration
- `acm-research-lead.md` — Research lead  
- `acm-extraction-pre.md` / `acm-extraction-post.md` — Team pipeline stages
- `acm-schema-expert.md` — Schema specialist (can be merged into backend-specialist)
- `acm-e2e-tester.md` / `acm-ui-tester.md` — Can be merged into qa-specialist

### OpenCode Agent Format Example

```markdown
---
description: Python/FastAPI/SurrealDB backend development specialist
mode: subagent
model: github-copilot/claude-sonnet-4.6
tools:
  write: true
  edit: true
  bash: true
---

[system prompt content here]
```

---

## Deliverable 3: OpenCode Plugins in `.opencode/plugins/`

Create these JS plugins (no TypeScript needed for simplicity, no build step):

### Plugin 1: `session-banner.js`

Event: `session.created` + `shell.env`  
Purpose: Print ACM-AI banner on session start; inject BMAD env vars

```javascript
export const SessionBannerPlugin = async ({ $, directory }) => {
  return {
    "shell.env": async (input, output) => {
      output.env.BMAD_PROJECT_ROOT = "D:\\ailocal\\acm-ai"
      output.env.BMAD_OUTPUT_FOLDER = "D:\\ailocal\\acm-ai\\_bmad-output"
      output.env.BMAD_USER = "Demi"
      output.env.BMAD_LANGUAGE = "English"
    },
    "session.created": async () => {
      // Read sprint status
      // Print banner (use tui.toast.show or console.log)
    }
  }
}
```

### Plugin 2: `scope-guard.js`

Event: `tool.execute.before`  
Purpose: Block writes to protected paths  
Protected: `.env`, `uv.lock`, `frontend/package-lock.json`, `docker-compose*.yml`, `.github/`, `.claude/settings.json`, `.claude/settings.local.json`, `pyproject.toml`

```javascript
export const ScopeGuardPlugin = async () => {
  const PROTECTED = [
    /^\.env($|\.)/,
    /^uv\.lock$/,
    /^frontend\/package-lock\.json$/,
    /^docker-compose/,
    /^\.github\//,
    /^\.claude\/settings/,
    /^pyproject\.toml$/,
  ]
  return {
    "tool.execute.before": async (input, output) => {
      const tool = input.tool
      if (tool !== "write" && tool !== "edit") return
      const filePath = output.args?.filePath || output.args?.path || ""
      // Normalize: strip project root prefix, convert backslashes
      const rel = filePath.replace(/\\/g, "/").replace(/^.*acm-ai\//, "")
      if (PROTECTED.some(p => p.test(rel))) {
        throw new Error(`Scope guard: cannot modify protected file '${rel}'`)
      }
    }
  }
}
```

### Plugin 3: `auto-commit.js`

Event: `session.idle`  
Purpose: Auto-commit WIP on session end (safety checkpoint)  
Uses: `bash.exe -c` for git commands (git is also available on Windows PATH directly)

```javascript
export const AutoCommitPlugin = async ({ $ }) => {
  return {
    "session.idle": async () => {
      // Check if on non-main branch with uncommitted changes
      // Stage tracked files, commit with wip: message, push
      // Use: await $`git status --porcelain` etc.
    }
  }
}
```

### Plugin 4: `pre-commit-gate.js`

Event: `tool.execute.before` (bash tool)  
Purpose: Intercept `git commit` and block if lint/build fail  
Uses: `uv.exe` (Windows) for ruff; `npm` for frontend

```javascript
// Intercept: input.tool === "bash" && command includes "git commit"
// Run: uv run ruff check . (via Windows uv.exe)
// Run: cd frontend && npm run lint && npm run build
// Throw on failure to block commit
```

---

## Deliverable 4: CLAUDE.md Additions (5 sections, additive only)

All insertions are **additive** — no existing content is modified.

### Section A: Custom Agents Table
**Insert after:** "Claude Code Custom Commands" section (after the table at ~line 297)

```markdown
## Custom Agents

Project-specific agents in `.claude/agents/` (Claude Code) and `.opencode/agents/` (OpenCode):

| Agent | File | Role | Used By |
|-------|------|------|---------|
| `orchestrator` | `orchestrator.md` | Sprint orchestrator; reads stories, delegates to specialists | Claude Code teams |
| `backend-specialist` | `backend-specialist.md` | Python/FastAPI/SurrealDB development | Both |
| `frontend-specialist` | `frontend-specialist.md` | Next.js/React/Tailwind/AG Grid development | Both |
| `qa-specialist` | `qa-specialist.md` | Testing, playwright, quality gates | Both |
| `docs-specialist` | `docs-specialist.md` | Documentation updates and MEMORY.md maintenance | Both |
| `acm-sprint-lead` | `acm-sprint-lead.md` | ACM sprint coordination | Claude Code teams |
| `acm-research-lead` | `acm-research-lead.md` | Research and spike work | Claude Code teams |
| `acm-extraction-core` | `acm-extraction-core.md` | ACM data extraction implementation | Both |
| `acm-extraction-pre` | `acm-extraction-pre.md` | Pre-processing pipeline stage | Claude Code teams |
| `acm-extraction-post` | `acm-extraction-post.md` | Post-processing pipeline stage | Claude Code teams |
| `acm-rag-strategist` | `acm-rag-strategist.md` | RAG/vector search strategy | Both |
| `acm-schema-expert` | `acm-schema-expert.md` | SurrealDB schema design | Both |
| `acm-e2e-tester` | `acm-e2e-tester.md` | End-to-end Playwright testing | Claude Code teams |
| `acm-ui-tester` | `acm-ui-tester.md` | UI component testing | Claude Code teams |

**Note:** Agents marked "Both" are ported to `.opencode/agents/` for OpenCode sessions. "Claude Code teams" agents require `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` and are not available in OpenCode.
```

### Section B: Hooks Documentation
**Insert after:** "MCP Configuration" section (~line 321)

```markdown
## Hooks (Claude Code Only)

Claude Code lifecycle hooks in `.claude/hooks/`. **Not applicable to OpenCode** — OpenCode uses a plugin system in `.opencode/plugins/` instead.

| Hook File | Event | Trigger | Behavior |
|-----------|-------|---------|----------|
| `session-start.sh` | `SessionStart` | New session startup | Installs cloud deps; persists BMAD env vars (`BMAD_USER=Demi`, `BMAD_OUTPUT_FOLDER=_bmad-output/`); prints project banner |
| `scope-guard.sh` | `PreToolUse Write\|Edit` | Any file write/edit | Blocks protected paths during Ralph loop (only when `.ralph/@fix_plan.md` exists) |
| `pre-commit-gate.sh` | `PreToolUse Bash` | Any bash command | Intercepts `git commit`; blocks unless ruff + frontend lint+build pass (Ralph loop only) |
| `story-done-check.sh` | `PostToolUse Write\|Edit` | After file write/edit | Detects `**Status:** done` in sprint story files; auto-commits, pushes, creates PR via `gh` CLI |
| `task-quality-gate.sh` | `TaskCompleted` | Agent task completion | Blocks task completion unless ruff + frontend lint+build pass |
| `auto-commit.sh` | `Stop` | Session end | Commits uncommitted tracked changes as `wip: safety checkpoint` on non-main branches |
| `ralph-stop-gate.sh` | `Stop` | Session end | Prevents stop during Ralph sprint loop; checks `.ralph/@fix_plan.md` for unchecked tasks |

**Protected paths** (scope-guard + scope-guard.js):  
`.env`, `uv.lock`, `frontend/package-lock.json`, `docker-compose*.yml`, `.github/`, `.claude/settings.json`, `.claude/settings.local.json`, `pyproject.toml`

**OpenCode equivalents** in `.opencode/plugins/`:
- `session-banner.js` → session-start.sh equivalent (shell.env + session.created events)
- `scope-guard.js` → scope-guard.sh equivalent (tool.execute.before event)
- `pre-commit-gate.js` → pre-commit-gate.sh equivalent (tool.execute.before bash event)
- `auto-commit.js` → auto-commit.sh equivalent (session.idle event)
```

### Section C: Key Reference Files
**Append to:** "Documentation" section, after the "Key docs:" list (~line 280)

```markdown
**Key reference files (always load at session start):**
- `MEMORY.md` — Persistent project memory: decisions, patterns, gotchas. Updated after significant sessions.
- `docs/sprint-artifacts/sprint-status.yaml` — Live sprint progress: completed/pending stories, current focus.
```

### Section D: AG Grid Pattern
**Add bullet to:** "Key Patterns" section, after the Frontend bullet (~line 111)

```markdown
- **AG Grid**: AG Grid React v35 (`ag-grid-react`) for tabular ACM data display. See `frontend/src/components/acm/ACMGrid.tsx` for the primary implementation pattern.
```

### Section E: BMAD Environment Variables
**Add to:** "Environment Variables" section, after the main `.env` block (~line 175)

```markdown
### BMAD Session Variables

Set automatically by `session-start.sh` (Claude Code) and `session-banner.js` (OpenCode). Do NOT put these in `.env`.

```bash
BMAD_USER=Demi               # Your name — used by BMAD agents for personalization
BMAD_LANGUAGE=English        # Output language for BMAD workflows
BMAD_PROJECT_ROOT=<auto>     # Set to project directory at session start
BMAD_OUTPUT_FOLDER=_bmad-output/  # BMAD artifact output directory
```
```

---

## Implementation Order

### Phase 1: `opencode.json` (simple, no dependencies)
1. Create `/mnt/d/ailocal/acm-ai/opencode.json` with MCP config
2. Verify by running `opencode` from project directory and checking MCP servers load

### Phase 2: OpenCode Agents (`.opencode/agents/`)
1. Create `.opencode/agents/` directory
2. Port 6 core agents from `.claude/agents/` with OpenCode-compatible frontmatter
3. Test by `@mention`ing an agent in OpenCode

### Phase 3: OpenCode Plugins (`.opencode/plugins/`)
1. Create `.opencode/plugins/` directory
2. Implement `session-banner.js` (BMAD env vars + banner)
3. Implement `scope-guard.js` (protected file blocking)
4. Implement `pre-commit-gate.js` (commit gate)
5. Implement `auto-commit.js` (WIP safety checkpoint)
6. Test each plugin's behavior

### Phase 4: CLAUDE.md Additions
1. Add Section D (AG Grid pattern bullet) to Key Patterns
2. Add Section C (key reference files) to Documentation
3. Add Section E (BMAD env vars) to Environment Variables
4. Add Section A (Custom Agents table) after Claude Code Custom Commands
5. Add Section B (Hooks documentation) after MCP Configuration
6. Review that no existing content was modified

---

## Verification Steps

### `opencode.json` verification
```powershell
# From PowerShell in D:\ailocal\acm-ai:
opencode mcp list
# Should show all 8 servers. Remote ones (context7, gh_grep) should show as remote.
# Local ones may show errors if not yet installed — that's OK, they lazy-install.
```

### Agent verification
```
# In OpenCode TUI: type @backend-specialist
# Should autocomplete and show the agent
```

### Plugin verification
```
# In OpenCode TUI: start a new session
# Should see BMAD env vars injected
# Try editing .env — should be blocked by scope-guard.js
```

### CLAUDE.md verification
```bash
# In WSL:
grep -n "Custom Agents" CLAUDE.md      # Should find the new section
grep -n "BMAD Session Variables" CLAUDE.md  # Should find env vars section
grep -n "AG Grid" CLAUDE.md            # Should find the bullet
grep -n "session-start.sh" CLAUDE.md  # Should find hooks table
grep -n "MEMORY.md" CLAUDE.md         # Should find reference in Documentation section
```

---

## Known Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| `npx -y` slow on first run (downloads package) | Acceptable — packages cache after first use |
| `chrome-devtools-mcp` requires Chrome with `--remote-debugging-port=9222` | Document in CLAUDE.md; add note to opencode.json comment |
| `GITHUB_TOKEN` not set | `{env:GITHUB_TOKEN}` resolves to empty string — github MCP will fail gracefully |
| `VERCEL_TOKEN` not set | Same — vercel MCP will fail gracefully |
| OpenCode Bun shell on Windows — path separators | Use `path.normalize()` or always compare normalized paths in plugins |
| `session.idle` fires frequently, not just on "stop" | Auto-commit plugin must check `git status` before committing; use cooldown or debounce |
| OpenCode plugin API may differ from docs | Test iteratively; check `.opencode/plugins/` examples in OpenCode ecosystem |

---

## Files to Create / Edit Summary

| File | Action | Size estimate |
|------|--------|--------------|
| `opencode.json` | **Create** | ~50 lines |
| `.opencode/agents/backend-specialist.md` | **Create** | ~80 lines |
| `.opencode/agents/frontend-specialist.md` | **Create** | ~80 lines |
| `.opencode/agents/qa-specialist.md` | **Create** | ~60 lines |
| `.opencode/agents/docs-specialist.md` | **Create** | ~50 lines |
| `.opencode/agents/acm-extraction-core.md` | **Create** | ~80 lines |
| `.opencode/agents/acm-rag-strategist.md` | **Create** | ~60 lines |
| `.opencode/plugins/session-banner.js` | **Create** | ~60 lines |
| `.opencode/plugins/scope-guard.js` | **Create** | ~40 lines |
| `.opencode/plugins/pre-commit-gate.js` | **Create** | ~60 lines |
| `.opencode/plugins/auto-commit.js` | **Create** | ~50 lines |
| `CLAUDE.md` | **Edit** (additive only) | +~80 lines |

---

## Context for Next Session

When picking this up in a new session, say:
> "Execute the OpenCode setup plan at `docs/plans/opencode-setup-plan.md`"

The plan is self-contained. Start with Phase 1 (`opencode.json`), then Phase 2 (agents), then Phase 3 (plugins), then Phase 4 (CLAUDE.md edits).

**Do NOT modify existing content in CLAUDE.md — additive insertions only.**
