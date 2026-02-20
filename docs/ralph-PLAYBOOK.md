# System Prompt Repos × BMAD V6 × Ralph Loop — Universal Playbook

> **What this is:** A complete, project-agnostic guide to leveraging leaked/open-source system prompts from production AI tools, combining them with the BMAD V6 methodology and Ralph autonomous coding loops, and running the whole thing on either cloud APIs or local open-source models via Ollama. Works for any tech stack, any project size.

---

## 1. The Problem This Solves

### The Repetitive Ralph Loop Setup Problem

Every time you start a new feature or epic, you go through the same expensive cycle in Claude Code CLI:

1. Prompt Claude Code to research 3-4 external repos (Ralph variants, BMAD skills, etc.)
2. Wait for it to read and understand those repos (burns context window)
3. Ask it to create a Ralph loop configuration based on those repos
4. Customize the loop for your specific story/epic
5. Finally start the actual implementation

This eats context window, costs tokens, burns time, and introduces inconsistency because each session interprets the repos slightly differently.

### What You Actually Need

- A **one-time setup** that bakes all the knowledge from those repos into your workflow permanently
- A **pre-built Ralph loop bootstrap** that already knows your project architecture
- System prompt patterns from production AI tools (Cursor, Devin, Replit, etc.) **already distilled** into your BMAD agent definitions
- The ability to run this on **local/open-source models** via Ollama when appropriate, saving cloud API tokens for complex work

---

## 2. The Source Repos — What They Are & What They Give You

### System Prompt Collections

