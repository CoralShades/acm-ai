# Claude Code Best Practices Playbook

> **Authoritative reference** synthesizing Anthropic's official docs, Boris Cherny's (creator of Claude Code) personal workflow, and GritAI Studio's analysis. Optimized for human scanning and AI agent context injection.
>
> **Sources:** `[Official]` = Anthropic docs · `[Boris]` = Boris Cherny's workflow · `[Video]` = GritAI Studio breakdown
>
> **Last updated:** March 2026

---

## 1. THE ONE CONSTRAINT: CONTEXT WINDOW

Everything flows from this: **context fills fast, performance degrades as it fills.** Every technique below is a context management strategy. `[Official]`

- 200K token default window. 1M beta available (Opus 4.6 / Sonnet 4.6). `[Official]`
- Window holds: conversation history + file contents + command outputs + CLAUDE.md + loaded skills + auto memory `[Official]`
- Quality degrades as older context gets compressed — don't rely on early instructions in long sessions `[Official]`
- Track usage: `/status` or customize statusline to always show context `[Boris]`
- `/clear` between unrelated tasks — non-negotiable `[Official]`
- `/compact <instructions>` for controlled summarization: `/compact Focus on the API changes` `[Official]`
- Manual summarization beats autocompact — you control what survives `[Video]`
- Partial compaction: `Esc+Esc` or `/rewind` → select message → "Summarize from here" `[Official]`
- Customize compaction survival in CLAUDE.md: `"When compacting, always preserve the full list of modified files and any test commands"` `[Official]`

### Parallel Sessions

- **Run 5–10 parallel sessions.** Plan in one, review in another, implement in a third. `[Boris]`
- Use 3–5 Git worktrees or checkouts for separate branches `[Boris]`
- Each worktree = own directory + own branch + shared repo history `[Official]`
- Think of AI as **capacity you can schedule**, not a single conversational tool `[Boris]`
- Fresh context improves code review — Claude won't be biased toward code it just wrote `[Official]`

### Writer/Reviewer Pattern `[Official]`

- Session A writes code → Session B reviews it (clean eyes)
- Session A writes tests → Session B writes code to pass them
- Prevents self-confirmation bias

---

## 2. VERIFICATION: HIGHEST LEVERAGE

> **The single highest-leverage thing you can do.** `[Official]` `[Boris]`

Without verification → one shot, hope it works, bugs found manually
With verification → **self-correcting loop**, Claude writes/tests/fixes iteratively

### Three Verification Strategies `[Official]`

1. **Test cases** — write tests, run them, iterate until pass
2. **Visual verification** — Claude-in-Chrome extension for UI testing `[Boris]`
3. **Root cause fixing** — Claude traces + fixes, not just patches

### The "Go Fix It" Pattern `[Boris]`

- When something breaks: don't over-explain. Say **"go fix it"**
- Trust the verification loop you set up
- Claude fixes most bugs by itself when it has tests to run against

### Verification is Non-Negotiable `[Boris]`

- Nothing ships without verification
- If you can't verify it, **don't ship it** `[Official]`

### Do-This / Not-This: Verification Prompts

| ❌ Not This | ✅ Do This |
|---|---|
| "Add a login page" | "Add a login page. Write tests for email validation, wrong password, and successful login. Run the tests and make sure they pass." |
| "Refactor the database module" | "Refactor the database module to use connection pooling. Run `npm test` after each change. All 47 existing tests must still pass." |
| "Fix the CSS layout" | "Fix the sidebar overlapping main content on mobile. Verify no element wider than 100vw exists using `document.querySelector` in the browser console." |

---

## 3. THE WORKFLOW: EXPLORE → PLAN → IMPLEMENT → COMMIT

Four steps, every time for non-trivial tasks. `[Official]`

### Step 1: Explore

- Read relevant code. Understand current state. **Don't change anything yet.**
- `> Read src/auth/ and explain how the login flow works today. Don't change anything yet.`

### Step 2: Plan

- `Shift+Tab` twice → plan mode (read-only guarantees) `[Official]`
- Propose plan. Review it. Iterate until solid. `[Boris]`
- `> Write a plan for adding OAuth. Which files need to change? What's the order of operations? Don't implement yet.`
- Press `Ctrl+G` to open plan in your text editor for direct editing `[Official]`

