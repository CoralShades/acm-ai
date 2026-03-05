# Model Strategy Guide

Model selection is one of the most important levers for balancing cost, speed, and quality in Ralph loops. This document defines when to use which model, how billing works, and how to use local Ollama models.

---

## Capability Tiers

| Tier | Model ID | Speed | Cost | Reasoning | Context Window | Best For |
|---|---|---|---|---|---|---|
| **Fast/Cheap** | `claude-haiku-*` | Fastest | Lowest | Basic | 200k | Docs, lint, simple tests, changelog |
| **Balanced** | `claude-sonnet-*` | Medium | Medium | Strong | 200k | Most implementation work, code review, QA |
| **Best** | `claude-opus-*` | Slowest | Highest | Best | 200k | Complex architecture, novel problems, undocumented areas |

### Current Model IDs (as of August 2025)

```
claude-haiku-4-5        # Fast/cheap tier
claude-sonnet-4-6       # Balanced tier (current session model)
claude-opus-4-6         # Best reasoning tier
```

In Ralph config and Task tool calls, use the shorthand: `haiku`, `sonnet`, `opus`.

---

## Default Phase Assignments

| Phase | Agent | Default Model | Justification |
|---|---|---|---|
| Architecture review | ralph-architect | `sonnet` | Needs strong reasoning but well-defined scope |
| Sprint planning | ralph-sm | `sonnet` | Story parsing + config generation; structured task |
| Backend implementation | backend-specialist | `sonnet` | Codebase has established patterns; sonnet follows them well |
| Frontend implementation | frontend-specialist | `sonnet` | Same; Next.js/React patterns are well-documented |
| QA / gate verification | ralph-qa | `sonnet` | Test execution is tool-heavy; sonnet handles well |
| Code review | ralph-reviewer | `sonnet` | Pattern matching and checklist completion |
| Documentation | docs-specialist | `haiku` | Templated writing; no complex reasoning required |

These are defaults. Override based on the heuristics below.

---

## Upgrade Heuristics (sonnet → opus)

Only applies to single-agent calls (never in teams).

### When to upgrade to opus

| Trigger | Example |
|---|---|
| Story touches area with no existing code patterns | First implementation of a new LangGraph graph type |
| Deep architectural reasoning required | Designing pipeline state machine with 9+ stages |
| Cross-cutting concern affecting 4+ subsystems | SSE + pipeline + frontend + SurrealDB schema change |
| Previous sonnet attempt produced wrong architecture | Sonnet chose wrong pattern; opus to course-correct |
| Minimal documentation exists for the domain | Novel ACM extraction algorithm with no prior art in codebase |
| Story marked "Complex" or "Spike" in ralph-config.json | Explicit signal from SM that complexity is high |

### Upgrade anti-patterns

Do NOT upgrade to opus for:
- Stories that have clear existing patterns to follow
- Simple CRUD endpoint additions
- Test additions following existing test file structure
- Any story inside a team (team rules override)
- Stories estimated under 2 hours of human development time

---

## Downgrade Heuristics (sonnet → haiku)

### When to downgrade to haiku

| Trigger | Example |
|---|---|
| Task is documentation only | Updating docs/sprint-artifacts/ completion record |
| Task is a simple lint/format fix | `ruff check --fix` with no logic changes |
| Task follows a rigid template | CHANGELOG entry following established format |
| Task is reading + summarizing only | Sprint retrospective summary from log files |
| Story estimated under 30 minutes human time | Adding a missing type hint, fixing a typo |

### Haiku limitations to be aware of

- May not correctly handle complex multi-file refactors
- Less reliable at inferring implicit project conventions
- Can miss edge cases in error handling
- Do not use haiku for any task that requires reasoning about trade-offs

---

## Billing: OAuth vs API Key

Understanding billing is critical for cost control in long Ralph loops.

### OAuth (Subscription Billing)

- **How it works:** Claude Code uses your Anthropic subscription (Pro or Team plan) for all model calls
- **Billing:** Fixed monthly subscription; no per-token charges
- **Activation:** Default when you log in via `claude auth login` with browser OAuth
- **Best for:** Personal development, exploratory work, overnight runs where you want cost predictability
- **Limitation:** Rate limits apply at subscription tier; heavy usage may hit limits

### API Key (Per-Token Billing)

- **How it works:** Set `ANTHROPIC_API_KEY` env var; Claude Code bills per token
- **Billing:** Per input/output token; see Anthropic pricing page for current rates
- **Activation:** `export ANTHROPIC_API_KEY=sk-ant-...` before starting Claude Code
- **Best for:** Production pipelines, CI/CD, when you need guaranteed no rate limits
- **Limitation:** Costs can be significant for long opus runs; monitor usage

### Forcing OAuth When API Key Is Set

If `ANTHROPIC_API_KEY` is in your environment but you want to use OAuth subscription:

```bash
env -u ANTHROPIC_API_KEY claude
```

This unsets the API key for the Claude process, forcing OAuth billing. Useful when you want to use subscription billing but have the API key set for other tools.

### Cost Estimation for Ralph Loops

Rough estimates (as of 2025; verify current pricing):

| Scenario | Model | Approx cost (API key) |
|---|---|---|
| Single story (50 turns, sonnet) | sonnet | $0.50 - $2.00 |
| Full sprint 8 stories (sonnet) | sonnet | $4.00 - $16.00 |
| Architecture review (opus, 12 turns) | opus | $3.00 - $8.00 |
| Docs update (haiku, 10 turns) | haiku | $0.05 - $0.20 |
| Full sprint with opus for complex stories | mixed | $20.00 - $60.00 |