| Resource | Stars | What It Gives You |
|---|---|---|
| [x1xhlol/system-prompts-and-models-of-ai-tools](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools) | 109k★ | Production system prompts from Cursor, Devin, Replit, Claude Code, v0, Lovable, Windsurf, Augment Code, Kiro, and 20+ more tools — how real products structure agentic coding |
| [asgeirtj/system_prompts_leaks](https://github.com/asgeirtj/system_prompts_leaks) | 31.7k★ | System prompts from ChatGPT, Claude, Gemini — conversational AI patterns, guardrails, output formatting, tool-use schemas |
| [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | — | Complete Claude Code system prompts deconstructed — every built-in tool, subagent prompt (Plan/Explore/Task), and utility prompt. Updated per version |

### BMAD & Ralph Tooling

| Resource | What It Does |
|---|---|
| [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | Official BMAD V6 — 12+ specialized agents, slash commands, full SDLC workflow |
| [aj-geddes/claude-code-bmad-skills](https://github.com/aj-geddes/claude-code-bmad-skills) | BMAD optimized for Claude Code — 9 skills, 15 commands, 70-85% token optimization |
| [snarktank/ralph](https://github.com/snarktank/ralph) | Original Ralph — autonomous AI agent loop until all PRD items are complete |
| [frankbria/ralph-claude-code](https://github.com/frankbria/ralph-claude-code) | Ralph with intelligent exit detection, monitoring dashboard, for Claude Code |
| [LarsCowe/bmalph](https://github.com/LarsCowe/bmalph) | Unified BMAD + Ralph — planning phases 1-3 then `/bmalph-implement` transitions to Ralph |
| [ClaytonFarr/ralph-playbook](https://github.com/ClaytonFarr/ralph-playbook) | Deep methodology guide — acceptance-driven backpressure, TDD workflow, sandbox security patterns |

### What to Extract from the System Prompt Repos

**From Cursor's Agent Prompt:**
- The "read files before guessing" pattern — forces codebase exploration before making changes
- The "parallel tool calls" optimization — running multiple file reads simultaneously
- Chunk-based file reading with signature-level exploration
- The linter/test feedback loop pattern

**From Devin AI's Prompt:**
- Planning-before-execution with explicit step tracking
- Browser + terminal + editor multi-tool coordination
- The `return_documents` completion protocol

**From Replit Agent:**
- Project scaffolding and dependency management patterns
- File-system-first approach to understanding project structure
- Deployment-aware development pattern

**From Claude Code's Own System Prompt (Piebald-AI repo):**
- The Plan/Explore/Task subagent architecture
- The "Skillify Current Session" pattern — turning ad-hoc work into reusable skills
- Compact/statusline management for long-running tasks

---

## 3. TODO List (Prioritized)

### Phase A: Foundation (Do Once, Benefit Forever)

- [ ] **A1.** Extract and distill the best patterns from the system prompt repos into a reusable Claude Code Skill
- [ ] **A2.** Create a project-specific `CLAUDE.md` that encodes your architecture, conventions, and repo structure
- [ ] **A3.** Build a pre-configured Ralph loop template tailored to your tech stack
- [ ] **A4.** Create a `/ralph-init` Claude Code Skill that bootstraps a Ralph loop from any BMAD story — no manual repo research needed
- [ ] **A5.** Set up Ollama with custom Modelfiles for routine dev tasks (save cloud tokens for planning/architecture)

### Phase B: Integration (Wire Everything Together)

- [ ] **B1.** Install and configure `bmalph` or equivalent BMAD+Ralph unified workflow
- [ ] **B2.** Create Claude Code Subagents for each repo or tech stack layer in your project
- [ ] **B3.** Set up Ollama Modelfiles with distilled system prompts for local code review, testing, and routine implementation
- [ ] **B4.** Create a project-level `.claude/agents/` directory with pre-built agent definitions
- [ ] **B5.** Configure `CLAUDE.md` files across all repos in a multi-repo project

### Phase C: Optimization (Make It Seamless)

- [ ] **C1.** Set up `claude-launcher` to seamlessly switch between Ollama (local/free) and cloud API (powerful)
- [ ] **C2.** Create Ralph loop variants per tech stack layer (e.g., `ralph-backend`, `ralph-frontend`, `ralph-mobile`)
- [ ] **C3.** Implement acceptance-driven backpressure patterns from the ralph-playbook for automated quality gates
- [ ] **C4.** Build a documentation auto-generation pipeline from BMAD artifacts
- [ ] **C5.** Evaluate if bmalph's spec changelog + fix_plan pattern integrates with your project management tool (Jira, Plane, Linear, etc.)

---

## 4. The Plan: Step-by-Step Execution

### STEP 1: Distill System Prompt Patterns into a Reusable Skill (Tasks A1, A4)

The system prompt repos are a goldmine, but you don't need to re-read them every session. Extract the patterns **once** and encode them as a Claude Code Skill.

Create `~/.claude/skills/{{your-project}}/dev-patterns/SKILL.md`:

```markdown
# {{PROJECT_NAME}} Development Patterns

## Skill ID
{{project-slug}}-dev-patterns

## Purpose
Distilled production patterns from Cursor, Devin, and Replit system prompts,
adapted for {{PROJECT_NAME}}'s architecture.

## Before Modifying Any File
1. ALWAYS read the file first — never guess at contents
2. Explore related files in parallel (use Task tool for parallel reads)
3. Check for existing tests, types, and interfaces that constrain your changes
4. Understand the import/dependency chain before touching anything

## Project Architecture Awareness
{{Describe your project architecture here. Examples:}}

### Example — Monorepo (Full-Stack Web App)
- **Backend**: Node.js/Express (TypeScript) — `/packages/api/`
- **Frontend**: React/Next.js (TypeScript) — `/packages/web/`
- **Shared**: Common types and utilities — `/packages/shared/`
- Changes to shared packages must be validated against ALL consumers

### Example — Multi-Repo (Microservices)
- **Service A**: Python/FastAPI — `repo: service-a`
- **Service B**: Go — `repo: service-b`
- **Gateway**: Node.js — `repo: api-gateway`
- **Mobile**: React Native — `repo: mobile-app`
- API contract changes must be coordinated across repos

### Example — Single Repo (SaaS Application)
- **Framework**: Rails 7 / Django / Laravel / Spring Boot
- **Frontend**: Hotwire / HTMX / Livewire / Thymeleaf
- **Database**: PostgreSQL with migrations
- **Background Jobs**: Sidekiq / Celery / Queues / Spring Batch

## Implementation Loop (Inspired by Cursor + Devin)
1. Read the story/task requirements completely
2. Explore the relevant codebase area (files, tests, related modules)
3. Plan the changes explicitly before writing code
4. Implement incrementally — one logical change at a time
5. Run tests/linting after each change
6. If tests fail, read the error, re-read the relevant file, fix, repeat
7. Commit with conventional commit messages

## Output Protocol
- After completing a task, explicitly state what was done and what tests pass
- If blocked, state the blocker clearly rather than guessing
- Output <promise>COMPLETE</promise> only when ALL acceptance criteria are met
```

---

### STEP 2: Build Your Project's CLAUDE.md (Task A2)

This is the single most impactful thing you can do. Place a `CLAUDE.md` in each repo root so Claude Code auto-loads your project context every session.

**Template:**

```markdown
# CLAUDE.md — {{PROJECT_NAME}} {{(repo-name if multi-repo)}}

## Project Overview
{{One paragraph describing the project, its purpose, and which part of the
system this repo represents.}}

## Tech Stack
- **Language**: {{e.g., TypeScript, Python, PHP, Dart, Go, Rust, Java}}
- **Framework**: {{e.g., Next.js, Django, Laravel, Flutter, Spring Boot}}
- **Database**: {{e.g., PostgreSQL, MySQL, MongoDB, Supabase}}
- **Testing**: {{e.g., Jest, Pytest, PHPUnit, Flutter Test, JUnit}}
- **Linting**: {{e.g., ESLint, Ruff, PHPStan, Dart Analyzer, Checkstyle}}
- **CI/CD**: {{e.g., GitHub Actions, GitLab CI, CircleCI}}

## Folder Structure
{{Describe key directories and their purpose — what goes where.}}

## Conventions
- {{Coding patterns: e.g., "Repository pattern for data access", "BLoC for state management"}}
- {{Naming: e.g., "kebab-case files, PascalCase components"}}
- {{Git: e.g., "Conventional commits, feature branches off develop"}}
- {{Testing: e.g., "Every endpoint gets a feature test", "Minimum 80% coverage"}}

## BMAD Context
- Planning artifacts live in `_bmad-output/planning-artifacts/`
- Stories are generated by the Scrum Master agent with full acceptance criteria
- Implementation follows the Developer agent patterns
- All PRD and architecture docs are the source of truth

## Ralph Loop Configuration
When running a Ralph loop on this repo:
- Max iterations: {{30 for typical stories, 50 for complex epics}}
- Completion promise: "COMPLETE"
- Test command: {{`npm test` / `pytest` / `php artisan test` / `flutter test` / `./gradlew test`}}
- Lint command: {{`npm run lint` / `ruff check .` / `./vendor/bin/phpstan` / `dart analyze`}}
- Commit after each successfully completed story
- Update progress.txt after each iteration

## Do NOT
- Modify files outside the current story scope
- Skip writing tests
- Ignore linter/analyzer errors
- Change database migrations/schemas without explicit approval in the story
- {{Add project-specific guardrails here}}
```

---

### STEP 3: Create the Ralph Bootstrap Skill (Task A3, A4)

This eliminates the repetitive "research repos and set up Ralph" pattern. One skill, one command, instant Ralph loops.

Create `~/.claude/skills/{{your-project}}/ralph-bootstrap/SKILL.md`:

```markdown
# Ralph Loop Bootstrap

## Skill ID
ralph-bootstrap

## Purpose
Instantly bootstrap a Ralph autonomous coding loop for any BMAD story or epic
without needing to research external repos each time.

## Commands
- `/ralph-init` — Initialize a Ralph loop for the current story
- `/ralph-epic` — Initialize a Ralph loop for an entire epic (multiple stories)

## When /ralph-init is invoked

### Step 1: Gather Context
- Read the current story file from `_bmad-output/planning-artifacts/`
  (or wherever your BMAD stories are stored)
- Parse acceptance criteria into a checklist
- Identify which repo(s) are affected
- Read CLAUDE.md for project conventions

### Step 2: Generate the Ralph directory structure
```bash
mkdir -p .ralph/logs .ralph/specs
```

### Step 3: Generate @fix_plan.md
Create `.ralph/@fix_plan.md`:
```
# Fix Plan: [Story Title]
## Source: [story file path]
## Generated: [timestamp]

### Tasks
- [ ] Task 1: [derived from acceptance criterion 1]
- [ ] Task 2: [derived from acceptance criterion 2]
- [ ] Task N: [derived from acceptance criterion N]

### Completion Criteria
- All tasks checked off
- All tests passing (`{{TEST_COMMAND}}`)
- No linter errors (`{{LINT_COMMAND}}`)
- Code committed with conventional commit message
```

### Step 4: Generate PROMPT.md
Create `.ralph/PROMPT.md`:
```
You are implementing a feature for {{PROJECT_NAME}}.
Read @fix_plan.md for your current tasks.
Read CLAUDE.md in the project root for conventions and architecture.

RULES:
1. Pick the next unchecked task
2. Implement it following the patterns in CLAUDE.md
3. Run tests: {{TEST_COMMAND}}
4. Run linter: {{LINT_COMMAND}}
5. If tests pass, check off the task in @fix_plan.md and commit
6. If tests fail, fix and retry (max 3 retries per task)
7. Output <promise>COMPLETE</promise> when all tasks are done
8. Output <promise>BLOCKED</promise> if you cannot proceed

NEVER skip tests. NEVER mark a task complete without verification.
```

### Step 5: Generate ralph_loop.sh
Create `.ralph/ralph_loop.sh`:
```bash
#!/bin/bash
TOOL="${1:---tool claude}"
MAX_ITERATIONS="${2:-30}"
COMPLETION_PROMISE="COMPLETE"

for i in $(seq 1 $MAX_ITERATIONS); do
  echo "=== Ralph Iteration $i of $MAX_ITERATIONS ==="

  # Run Claude Code with the prompt
  claude --print --prompt-file .ralph/PROMPT.md $TOOL

  # Check if complete
  if grep -q "COMPLETE" .ralph/logs/iteration-$i.log 2>/dev/null; then
    echo "✅ Ralph completed all tasks in $i iterations"
    exit 0
  fi

  # Check if blocked
  if grep -q "BLOCKED" .ralph/logs/iteration-$i.log 2>/dev/null; then
    echo "🚫 Ralph is blocked. Check logs for details."
    exit 1
  fi
done

echo "⚠️ Ralph hit max iterations ($MAX_ITERATIONS)"
exit 2
```

### Step 6: Start the loop
```bash
chmod +x .ralph/ralph_loop.sh
.ralph/ralph_loop.sh --tool claude 30
```

## When /ralph-epic is invoked
Same as above but:
- Read ALL stories for the epic
- Generate a multi-story fix_plan.md with story-level grouping
- Track completion per-story with git tags
- Use `SPECS_CHANGELOG.md` to track what changed between runs
```

---

### STEP 4: Set Up Ollama for Local/Free Development (Task A5, B3)

#### 4a. Install Ollama and Pull Models

```bash
# Install Ollama (v0.14+ required for Anthropic API compatibility)
curl -fsSL https://ollama.com/install.sh | sh

# Pull recommended coding models
ollama pull qwen3-coder          # Great general coding model
ollama pull glm-4.7-flash        # 30B MoE, only 3B active — very fast
ollama pull gpt-oss              # 128k context, good for analysis
```

#### 4b. Create a Project-Specific Modelfile

```dockerfile
# ~/ollama-models/Modelfile.{{project-slug}}
FROM qwen3-coder

SYSTEM """
You are a senior developer working on {{PROJECT_NAME}}.

Tech Stack:
{{List your stack here, e.g.:}}
- Python 3.12 / FastAPI / SQLAlchemy / Alembic
- React 19 / Next.js 15 / TypeScript / Tailwind
- PostgreSQL / Redis / Docker

Rules:
- Always read files before modifying them
- Run tests after every change
- Follow existing code patterns and conventions
- Write clear, conventional commit messages
- Never guess — if unsure, state what information you need

You have tool-calling capabilities. Use them to read files,
run commands, and verify your work.
"""

PARAMETER temperature 0.2
PARAMETER num_ctx 65536
```

Build and use:
```bash
ollama create {{project-slug}}-dev -f ~/ollama-models/Modelfile.{{project-slug}}
ollama run {{project-slug}}-dev  # Interactive test
```

#### 4c. Connect to Claude Code

```bash
# Set environment variables (add to ~/.bashrc or ~/.zshrc for persistence)
export ANTHROPIC_AUTH_TOKEN="ollama"
export ANTHROPIC_API_KEY=""
export ANTHROPIC_BASE_URL="http://localhost:11434"

# Launch Claude Code with your local model
claude --model {{project-slug}}-dev
```

Or use `claude-launcher` for one-command switching:
```bash
npm install -g claude-launcher
claude-launcher -l  # Local (Ollama) — free, private
claude-launcher -a  # Anthropic (cloud) — powerful, paid
```

#### 4d. Recommended Models by Task

| Task | Model | Why |
|---|---|---|
| Routine story implementation | `qwen3-coder` (local) or `glm-4.7-flash` | Good coding, fast, free |
| Complex architecture decisions | Claude Opus/Sonnet (cloud) | Best reasoning, worth the cost |
| Code review & analysis | `gpt-oss` (local) | 128k context, good at analysis |
| Ralph loops (simple stories) | `qwen3-coder` (local) | Free autonomous iteration |
| Ralph loops (complex epics) | Claude Sonnet/Opus (cloud) | Better long-range coherence |
| Quick bug fixes & one-offs | `glm-4.7-flash` (local) | 3B active params = very fast |
| Large model without local GPU | `qwen3-coder:480b-cloud` (Ollama Cloud) | Offloaded to Ollama servers |

#### 4e. Hardware Guidelines

| Setup | What You Can Run |
|---|---|
| 8GB RAM (CPU only) | Small models only — very slow, not recommended for Ralph |
| 16GB RAM / Apple Silicon | `glm-4.7-flash` (tight), basic coding tasks |
| 32GB RAM / Apple Silicon | `qwen3-coder`, `glm-4.7-flash` — comfortable for Ralph loops |
| 64GB+ RAM or dedicated GPU | Most open-source models, good Ralph loop performance |
| Any machine + internet | Ollama Cloud models (free tier available) |

---

### STEP 5: Wire BMAD + Ralph + System Prompts Together (Tasks B1, B2, B4)

#### Option A: Use `bmalph` (Unified BMAD + Ralph)

Cleanest approach — single tool manages the entire lifecycle:

```bash
cd your-project
bmalph init --name your-project
```

Workflow:
1. `/analyst` → Product brief (Phase 1)
2. `/pm` → PRD (Phase 2)
3. `/architect` → Architecture + stories (Phase 3)
4. `/bmalph-implement` → Auto-generates `@fix_plan.md` and transitions to Ralph (Phase 4)
5. `bash .ralph/ralph_loop.sh` → Autonomous implementation

When you add more epics:
```
BMAD (Epic 1) → /bmalph-implement → Ralph works on Epic 1
       ↓
BMAD (add Epic 2) → /bmalph-implement → Ralph sees changes + picks up Epic 2
```

Completed stories are preserved in the fix plan via smart merge.

#### Option B: BMAD Skills + Custom Ralph Bootstrap (More Control)

Keep your existing BMAD V6 setup and add the Ralph bootstrap skill from Step 3:
1. BMAD phases 1-3 work as they do now
2. When ready to implement, use `/ralph-init` (your custom skill)
3. The skill auto-generates everything Ralph needs from your BMAD story artifacts
4. Launch the loop — no repo research needed

#### Create Stack-Specific Subagents

Define subagents in `~/.claude/agents/` for each layer of your project:

**Template:**
```markdown
# ~/.claude/agents/{{stack-layer}}-developer.md
---
name: {{stack-layer}}-developer
description: {{PROJECT_NAME}} {{stack description}} specialist
skills:
  - {{project-slug}}-dev-patterns
  - ralph-bootstrap
---
You are a senior {{technology}} developer working on {{PROJECT_NAME}}'s {{component}}.

You follow:
- {{Convention 1}}
- {{Convention 2}}
- {{Convention 3}}
- {{Testing approach}}
- {{Linting/quality standard}}

Read CLAUDE.md in the project root for full conventions.
```

**Example — Backend (Python/FastAPI):**
```markdown
---
name: backend-developer
description: API service specialist
skills:
  - dev-patterns
  - ralph-bootstrap
---
You are a senior Python developer working on the API service.

You follow:
- Clean Architecture with dependency injection
- Pydantic models for all request/response schemas
- Alembic for database migrations
- Pytest with 80%+ coverage requirement
- Ruff for linting, mypy for type checking

Read CLAUDE.md in the project root for full conventions.
```

**Example — Frontend (React/Next.js):**
```markdown
---
name: frontend-developer
description: Web application specialist
skills:
  - dev-patterns
  - ralph-bootstrap
---
You are a senior React/Next.js developer working on the web application.

You follow:
- Server Components by default, Client Components only when needed
- Tailwind CSS for styling, no CSS modules
- React Query for server state, Zustand for client state
- Vitest + Testing Library for tests
- ESLint + Prettier enforced

Read CLAUDE.md in the project root for full conventions.
```

**Example — Mobile (Flutter):**
```markdown
---
name: mobile-developer
description: Mobile app specialist
skills:
  - dev-patterns
  - ralph-bootstrap
---
You are a senior Flutter developer working on the mobile application.

You follow:
- BLoC pattern for state management
- Feature-first folder organization
- Widget tests + integration tests
- Material 3 design system
- Dart analysis options strict mode

Read CLAUDE.md in the project root for full conventions.
```

**Example — DevOps/Infra:**
```markdown
---
name: infra-developer
description: Infrastructure and deployment specialist
skills:
  - dev-patterns
---
You are a senior DevOps engineer managing infrastructure.

You follow:
- Infrastructure as Code (Terraform/Pulumi)
- Docker multi-stage builds
- GitHub Actions for CI/CD
- Environment parity (dev = staging ≈ prod)
- Secrets managed via Vault/SSM, never in code

Read CLAUDE.md in the project root for full conventions.
```

---

### STEP 6: The Complete Workflow (After Setup)

**BEFORE (repetitive, token-hungry):**
```
1. Open Claude Code CLI
2. "Research these 3-4 repos: [paste URLs]"
3. Wait while Claude reads everything (burns context window)
4. "Now create a Ralph loop based on those repos for this story"
5. Wait while Claude synthesizes (more context burned)
6. Review and fix the generated config
7. Finally start implementing
```

**AFTER (instant, consistent):**
```
1. Open Claude Code CLI in your repo
2. CLAUDE.md auto-loads your project context
3. /ralph-init   (or /bmalph-implement if using bmalph)
4. The skill instantly generates fix_plan.md + PROMPT.md from your BMAD story
5. Ralph starts implementing immediately
```

**For local/cost-saving runs:**
```
claude-launcher -l   # Switch to Ollama (free)
/ralph-init          # Same skill, same workflow, local model
```

**For complex work:**
```
claude-launcher -a   # Switch to Anthropic cloud (powerful)
/ralph-init          # Same skill, now powered by Opus/Sonnet
```

---

## 5. Leveraging System Prompt Patterns — Platform-Specific Guides

### Ollama (Local Inference)

- **Modelfiles** bake your system prompt into the model permanently — create once, use forever
- **Ollama Cloud** models (e.g., `qwen3-coder:480b-cloud`) give you large models without local GPU
- **Pre-release Ollama** (0.14.3-rc1+) is needed for full tool-use support that Ralph requires
- **Context window**: Set `OLLAMA_CONTEXT_LENGTH=65536` or higher — Claude Code recommends 64k minimum
- **API compatibility**: Ollama v0.14+ speaks the Anthropic Messages API natively — no shims needed

### Hugging Face

- **Fine-tuning**: Use distilled system prompts as training data for LoRA adapters on smaller models
- **Project-specific models**: Fine-tune on your codebase + system prompt patterns for a model that already "knows" your conventions
- **Datasets**: The system prompt repos can be structured as HF datasets for community sharing
- **Inference Endpoints**: Use HF as an alternative backend to Ollama for cloud inference
- **Direct to Ollama**: `ollama pull hf.co/Qwen/Qwen3-Coder-8B-GGUF` — pull HF models directly

### Kaggle

- **Free GPU access** (T4/P100) — ideal for benchmarking and fine-tuning experiments
- **Benchmarking**: Test different open-source models against your Ralph loop to find the best fit
- **Prompt length testing**: Some models degrade with very long system prompts — test systematically
- **LoRA training**: Use Kaggle's free GPU hours for fine-tuning smaller models with your conventions

### Claude Code + Anthropic API (Cloud)

- **Best for**: Complex architecture decisions, multi-file refactors, initial BMAD planning phases
- **Claude Max subscription**: Unlimited usage for planning and complex implementation
- **Subagents**: Use Claude Code's native subagent system for parallel work across repos
- **Agent Teams** (experimental): `export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` for multi-agent collaboration

### Project Management Integration

- System prompt patterns from the repos (especially Notion AI) show how PM-oriented AI assistants are structured
- Adapt these patterns to build custom AI integrations for your PM tool (Jira, Plane, Linear, etc.)
- BMAD agents can be configured to generate stories in your PM tool's format directly

---

## 6. Key Repos Quick Reference

| Repo | Install Command | Purpose |
|---|---|---|
| `bmad-code-org/BMAD-METHOD` | `npx bmad-method install` | Official BMAD V6 |
| `aj-geddes/claude-code-bmad-skills` | `./install-v6.sh` | BMAD optimized for Claude Code |
| `frankbria/ralph-claude-code` | Copy `ralph.sh` to project | Ralph CLI for Claude Code |
| `snarktank/ralph` | Copy `ralph.sh` + `CLAUDE.md` to project | Original Ralph (Amp + Claude Code) |
| `LarsCowe/bmalph` | `bmalph init` | Unified BMAD + Ralph |
| `ClaytonFarr/ralph-playbook` | Reference only | Methodology deep-dive |
| `x1xhlol/system-prompts-and-models-of-ai-tools` | Clone and browse | System prompt patterns (109k★) |
| `asgeirtj/system_prompts_leaks` | Clone and browse | ChatGPT/Claude/Gemini prompts (31.7k★) |
| `Piebald-AI/claude-code-system-prompts` | Reference only | Claude Code internals deconstructed |
| `wesammustafa/Claude-Code-Everything-You-Need-to-Know` | Clone (Obsidian recommended) | Comprehensive Claude Code guide + BMAD |

---

## 7. What This Saves You

| Before | After |
|---|---|
| 15-20 min per Ralph loop setup | < 1 min (`/ralph-init`) |
| Re-reading 3-4 repos every session | Knowledge baked into skills permanently |
| Inconsistent loop configs across sessions | Standardized, tested templates |
| Always consuming cloud API tokens | Routine work on free local models |
| Context window burned on repo research | Full context available for actual coding |
| Different setup per repo/project | Unified skills work across everything |
| Manual "research then implement" cycle | One-command bootstrap from BMAD stories |

---

## 8. Quick-Start Checklist

For the fastest possible setup on a new project:

```bash
# 1. Install BMAD
npx bmad-method install

# 2. Install BMAD Claude Code Skills
cd /tmp && git clone https://github.com/aj-geddes/claude-code-bmad-skills.git
cd claude-code-bmad-skills && chmod +x install-v6.sh && ./install-v6.sh

# 3. Install Ralph
mkdir -p scripts/ralph
cp /path/to/ralph/ralph.sh scripts/ralph/
cp /path/to/ralph/CLAUDE.md scripts/ralph/  # For Claude Code

# 4. Create your CLAUDE.md (use template from Step 2 above)
# 5. Create your dev-patterns skill (use template from Step 1 above)
# 6. Create your ralph-bootstrap skill (use template from Step 3 above)

# 7. (Optional) Set up Ollama for local/free runs
ollama pull qwen3-coder
ollama create my-project-dev -f ~/ollama-models/Modelfile.my-project

# 8. Start building
claude  # Opens Claude Code with CLAUDE.md auto-loaded
# Use /analyst → /pm → /architect → /ralph-init → done
```

---

## Appendix: File Structure After Setup

```
~/.claude/
├── skills/
│   └── {{project-slug}}/
│       ├── dev-patterns/SKILL.md          # Distilled system prompt patterns
│       └── ralph-bootstrap/SKILL.md       # Ralph loop bootstrapper
├── agents/
│   ├── backend-developer.md               # Stack-specific subagents
│   ├── frontend-developer.md
│   ├── mobile-developer.md
│   └── infra-developer.md
├── config/
│   └── bmad/                              # BMAD configuration
└── settings.json                          # Ollama env vars (optional)

your-project/
├── CLAUDE.md                              # Project context (auto-loaded)
├── _bmad-output/
│   └── planning-artifacts/                # PRD, architecture, stories
├── .ralph/
│   ├── ralph_loop.sh                      # Loop runner
│   ├── PROMPT.md                          # Iteration prompt template
│   ├── @fix_plan.md                       # Generated task list
│   ├── PROJECT_CONTEXT.md                 # Extracted project context
│   ├── SPECS_CHANGELOG.md                 # Spec diff between runs
│   └── logs/                              # Iteration logs
└── src/                                   # Your actual code
```