### Step 3: Implement

- Exit plan mode → switch to auto-accept (`Shift+Tab`) `[Boris]`
- Claude executes the agreed plan with verification
- `> Implement the plan. After each file, run the test suite. Don't move on until all tests pass.`

### Step 4: Commit

- Let Claude write commit message — it saw every change
- Large diffs → ask Claude to split into logical commits
- `> Commit with a clear message. If changes are large, split into separate logical commits.`

### When to Skip Planning `[Official]`

- If you could describe the diff in one sentence → skip it
- Fixing a typo, adding a log line, renaming a variable → just do it directly
- **Complex tasks: always start in plan mode, no exceptions** `[Boris]`

### Re-entering Plan Mode `[Video]`

- If Claude starts derailing or getting stuck mid-implementation → go back to plan mode
- Multiple team members confirm this recovery pattern

---

## 4. PROMPTING: BE SPECIFIC

Vague prompts waste tokens on guessing. Specific prompts get Claude to the right place immediately. `[Official]`

### Do-This / Not-This: Prompt Specificity

| Category | ❌ Not This | ✅ Do This |
|---|---|---|
| **Scope** | "Improve the API" | "Add rate limiting to POST /api/users. 100 req/min/IP. Return 429 with retry-after header." |
| **Sources** | "Write a migration script" | "Write a migration from `db/v1.sql` to `db/v2.sql`. Handle `user.role` column becoming a separate `roles` table." |
| **Patterns** | "Add error handling" | "Add error handling following the pattern in `src/api/orders.ts`. Use `AppError` class. Log to Sentry. Return standard error shapes." |
| **Symptoms** | "The app crashes sometimes" | "App crashes loading dashboard after login. Stack trace points to `useEffect` in `Dashboard.tsx:47`. Only when user has no recent orders." |

### Input Methods `[Official]`

- **@-references** — `@filename` adds file to context. `@https://...` fetches URL content
- **Images** — drag-and-drop screenshots, mockups, error messages. Claude reads natively
- **Pipes** — `git diff main | claude "Review this diff for bugs"`
- **Pipes** — `npm test 2>&1 | claude "Fix the failing tests"`
- **Bash commands** — Claude can pull context itself via bash, MCP tools, file reads

### Advanced Prompting Techniques

- **Use voice dictation.** 3x faster than typing → prompts get way more detailed. macOS: fn key twice. `[Video]`
- **Specs reduce corrections.** Write detailed specs before handing work off. `[Video]`
- **Make Claude your reviewer.** "Grill me on these changes and don't make a PR until I pass your test." `[Video]`
- **Have Claude diff.** Compare main vs feature branch for review. `[Video]`
- **Delegating style.** Give context + direction, trust Claude to figure out details: `[Official]`
  - `> The checkout flow is broken for users with expired cards. The relevant code is in src/payments/. Investigate and fix it.`
  - Don't specify which files to read or commands to run — Claude figures it out

---

## 5. CLAUDE.md: YOUR PROJECT BRAIN

Markdown file at project root → Claude reads at start of **every** session. Write it like onboarding notes for a brilliant new hire. `[Official]`

### What to Include `[Official]`

- Bash commands Claude can't guess (build, test, lint, deploy)
- Code style rules that differ from defaults
- Testing instructions + preferred test runners
- Repo etiquette: branch naming, PR conventions
- Architectural decisions + common gotchas
- Verification commands: `"After editing TypeScript files, always run tsc --noEmit"` `[Video]`

### What to Exclude `[Official]`

- Anything Claude can figure out by reading code
- Standard language conventions Claude already knows
- Detailed API docs (link instead)
- Info that changes frequently
- Long tutorials or file-by-file descriptions

### Location Hierarchy `[Official]`

| Location | Scope | Auto-loaded? |
|---|---|---|
| `./CLAUDE.md` | Project root | ✅ Every session in this project |
| `~/.claude/CLAUDE.md` | User global | ✅ Every project ("always use TypeScript") |
| `./subdir/CLAUDE.md` | Subdirectory | ✅ When Claude works in that directory |

### Critical Rules