**Note:** Team mode multiplies costs by number of parallel agents.

---

## Ollama Local Models

For cost-free local execution, Ralph can use Ollama models. These run on your machine with no API costs.

### Setup

```bash
# Install Ollama (Windows)
# Download from https://ollama.ai

# Pull a model
ollama pull qwen3-coder:7b
ollama pull glm4:9b

# Verify
ollama list
```

### Recommended Models for Ralph

| Model | Size | Best For | VRAM Required |
|---|---|---|---|
| `qwen3-coder:7b` | 4.7 GB | Code implementation, small stories | 6 GB |
| `qwen3-coder:14b` | 9 GB | Better code reasoning, medium stories | 10 GB |
| `glm-4.7-flash` | 4 GB | Fast iteration, docs, simple tasks | 5 GB |
| `codestral:22b` | 14 GB | Complex code tasks | 16 GB |
| `llama3.1:70b` | 40 GB | Near-Claude quality, all tasks | 48 GB (A100) |

### Hardware Requirements

| Scenario | Min VRAM | Recommended |
|---|---|---|
| Haiku-equivalent (7b models) | 6 GB | RTX 3060 12GB |
| Sonnet-equivalent (14b-22b models) | 12 GB | RTX 4090 24GB |
| Opus-equivalent (70b+ models) | 40 GB | A100 40GB |

### Modelfile for Ralph-Optimized Inference

Create a custom Modelfile for better Ralph performance:

```dockerfile
# File: Modelfile.ralph-coder
FROM qwen3-coder:14b

SYSTEM """
You are an expert software engineer working on the ACM-AI project.
You follow the project's coding standards strictly:
- Python: type hints required, Google-style docstrings, ruff-compatible
- Commits: conventional commits (feat:, fix:, docs:, refactor:, test:)
- Always prefer editing existing files over creating new ones
- Never create documentation files unless explicitly requested
"""

PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER num_ctx 32768
```

Build and use:
```bash
ollama create ralph-coder -f Modelfile.ralph-coder
ollama run ralph-coder
```

### Claude Launcher for Model Switching

To switch between Claude and Ollama without changing config:

```bash
# claude-launcher.sh — wrapper that selects model based on env var
#!/usr/bin/env bash

MODEL="${RALPH_MODEL:-sonnet}"

case "$MODEL" in
  haiku)
    env -u ANTHROPIC_API_KEY claude --model claude-haiku-4-5 "$@"
    ;;
  opus)
    env -u ANTHROPIC_API_KEY claude --model claude-opus-4-6 "$@"
    ;;
  local-fast)
    # Use Ollama via OpenAI-compatible API
    ANTHROPIC_BASE_URL=http://localhost:11434/v1 \
    ANTHROPIC_API_KEY=ollama \
    claude --model glm-4.7-flash "$@"
    ;;
  local-coder)
    ANTHROPIC_BASE_URL=http://localhost:11434/v1 \
    ANTHROPIC_API_KEY=ollama \
    claude --model ralph-coder "$@"
    ;;
  *)
    # Default: sonnet via OAuth
    env -u ANTHROPIC_API_KEY claude --model claude-sonnet-4-6 "$@"
    ;;
esac
```

Usage:
```bash
RALPH_MODEL=local-coder bash .claude/hooks/ralph-batch.sh
RALPH_MODEL=haiku claude -p "/ralph-run E30-S5"
RALPH_MODEL=opus claude -p "/ralph-run E30-S1"  # single complex story
```

### Ollama Limitations for Ralph

- No tool use / function calling in most 7b models
- Context window typically 8k-32k (vs Claude's 200k)
- Cannot use MCP servers (no tool protocol support in Ollama's native API)
- Quality significantly lower than Claude for multi-file reasoning
- Best used for: docs updates, simple lint runs, exploratory research
- Not recommended for: implementation stories, architecture decisions, QA gates

### When to Use Local Models

```
Story type = docs update AND model = haiku? → try local-fast (glm-4.7-flash)
Story type = simple test addition? → try local-coder (qwen3-coder:14b)
Story type = implementation? → use sonnet (Claude API)
Story type = architecture? → use sonnet or opus (Claude API)
Overnight batch run, cost sensitive? → start with local, fallback to sonnet on failure
```

---

## Model Selection Decision Tree

```
Is this inside a team (team_name set)?
  YES → always sonnet (MANDATORY, see CLAUDE.md)
  NO  →
    Is this docs/changelog/lint only?
      YES → haiku
      NO  →
        Is this architecture/design story?
          YES → sonnet (upgrade to opus if: undocumented area, cross-cutting, novel)
          NO  →
            Does this follow established codebase patterns?
              YES → sonnet
              NO  → sonnet (first attempt), opus (if sonnet fails or story is marked Complex)
```

---

## ralph-config.json Model Overrides

Per-story model overrides are supported in ralph-config.json:

```json
{
  "stories": [
    {
      "id": "E30-S1",
      "title": "SF Schema Config Loader",
      "model": "sonnet",          // default
      "status": "Done"
    },
    {
      "id": "E30-S3",
      "title": "Novel Pipeline Redesign",
      "model": "opus",            // override: complex, undocumented
      "status": "Ready"
    },
    {
      "id": "E30-S7",
      "title": "Update Sprint Docs",
      "model": "haiku",           // override: docs only
      "status": "Ready"
    }
  ]
}
```

The bash loop and `/ralph-run` command read the `model` field and pass it to the `claude` CLI invocation.
