---
description: Generate an optimized Claude Code prompt for any task. Analyzes your request, selects the right skills and agent strategy, and produces a ready-to-use prompt with glossary and verification checklist.
argument-hint: <your request description> [--save] [--no-plan] [--with-plan] [--tmux] [--format FORMAT]
---

# Generate Prompt

Generate an optimized Claude Code prompt for your request.

## Usage

```
/generate-prompt <your request description>
```

## Options

- `--save` — Save the generated prompt to `docs/sprint-artifacts/prompt-packs/`
- `--no-plan` — Skip plan mode even if auto-detected
- `--with-plan` — Force plan mode even if not auto-detected
- `--tmux` — Force tmux agent team strategy
- `--format FORMAT` — Output format: `terminal` (default), `copy-paste`, `prompt-pack`

## Examples

```
/generate-prompt "Fix the extraction pipeline timeout error"
/generate-prompt "Add MinerU as a new extraction provider" --save --tmux
/generate-prompt "Refactor pre-extraction stages" --format prompt-pack
```

## What Happens

When you run `/generate-prompt`, Claude Code executes the `prompt-generator` skill which runs a 5-phase pipeline:

1. **Discover** — Scans project for available skills (updates `skills-registry.json` if stale or missing)
2. **Classify** — Applies `/request-classifier` to determine request type, complexity, and whether plan mode is needed
3. **Route** — Applies `/prompt-router` to select optimal skills, agent strategy, and Context7 directives
4. **Generate** — Populates the master prompt template with glossary, current state, key files, strategy config, and verification checklist
5. **Output** — Delivers the prompt in the requested format; if plan mode is on, also scaffolds `task_plan.md`, `findings.md`, `progress.md`

## Instructions

Load the `prompt-generator` skill and follow its 5-phase pipeline:

```
D:/ailocal/acm-ai/.claude/skills/prompt-generator/SKILL.md
```

### Argument Parsing

Parse `$ARGUMENTS` to extract:
- **Request text** — everything before the first `--` flag, or the full string if no flags
- **Flags** — `--save`, `--no-plan`, `--with-plan`, `--tmux`, `--format <value>`

If no arguments are provided, ask the user: "What would you like to generate a prompt for?"

### Phase 1 — Discover

Check `D:/ailocal/acm-ai/skills-registry.json`:
- If missing: run `/skill-discovery` to generate it
- If older than 1 hour: run `/skill-discovery` to refresh it
- If current: read it directly

### Phase 2 — Classify

Run `/request-classifier` on the user's request text.

Apply flag overrides:
- `--no-plan` present → force `plan_mode: false`
- `--with-plan` present → force `plan_mode: true`

If classification is ambiguous, present candidates and ask the user to confirm.

### Phase 3 — Route

Run `/prompt-router` with the classification JSON.

Apply flag overrides:
- `--tmux` present → force `agent_strategy: "tmux-team"`
- `--format prompt-pack` or `--save` → force `output_format: "prompt-pack"`

### Phase 4 — Generate

Read these reference files:
- Template: `D:/ailocal/acm-ai/.claude/skills/prompt-generator/references/prompt-template.md`
- Glossary: `D:/ailocal/acm-ai/.claude/skills/prompt-generator/references/glossary-builder.md`

Populate all `{{ variable }}` placeholders in the template.

If `plan_mode=true`, create skeleton files in `D:/ailocal/acm-ai/docs/sprint-artifacts/`:
- `task_plan.md`
- `findings.md`
- `progress.md`

### Phase 5 — Output

Select output format from `PromptPlan.output_format` (or `--format` override):

| Format | Action |
|--------|--------|
| `terminal` | Print with `══` border markers |
| `copy-paste` | Print in fenced code block |
| `prompt-pack` | Save to `docs/sprint-artifacts/prompt-packs/YYYY-MM-DD-{slug}.md` |

If `--save` flag: always save to prompt-packs/ AND print to terminal.

Confirm output with file path if saved.