- **Keep under 500 lines.** If Claude ignores a rule → file too long, rule is lost. `[Official]`
- **Prune ruthlessly.** If Claude already does it correctly without the instruction → delete it or convert to hook. `[Official]`
- **Use @-references for imports.** `@docs/api-patterns.md` keeps main CLAUDE.md clean. `[Official]`
- **Use emphasis sparingly.** `IMPORTANT:` and `**bold**` carry more weight for critical rules. `[Video]`
- **Run `/init` on ANY project** — even existing ones. Analyzes codebase, detects build systems, test frameworks, code patterns. Good starting point. `[Video]`

### Boris's Golden Rule `[Boris]`

> After every correction, end your prompt with: **"update your CLAUDE.md so you don't make that mistake again."**
> This turns every mistake into a permanent improvement. Compound engineering.

### Team CLAUDE.md `[Boris]`

- Entire team contributes, multiple times weekly
- Code review → tag Claude to update guidelines automatically
- Use `/install-github-app` for automated PR reviews
- Treat CLAUDE.md as **living document** that compounds value

### Vercel Benchmark Insight `[Video]`

- 56% of eval cases: skill was **never invoked** even though available
- Embedding compressed doc index directly into CLAUDE.md → **100% pass rate**
- Skills alone maxed at 79% even with explicit instructions
- Compressed 40KB of docs → 8KB (80% reduction) while maintaining 100% pass rate
- **Takeaway:** Critical info belongs in CLAUDE.md, not hidden in skills

---

## 6. CLAUDE.md STARTER TEMPLATE

```markdown
# Project Name

## Build & Run
- Dev: `npm run dev`
- Build: `npm run build`
- Test: `npm test` (vitest)
- Lint: `npm run lint` (eslint + prettier)
- Type check: `tsc --noEmit`

## Code Style
- Functional components, no classes
- Zod for validation
- ES modules, not CommonJS
- Error handling: use `AppError` class (see `src/utils/errors.ts`)

## Architecture
- State management: Zustand (`src/stores/`)
- API layer: tRPC (`src/server/api/`)
- Database: Prisma + PostgreSQL
- Auth: NextAuth.js

## Verification — IMPORTANT
- After editing TypeScript files, ALWAYS run `tsc --noEmit`
- After ANY code change, run `npm test`
- Before committing, run `npm run lint`

## Git Conventions
- Branch naming: `feat/`, `fix/`, `chore/`
- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`
- PR must pass CI before merge

## Common Gotchas
- The `user.role` field is deprecated — use `roles` table via `getUserRoles()`
- API routes in `src/pages/api/` are legacy — new routes go in `src/server/api/routers/`
- Environment variables: check `.env.example` — never commit `.env`

## When Compacting
Always preserve: modified file list, test commands, architectural decisions made this session.
```

---

## 7. SKILLS: ON-DEMAND EXPERTISE

CLAUDE.md = always loaded. Skills = loaded only when invoked. Keeps base context clean. `[Official]`

### Two Types `[Video]`

1. **Auto-invoked domain knowledge** — Claude applies when working in relevant areas
2. **Workflow skills** — invoke with `/skill-name` for repeatable multi-step processes

### Creating Skills `[Official]`

```
.claude/skills/review.md
```

```markdown
---
name: code-review
description: Review staged changes for issues
---

Review the staged changes. Check for:
1. Security issues (injection, auth bypass)
2. Performance regressions
3. Missing tests for new logic
4. Style guide violations per CLAUDE.md
```

Invoke: `/review`

### Skill Best Practices

- Create your own skills, commit to Git, reuse across projects `[Boris]`
- Any pattern you repeat → make it a skill `[Boris]`
- Use `disable_model_invocation: true` for workflows that should only trigger manually `[Video]`
- Built-in skills: `/docx`, `/xlsx`, `/pptx`, `/pdf` for document creation `[Video]`
- Team builds learning-focused skills: spaced repetition where you explain understanding → Claude fills gaps `[Boris]`

### Skills vs CLAUDE.md `[Video]`

- Critical info → CLAUDE.md (always loaded, 100% invocation)
- Specialized workflows → Skills (on-demand, ~79% invocation even with explicit instructions)
- Compressed index of skills in CLAUDE.md → best of both worlds

---

## 8. PLUGINS `[Official]`

Next evolution beyond skills. Packaged extensions installable from marketplaces. Think npm for Claude Code.

- `/plugin` — browse marketplace
- Plugins bundle: skills + hooks + subagents + MCP servers
- Launched December 2025 with 36 curated plugins
- Code intelligence plugins: precise symbol navigation + automatic error detection after edits
- Auto-updates available per marketplace

```bash
# Install
/plugins install typescript-lsp

