# Ralph Templates

Copy-paste ready templates for bootstrapping a Ralph loop on any project.

## Usage

1. Copy the relevant template files to your project
2. Replace all `{{PLACEHOLDER}}` markers with project-specific values
3. Follow the setup guide in `../00-quickstart.md`

## Template Manifest

| Template | Produces | Key Variables |
|----------|----------|---------------|
| `CLAUDE.md.template` | Project root `CLAUDE.md` | `PROJECT_NAME`, `STACK`, `TEST_COMMAND`, `LINT_COMMAND`, `BUILD_COMMAND` |
| `prd.json.template` | `prd.json` project state | `PROJECT_NAME`, story/gate data |
| `ralph-config.json.template` | `ralph-config.json` | Model names, limits, phase toggles |
| `ralph_loop.sh.template` | Simple bash loop (~50 lines) | `MAX_ITERATIONS`, `MODEL`, `PROMPT_FILE` |
| `ralph_loop_full.sh.template` | Full bash loop (~250 lines) | `MAX_ITERATIONS`, `CHECKPOINT_INTERVAL`, `NO_PROGRESS_THRESHOLD` |
| `PROMPT.md.template` | Iteration prompt | `PROJECT_NAME`, `TEST_COMMAND`, `LINT_COMMAND`, `FIX_PLAN_PATH` |
| `PROMPT_REVIEW.md.template` | Adversarial review prompt | `PROJECT_NAME`, `FIX_PLAN_PATH` |

## Hook Templates

| Template | Hook Event | Purpose |
|----------|-----------|---------|
| `hooks/ralph-stop-gate.sh` | Stop | Prevent premature exit during loops |
| `hooks/ralph-gate-guard.sh` | PreToolUse (Bash) | Block commits with unmet deps |
| `hooks/pre-commit-gate.sh` | PreToolUse (Bash) | Block commits failing lint/build |
| `hooks/scope-guard.sh` | PreToolUse (Write\|Edit) | Block writes to protected paths |
| `hooks/task-quality-gate.sh` | TaskCompleted | Block task completion without passing gates |

## Agent Templates

| Template | Role | Max Turns |
|----------|------|-----------|
| `agents/ralph-sm.md.template` | Scrum Master — tech spec creation | 20 |
| `agents/ralph-architect.md.template` | Architect — risk analysis (read-only) | 12 |
| `agents/ralph-qa.md.template` | QA — test coverage verification | 30 |
| `agents/ralph-reviewer.md.template` | Reviewer — code review + compliance | 15 |

## Conventions

- `{{PLACEHOLDER}}` — Replace with project-specific value
- `.template` suffix — Remove suffix when copying to project
- Hook scripts — Copy directly (no suffix), customize `PROTECTED_PATTERNS` and commands
- All templates are project-agnostic — no framework or database references