# List installed
/plugins list

# Update all
/plugins update
```

---

## 9. SUBAGENTS: ISOLATED CONTEXT

Separate Claude instances with own context window. Only summary returns to parent. `[Official]`

### When to Use `[Official]`

- Deep file exploration that would pollute main context
- Parallel investigation (multiple subagents simultaneously)
- Verification after implementation
- Tasks where only the result matters, not the process

### Usage

- Append **"use subagents"** to any request for more compute `[Boris]`
- `> Use subagents to investigate how our auth system handles token refresh`
- `/subagents` — view available, create new ones `[Official]`

### Boris's Specialized Subagents `[Boris]`

| Role | Purpose |
|---|---|
| Code Simplifier | Cleanup and simplification |
| Verify App | End-to-end testing |
| Build Validator | Ensure builds pass |
| Code Architect | Design decisions |

Think of them as team members with distinct responsibilities.

---

## 10. AGENT TEAMS `[Official]`

Beyond subagents. Multiple independent Claude instances that coordinate with each other.

### Subagents vs Agent Teams `[Official]`

| | Subagents | Agent Teams |
|---|---|---|
| **Context** | Own window; results return to caller | Own window; fully independent |
| **Communication** | Report back to main agent only | Teammates message each other directly |
| **Coordination** | Main agent manages all work | Shared task list with self-coordination |
| **Best for** | Focused tasks where only result matters | Complex work requiring discussion/collaboration |
| **Token cost** | Lower (results summarized) | Higher (each teammate = separate instance) |

### When to Use Agent Teams

- Parallel exploration adds real value
- Teammates need to share findings, challenge each other
- Debate structure: multiple investigators actively trying to disprove each other's theories `[Official]`

### Usage

```bash
# Start agent team from prompt
> Spawn 5 agent teammates to investigate different hypotheses.
> Have them talk to each other to try to disprove each other's theories.

# Monitor
/tasks
```

- Teammates load project context automatically (CLAUDE.md, MCP, skills) but NOT lead's conversation history `[Official]`

---

## 11. THE INTERVIEW TECHNIQUE

Have Claude interview you BEFORE coding. Produces better specs than you'd write alone. `[Official]` `[Boris]`

### Pattern

1. Start with minimal prompt: `"I want to add a notification system. Interview me about the requirements, then write a spec."`
2. Claude uses `AskUserQuestion` tool to ask targeted questions `[Official]`
3. Claude asks about: implementation details, edge cases, trade-offs, UI/UX you hadn't considered
4. Result: comprehensive spec

### Critical Follow-Up `[Boris]`

- **Start a FRESH session to execute the spec.** Don't implement in the interview session.
- Clean context → focused entirely on implementation
- The spec becomes input for the next session

### Beyond Coding `[Video]`

- Use for architecture decisions, documentation planning, API design
- "You can use this for so much more than coding"

---

## 12. HOOKS: DETERMINISTIC AUTOMATION `[Official]`

Hooks = deterministic control over Claude's behavior. Always happen, not reliant on LLM choice.

### Three Types `[Official]`

| Type | How it works | Use case |
|---|---|---|
| **Command hooks** | Run shell command, exit code controls flow | Formatting, linting, context injection |
| **Prompt hooks** | Single LLM call to evaluate condition | Completeness checks |
| **Agent hooks** | Spawn subagent that can read files + use tools | Complex verification |

### Hook Events `[Official]`

- `SessionStart` — runs when session begins (or after compaction with `compact` matcher)
- `PreToolUse` — runs before Claude uses a tool (can block with exit 2)
- `PostToolUse` — runs after tool execution
- `UserPromptSubmit` — runs when user sends a message
- `Stop` — runs when Claude finishes (can force Claude to keep working)

### Practical Examples

**Auto-format after every edit:** `[Video]`
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "write|edit",
      "hooks": [{
        "type": "command",
        "command": "prettier --write $CLAUDE_FILE_PATH"
      }]
    }]
  }
}
```

**Re-inject context after compaction:** `[Official]`
```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "compact",
      "hooks": [{
        "type": "command",
        "command": "echo 'Reminder: use Bun, not npm. Run bun test before committing. Current sprint: auth refactor.'"
      }]
    }]
  }
}
```

**Auto-completeness check on stop:** `[Official]`
```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "prompt",
        "prompt": "Check if all tasks are complete. If not, respond with {\"ok\": false, \"reason\": \"what remains to be done\"}."
      }]
    }]
  }
}
```

### Hook Flow Control `[Official]`

- Exit 0 → action proceeds (stdout added to context)
- Exit 2 → action blocked (stderr sent to Claude as feedback)
- Any other exit → action proceeds (stderr logged, not shown to Claude)

---

## 13. AUTO MEMORY (MEMORY.md) `[Official]`

Claude saves learnings automatically as you work — project patterns, preferences.

- First 200 lines of `MEMORY.md` loaded at session start
- Separate from CLAUDE.md — auto-generated vs human-curated
- Sessions are ephemeral — Claude doesn't learn preferences over time UNLESS captured in CLAUDE.md or MEMORY.md `[Video]`
- Put persistent knowledge in CLAUDE.md, let auto memory capture patterns

---

## 14. MODEL CONFIGURATION `[Official]`

### Model Aliases

| Alias | Use |
|---|---|
| `opus` | Best reasoning, highest quality |
| `sonnet` | Fast, efficient coding |
| `opusplan` | **Hybrid: Opus for planning, Sonnet for execution** |
| `sonnet[1m]` / `opus[1m]` | 1M context window variants (beta) |

### The opusplan Alias `[Official]`

- Plan mode → Opus (complex reasoning, architecture)
- Execution mode → automatically switches to Sonnet (code generation)
- Best of both worlds: reasoning quality + execution efficiency

### Boris on Model Selection `[Boris]`

- **Always use the latest/best model** (currently Opus 4.6)
- Optimize for **cost per reliable change**, not cost per token
- Correction tax of weaker models' hallucinations costs MORE than the model premium
- "The 80% that work more than compensate" for the cost

### Effort Levels (Opus 4.6) `[Official]`

- `low` / `medium` / `high` (default)
- Lower = faster + cheaper for straightforward tasks
- Higher = deeper reasoning for complex problems
- Set via: `/model` slider, `CLAUDE_CODE_EFFORT_LEVEL` env var, or settings file

### 1M Context Window (Beta) `[Official]`

- Available for Opus 4.6 and Sonnet 4.6
- Standard rates up to 200K → long-context pricing beyond
- Enable: `/model sonnet[1m]` or `/model claude-sonnet-4-6[1m]`
- Disable: `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`
- Still follow context management tips even with 1M — keeps Claude focused

---

## 15. REMOTE SESSIONS & MOBILITY `[Official]`

### Claude Code on the Web

- Runs on Anthropic's secure cloud infrastructure in isolated VMs
- Push tasks remotely: `claude --remote "Fix the flaky test in auth.spec.ts"`
- Multiple `--remote` commands run in parallel, independently
- Monitor with `/tasks`

### Teleport `[Official]`

- Move sessions between environments: web ↔ terminal ↔ desktop ↔ mobile
- "Open in CLI" from web → copies command to paste in terminal
- `/teleport` — pull remote session into terminal
- `/desktop` — hand off to Desktop app for visual diff review
- Verifies correct repo, fetches branch, loads full conversation history

### Plan Locally, Execute Remotely `[Official]`

```bash
# Plan in local terminal (plan mode)
# Then send to cloud for autonomous execution
claude --remote "Implement the OAuth plan from docs/oauth-spec.md"
```

### Session Sharing `[Official]`

- Enterprise/Teams: Private or Team visibility
- Max/Pro: Private or Public visibility
- **Check for sensitive content before sharing** — sessions may contain code + credentials

---

## 16. SESSION MANAGEMENT

### Essential Commands

| Command / Key | Action | When to Use |
|---|---|---|
| `Esc` | Stop Claude mid-action | Heading wrong direction |
| `Esc Esc` | Rewind menu | Restore previous state |
| `/clear` | Reset context, reload CLAUDE.md | Between unrelated tasks |
| `/compact <instructions>` | Compress with controlled summarization | Context getting full |
| `/compact` (no args) | Auto-summarize | Quick context reduction |
| `"undo that"` | Revert Claude's changes | Quick correction |
| `--continue` | Resume last session | Pick up where you left off |
| `/resume` | Session picker | Switch between sessions |
| `/rename` | Name current session | Organization |
| `/rewind` | Checkpoint menu | Restore conversation/code/both |
| `/status` | Show context usage + account info | Check state |
| `/statusline` | Customize status bar | Always-visible context tracking `[Boris]` |
| `/context` | Check context usage | Monitor window |
| `/model <alias>` | Switch model mid-session | Change strategy |
| `/init` | Auto-generate CLAUDE.md | New or existing projects |
| `/permissions` | Pre-approve safe commands | Reduce interruptions |
| `/sandbox` | OS-level isolation | Security boundaries |
| `/config` | Settings including output style | Learning mode |
| `/plugin` | Browse plugin marketplace | Install extensions |
| `/subagents` | View/create subagents | Delegation |
| `/tasks` | Monitor remote sessions | Parallel work |
| `/install-github-app` | Auto PR reviews | CI integration |
| `Shift+Tab` | Toggle auto-accept mode | Implementation phase |
| `Shift+Tab Tab` | Enter plan mode | Research/planning phase |
| `Ctrl+G` | Open plan in text editor | Direct plan editing |
| `Ctrl+O` | Toggle verbose mode | Debug hooks |

### Session Lifecycle Tips

- Sessions are per-directory — `/resume` shows sessions from same git repo `[Official]`
- Give sessions descriptive names for later retrieval `[Official]`
- `/resume` picker: keyboard navigation, search, rename with `R` `[Official]`
- Conversation stored locally: full message history, tool usage, results `[Official]`
- Before changes: Claude snapshots affected files (auto-checkpoint) `[Official]`

---

## 17. FAILURE PATTERNS & FIXES

| Pattern | Symptom | Fix | Source |
|---|---|---|---|
| **Kitchen sink session** | One task → unrelated question → back to first. Context polluted with irrelevant info | `/clear` between unrelated tasks. Fork sessions. | `[Official]` |
| **Correction loop** | Wrong → correct → still wrong → correct again. Failed approaches fill context | After 2 failed corrections: `/clear` + rewrite prompt incorporating learnings | `[Official]` `[Video]` |
| **Overspecified CLAUDE.md** | Too long. Claude ignores half. Important rules lost in noise | Prune ruthlessly. Under 500 lines. Delete what Claude already does correctly. Convert to hooks. | `[Official]` |
| **Trust-then-verify gap** | Plausible code that doesn't handle edge cases | Always provide verification. Can't verify → don't ship. | `[Official]` |
| **Infinite exploration** | "Investigate X" without scope. Claude reads hundreds of files | Scope narrowly or use subagents | `[Official]` |
| **Sunk cost fallacy** | Pushing a dead session instead of starting fresh | Quick abandonment. Parallel sessions hedge against dead ends. **10–20% of sessions fail — that's normal.** | `[Boris]` |
| **Derailing mid-implementation** | Claude starts going off-track during coding | Re-enter plan mode. Realign on approach. | `[Video]` |

### Recovery Techniques

- After a mediocre fix: **"Knowing everything you know now, scrap this and implement the elegant solution."** Claude often finds better approaches once it understands the problem space. `[Video]`
- Save context to markdown file → `/clear` → start over with that file as input `[Video]`
- Parallel sessions: if one goes nowhere, another is progressing `[Boris]`

---

## 18. MCP (MODEL CONTEXT PROTOCOL) `[Official]`

Open standard connecting Claude Code to external data sources and tools.

- Read design docs in Google Drive
- Update tickets in Jira
- Pull data from Slack
- Custom tooling via MCP servers

```bash
# Add MCP server
claude mcp add brave-search -s project -- npx @modelcontextprotocol/server-brave-search
```

- Use official servers from Anthropic's site or build custom
- Scope with `--allowedTools` for batch operations

---

## 19. CI/CD & BATCH AUTOMATION `[Official]`

### Headless Mode

```bash
# Single query
claude -p "Analyze this file for security issues"

# Plan mode headless
claude -p --plan "Create a migration plan for React to Vue"

# Loop through tasks
for file in $(cat files.txt); do
  claude -p "Migrate $file from React to Vue. Follow the patterns in src/migrated/example.vue"
done
```

### GitHub Integration

- `/install-github-app` — automated PR reviews `[Boris]`
- `@claude` mention in PRs/issues → Claude analyzes, creates PRs, implements features `[Official]`
- Customize review prompt in `claude-code-review.yml` — default is too verbose `[Video]`

### Permissions & Security

- **Never use `--dangerously-skip-permissions` in production** `[Video]`
- `/permissions` — pre-approve specific safe commands `[Official]`
- `/sandbox` — OS-level isolation, upfront boundaries `[Official]`
- `claude allow "git commit"` — allowlist specific commands `[Official]`

---

## 20. RAPID-FIRE PRO TIPS

| # | Tip | Source |
|---|---|---|
| 1 | Install CLI tools (gh, aws, gcloud). Claude uses them without rate limits. | `[Video]` |
| 2 | `/init` on any project — even years-old ones. Surprisingly good CLAUDE.md starting point. | `[Video]` |
| 3 | `IMPORTANT:` and `**must**` in CLAUDE.md for critical rules. Use sparingly. | `[Video]` |
| 4 | CLAUDE.md can import files with `@docs/api-patterns.md`. Keep main file clean. | `[Official]` |
| 5 | Child directories get their own CLAUDE.md — loaded on demand per directory. Monorepo-friendly. | `[Official]` |
| 6 | Sessions are ephemeral. Claude doesn't learn over time. Persistent knowledge → CLAUDE.md. | `[Video]` |
| 7 | Always use latest model (Opus 4.6). Cost per reliable change > cost per token. | `[Boris]` |
| 8 | Any workflow repeated multiple times/day → `/skill` or slash command. Commit to Git. Reuse. | `[Boris]` |
| 9 | Post-tool-use hooks for auto-formatting. Catches last 10% without approval prompts. | `[Video]` |
| 10 | Enable explanatory/learning output styles in `/config`. Claude explains *why* behind changes. | `[Video]` |
| 11 | Have Claude generate visual HTML presentations explaining unfamiliar code. Makes great slides. | `[Video]` |
| 12 | Ask Claude to draw ASCII diagrams of new protocols/codebases. | `[Video]` |
| 13 | Build spaced repetition skill: explain understanding → Claude fills gaps → stores result. | `[Boris]` |
| 14 | Track context in statusline — keeps the constraint visible at all times. | `[Boris]` |
| 15 | Ask Claude questions you'd ask a senior engineer. Treat it like onboarding to a codebase. | `[Official]` |

---

## 21. THE META-LESSON

These patterns aren't laws. `[Official]`

- Sometimes **let context accumulate** — you're deep in a complex problem
- Sometimes **skip the plan** — task is exploratory
- Sometimes **use a vague prompt** — see how Claude interprets the problem
- Sometimes **be hyper-specific** — you know exactly what you want

> Pay attention to what works. Start with one technique. Use it for a week until automatic. Add another. Over time, you'll develop intuition no guide can capture. `[Official]`

> "The real skill is knowing what to delegate and when to step in. That takes practice, not rules." `[Boris]`

---

## SOURCE REFERENCE

| Tag | Source | URL |
|---|---|---|
| `[Official]` | Anthropic Claude Code Docs — Best Practices, Common Workflows, How It Works, Hooks, Agent Teams, Model Config | https://code.claude.com/docs/en/best-practices |
| `[Boris]` | Boris Cherny (creator of Claude Code) personal workflow | https://guides.gritai.studio/guides/boris-way.html |
| `[Video]` | GritAI Studio video breakdown by Alex | https://www.youtube.com/@GritAIStudio |
