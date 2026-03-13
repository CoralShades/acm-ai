# Prompt Generator Agent System

**A 4-skill pipeline that turns natural language into optimized Claude Code session prompts.**

```
                        "Add CSV export to the item grid"
                                     |
                                     v
                  +------------------------------------------+
                  |         /generate-prompt                  |
                  |   (entry point - slash command)           |
                  +------------------------------------------+
                        |         |         |         |
                        v         v         v         v
                   DISCOVER  CLASSIFY    ROUTE    GENERATE
                   (skills)  (type/cx)  (strat)  (template)
                        |         |         |         |
                        v         v         v         v
                  +------------------------------------------+
                  |     Ready-to-paste session prompt         |
                  |   with glossary, strategy, checklist      |
                  +------------------------------------------+
```

-----

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Architecture](#2-architecture)
3. [The 4-Skill Pipeline](#3-the-4-skill-pipeline)
4. [Request Classification](#4-request-classification)
5. [Agent Strategies](#5-agent-strategies)
6. [Output Formats](#6-output-formats)
7. [Plan Mode](#7-plan-mode)
8. [Skills Registry](#8-skills-registry)
9. [Context7 Integration](#9-context7-integration)
10. [Hooks](#10-hooks)
11. [Cross-Platform Support](#11-cross-platform-support)
12. [File Map](#12-file-map)
13. [Worked Examples](#13-worked-examples)
14. [Troubleshooting](#14-troubleshooting)

-----

## 1. Quick Start

### Generate a prompt

```
/generate-prompt "Fix the extraction pipeline timeout error"
```

That's it. The system will:
- Scan your project's 135+ skills
- Classify the request as `bug-fix / medium / plan ON`
- Route to `/systematic-debugging` + solo agent strategy
- Output a complete session prompt with glossary, key files, verification checklist

### Common invocations

```bash
# Simple fix (terminal output, plan mode auto-detected)
/generate-prompt "Fix the building sidebar not loading"

# Complex feature (saved to file, forced tmux team)
/generate-prompt "Add MinerU as a new extraction provider" --save --tmux

# Research task (prompt-pack format)
/generate-prompt "Compare Docling vs MinerU accuracy" --format prompt-pack

# Quick rename (no plan, minimal overhead)
/generate-prompt "Rename extract_items to extract_acm_items" --no-plan
```

### Flags

| Flag | Effect |
|------|--------|
| `--save` | Save to `docs/sprint-artifacts/prompt-packs/` AND print |
| `--no-plan` | Skip plan mode scaffolding |
| `--with-plan` | Force plan mode even for simple tasks |
| `--tmux` | Force tmux agent team strategy |
| `--format terminal` | Print with border markers (default) |
| `--format copy-paste` | Print in fenced code block |
| `--format prompt-pack` | Save as markdown file |

-----

## 2. Architecture

### Pipeline Flow

```
User types request
       |
       v
+-------------------+     +--------------------+     +----------------+     +------------------+
|  1. DISCOVER      | --> |  2. CLASSIFY       | --> |  3. ROUTE      | --> |  4. GENERATE     |
|  /skill-discovery |     |  /request-          |     |  /prompt-      |     |  /prompt-        |
|                   |     |  classifier         |     |  router        |     |  generator       |
+-------------------+     +--------------------+     +----------------+     +------------------+
|                   |     |                    |     |                |     |                  |
| Scan filesystem   |     | Parse keywords     |     | Match matrix   |     | Fill template    |
| Read SKILL.md     |     | Score complexity   |     | Select skills  |     | Build glossary   |
| Build registry    |     | Detect plan mode   |     | Choose strategy|     | Add verification |
| Output: JSON      |     | Output: class JSON |     | Add Context7   |     | Output: prompt   |
+-------------------+     +--------------------+     +----------------+     +------------------+
```

### Data Flow

```
skills-registry.json ----+
                          |
User's request ---------> RequestClassification -----> PromptPlan -----> Generated Prompt
                          (type, complexity,           (skills, strategy, (ready-to-paste
                           plan mode, signals)          Context7, format)  session prompt)
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| 4 separate skills (not 1 monolith) | Each skill can be invoked independently; classifier is useful without generator |
| JSON registry file (not runtime-only) | Cacheable, committable, inspectable; avoids repeated filesystem scans |
| Jinja2-style template (not hardcoded) | Template is editable without touching skill logic |
| Cross-platform copies (.claude/ + .agents/) | Works in Claude Code, Codex, Cursor, OpenCode |
| Hook-based auto-refresh | Registry stays current without manual intervention |

-----

## 3. The 4-Skill Pipeline

### Skill 1: Discovery (`/skill-discovery`)

**Purpose**: Scan the project filesystem and build a catalog of all available AI capabilities.

**What it scans**:

| Location | What | How |
|----------|------|-----|
| `.claude/skills/*/SKILL.md` | Claude Code skills | YAML frontmatter extraction |
| `.agents/skills/*/SKILL.md` | Cross-platform skills | YAML frontmatter extraction |
| `commands/*.md`, `commands/*.py` | Slash commands | Filename + description extraction |
| `.claude/hooks/*` | Automation hooks | Trigger type inference |
| `CLAUDE.md` | Project rules | `## ` header extraction |

**Output**: `skills-registry.json` at repo root (see [Skills Registry](#8-skills-registry))

**Invocation**:
```
/skill-discovery
```
Or manually:
```bash
bash .claude/skills/skill-discovery/scripts/scan_registry.sh
```

**Files**:
```
.claude/skills/skill-discovery/
  SKILL.md                         # Skill instructions
  scripts/scan_registry.sh         # POSIX bash scanner
  references/registry-schema.md    # JSON schema documentation
```

-----

### Skill 2: Classifier (`/request-classifier`)

**Purpose**: Parse a natural-language request into a structured classification.

**Produces**:
```json
{
  "request_type": "feature",
  "complexity": { "score": 7, "level": "complex", "reasoning": "..." },
  "plan_mode": true,
  "plan_type": "full",
  "keywords_matched": ["add", "new"],
  "files_mentioned": ["api/routers/", "frontend/src/"],
  "domain_signals": ["extraction", "frontend"],
  "override": null
}
```

**The 8 Request Types**:

| Type | Keywords | Plan Mode | Typical Complexity |
|------|----------|-----------|-------------------|
| `feature` | add, implement, create, new, build | Yes (full) | Medium-Complex |
| `bug-fix` | fix, broken, error, failing, crash | Yes (debug) | Simple-Medium |
| `research` | investigate, analyze, compare, audit | Yes (research) | Medium-Complex |
| `improvement` | optimize, refactor, improve, clean up | Yes (refactor) | Medium-Complex |
| `pipeline` | extraction, graph, node, LangGraph | Yes (always) | Medium-Complex |
| `frontend` | component, page, UI, React, Next.js | Conditional | Simple-Complex |
| `quick-task` | rename, move, update, change, just | No | Simple |
| `documentation` | document, docs, readme, write up | No | Simple |

**Complexity Scoring** (1-10 scale):

| Range | Level | Characteristics |
|-------|-------|----------------|
| 1-3 | Simple | < 25 words, 0-1 files, single action |
| 4-6 | Medium | 25-80 words, 2-4 files, multiple related actions |
| 7-10 | Complex | > 80 words OR 5+ files, cross-backend+frontend |

**Plan Mode Decision Tree**:

```
Is type in [feature, bug-fix, research, improvement, pipeline]?
  |
  +-- YES --> plan mode ON
  |
  +-- NO --> Contains "plan"/"research first"/"investigate before"?
               |
               +-- YES --> plan mode ON
               |
               +-- NO --> complexity >= 7?
                            |
                            +-- YES --> plan mode ON
                            |
                            +-- NO --> plan mode OFF

Overrides (always win):
  "no plan" / "skip planning" / "just do it"  --> OFF
  "with planning" / "plan first"              --> ON
```

**Priority Order** (when multiple types match):
1. `pipeline` (most specific, always wins)
2. `bug-fix` (strong signals)
3. `feature`
4. `improvement` / `research`
5. `frontend`
6. `documentation`
7. `quick-task` (fallback)

**Files**:
```
.claude/skills/request-classifier/
  SKILL.md                     # 10 worked examples included
  references/taxonomy.md       # Full taxonomy with scoring algorithm
```

-----

### Skill 3: Router (`/prompt-router`)

**Purpose**: Map a classification to the optimal skill bundle, agent strategy, Context7 directives, and output format.

**The Routing Matrix** (12 rows):

| Classification | Skills | Strategy | Context7 | Format |
|---------------|--------|----------|----------|--------|
| feature + complex | planning, dispatch, verification + domain | Tmux team | Yes | prompt-pack |
| feature + medium | planning, subagent-dev + domain | Subagent dispatch | If new lib | copy-paste |
| feature + simple | Domain only | Solo | No | terminal |
| bug-fix + any | systematic-debugging + domain | Solo focused | If lib error | copy-paste |
| research + any | planning, observability + domain | Parallel subagents | Yes | prompt-pack |
| improvement + complex | planning, subagent-dev, verification + domain | Subagent w/ gates | If patterns | prompt-pack |
| improvement + med/simple | verification + domain | Solo | No | copy-paste |
| pipeline + any | langgraph, observability, planning, verification | Tmux team | Yes | prompt-pack |
| frontend + complex | dispatch + frontend skills | Tmux team | If React patterns | prompt-pack |
| frontend + med/simple | Frontend skills | Solo | No | copy-paste |
| quick-task | Minimal | Solo | No | terminal |
| documentation | None | Solo | No | terminal |

**Domain Skill Selection** (appended based on `domain_signals`):

| Signal | Added Skills |
|--------|-------------|
| extraction, pipeline, graph, node | `/langgraph-fundamentals`, `/acm-observability` |
| agent, tool, chain | `/langchain-fundamentals` |
| model, schema, pydantic | `/pydantic-models-py` |
| debug, error, trace | `/systematic-debugging`, `/acm-observability` |
| component, page, UI, React | `/react-best-practices`, `/next-best-practices` |
| streaming, SSE | `/sse-streaming` |
| test, coverage, pytest | `/test-driven-development`, `/verification-before-completion` |
| api, endpoint, fastapi | `/fastapi-router-py` |

**Files**:
```
.claude/skills/prompt-router/
  SKILL.md                           # Quick routing guide + 8-step process
  references/routing-rules.md        # Full matrix + Context7 rules + PromptPlan schema
  references/agent-strategies.md     # Solo, Subagent, Tmux templates
```

-----

### Skill 4: Generator (`/prompt-generator`)

**Purpose**: Assemble the final prompt from discovery + classification + routing outputs.

**Template Sections** (all populated automatically):

| # | Section | Source |
|---|---------|--------|
| 1 | Session title | One-sentence goal from request |
| 2 | Skills to load | `PromptPlan.selected_skills` |
| 3 | Prerequisites | Services/files that must exist |
| 4 | Glossary | Domain-specific terms (max 15) |
| 5 | Current state | Branch, sprint, recent changes |
| 6 | Key files | Exact paths grouped by Read/Modify/Create |
| 7 | Plan or steps | Plan scaffold OR numbered "What to Change" |
| 8 | Agent strategy | Solo / Subagent / Tmux config |
| 9 | Context7 | Library doc directives (if needed) |
| 10 | Verification | ruff + pytest + npm build + custom |
| 11 | Files summary | NEW / MODIFY / MOVE counts |
| 12 | Commit template | Conventional commit message |

**Files**:
```
.claude/skills/prompt-generator/
  SKILL.md                              # 5-phase pipeline instructions
  scripts/generate_prompt.sh            # CLI wrapper (flag parsing)
  references/prompt-template.md         # Master template with {{ variables }}
  references/glossary-builder.md        # Domain glossary term lists
```

-----

## 4. Request Classification

### How Classification Works

The classifier uses a **keyword + signal matching** approach, not ML. It:

1. Scans for **primary keywords** (e.g., "fix" -> bug-fix)
2. Checks **secondary signals** (stack traces, file references, phrases)
3. Applies **priority ordering** when multiple types match
4. Scores **complexity** across 4 dimensions
5. Runs the **plan mode decision tree**
6. Checks for **user overrides** ("no plan", "with planning")

### Edge Cases

| Scenario | Resolution |
|----------|-----------|
| "Fix AND improve" | Primary action wins (is the fix or the improvement driving the request?) |
| "Investigate then fix" | `research` (investigation is the deliverable; fix is implied future work) |
| "Frontend feature with new API" | `feature` (not `frontend` — crosses backend boundary) |
| "Rename across all files" | `quick-task` with higher complexity (still mechanical) |
| "Add docs for complex system" | `documentation` (task is writing, not engineering) |

### User Overrides

| Phrase | Effect |
|--------|--------|
| "no plan", "skip planning", "just do it" | `plan_mode: false` |
| "with planning", "plan first", "think through" | `plan_mode: true` |
| "treat as quick task" | Override type to `quick-task` |
| "this is complex" | +2 to complexity score |

-----

## 5. Agent Strategies

### Strategy A: Solo Agent

**When**: Simple tasks, focused bug fixes, documentation, quick tasks.

```
Single Claude Code session
  |
  +-- Load skills
  +-- Read context
  +-- Implement
  +-- Verify
  +-- Commit
```

**Characteristics**: Low overhead, no coordination, linear execution.

-----

### Strategy B: Subagent Dispatch

**When**: Medium features, complex improvements with gates, parallel research.

```
Main Agent (orchestrator)
  |
  +-- Spawn Subagent A (backend) ----+
  |                                   |
  +-- Spawn Subagent B (frontend) ---+-- Wait for all
  |                                   |
  +-- Integrate results <-------------+
  |
  +-- Run verification
  +-- Commit
```

**Characteristics**: Parallel execution of independent tasks, gate checks between phases, orchestrator integrates results.

**Gate Pattern** (for improvements):
```
GATE 1: After Subagent A
  Run: uv run ruff check .
  Run: uv run pytest tests/
  FAIL -> Fix before dispatching B
  PASS -> Dispatch Subagent B
```

-----

### Strategy C: Tmux Agent Team

**When**: Complex features, pipeline work, anything needing simultaneous implementation + testing + research.

```
tmux session
  |
  +-- Pane 1: Implementation (lead)
  |     Skills: domain skills
  |     Writes code, updates progress.md
  |
  +-- Pane 2: Testing
  |     Skills: /verification-before-completion
  |     Runs tests continuously, reports failures to findings.md
  |
  +-- Pane 3: Research (optional)
        Skills: Context7 MCP
        Fetches docs, writes findings to findings.md
```

**Coordination Protocol**:
1. All panes read `task_plan.md` before starting
2. Panes write shared discoveries to `findings.md`
3. Implementation pane has file-edit priority
4. Implementation writes "COMPLETE" to `progress.md` when done
5. Testing pane runs final checklist

**2-pane vs 3-pane**:
- **2 panes**: No Context7 needed, minimal research
- **3 panes**: Library docs needed, complex architectural research

-----

## 6. Output Formats

| Format | When Used | Destination |
|--------|-----------|-------------|
| `terminal` | Simple/quick tasks | Printed with `══` border markers |
| `copy-paste` | Medium tasks | Printed in fenced code block for copying |
| `prompt-pack` | Complex tasks, plan mode | Saved to `docs/sprint-artifacts/prompt-packs/YYYY-MM-DD-{slug}.md` |

The `--save` flag always saves to prompt-packs AND prints to terminal.

### Terminal Output Example

```
══════════════════════════════════════════
  GENERATED PROMPT — Fix building sidebar crash
══════════════════════════════════════════
[... prompt content ...]
══════════════════════════════════════════
```

### Prompt-Pack Output

Saved as a dated markdown file:
```
docs/sprint-artifacts/prompt-packs/2026-03-13-fix-building-sidebar.md
```

-----

## 7. Plan Mode

### What It Creates

When plan mode activates, the generator scaffolds three planning files:

| File | Purpose | Updated By |
|------|---------|-----------|
| `task_plan.md` | Numbered steps with file paths | Read before starting; update checkboxes as you work |
| `findings.md` | Research discoveries and decisions | Populate during investigation |
| `progress.md` | Session recovery journal | Update at end of each session |

### When It Activates

| Request Type | Plan Mode |
|-------------|-----------|
| feature | Always ON |
| bug-fix | Always ON (debug plan) |
| research | Always ON (research plan) |
| improvement | Always ON (refactor plan) |
| pipeline | Always ON |
| frontend | ON if complexity >= 7 |
| quick-task | OFF |
| documentation | OFF |

### Plan Types

| Plan Type | Structure | Used For |
|-----------|-----------|----------|
| `full` | Goal + Steps + Risks | Features, pipeline work |
| `debug` | Symptoms + Hypothesis + Investigation Steps | Bug fixes |
| `research` | Questions + Methodology + Findings Template | Research/analysis |
| `refactor` | Current State + Target State + Migration Steps | Improvements |

-----

## 8. Skills Registry

### Location

```
D:/ailocal/acm-ai/skills-registry.json
```

### Schema

```json
{
  "version": "1.0",
  "scanned_at": "2026-03-13T00:06:52Z",
  "skills": [
    {
      "name": "planning-with-files",
      "description": "Persistent markdown-based planning...",
      "location": ".claude/skills/planning-with-files/SKILL.md",
      "also_at": [".agents/skills/planning-with-files/SKILL.md"],
      "has_scripts": false,
      "has_references": false,
      "platform": ["claude-code", "agents"]
    }
  ],
  "commands": [
    {
      "name": "acm_commands",
      "description": "ACM Extraction Background Commands",
      "location": "commands/acm_commands.py"
    }
  ],
  "hooks": [
    {
      "name": "pre-session-scan.md",
      "trigger": "Custom",
      "location": ".claude/hooks/pre-session-scan.md"
    }
  ],
  "rules": {
    "source": "CLAUDE.md",
    "sections": ["Project Overview", "Essential Commands", "Architecture", "..."]
  }
}
```

### Current Stats

| Category | Count |
|----------|-------|
| Skills | 135 |
| Commands | 5 |
| Hooks | 12 |
| CLAUDE.md rule sections | 19 |
| Cross-platform skills | 76 |

### Refreshing the Registry

The registry auto-refreshes via the pre-session hook when stale (>24h). Manual refresh:

```
/skill-discovery
```

Or:
```bash
bash .claude/skills/skill-discovery/scripts/scan_registry.sh
```

-----

## 9. Context7 Integration

### What It Does

Context7 MCP fetches **live library documentation** so generated prompts reference current APIs, not stale training data.

### When It's Included

| Condition | Included? |
|-----------|-----------|
| `pipeline` type | Always (LangGraph + LangChain) |
| `research` type | Always (mentioned libraries) |
| `feature` with explicit library version | Yes (that library) |
| `bug-fix` with library API error | Yes (offending library) |
| `quick-task` or `documentation` | Never |

### Available Templates

| Library | Directive |
|---------|-----------|
| LangGraph | `resolve-library-id for "langgraph"` -> `query-docs for "{topic}"` |
| LangChain | `resolve-library-id for "langchain"` -> `query-docs for "{topic}"` |
| Pydantic | `resolve-library-id for "pydantic"` -> `query-docs for "{topic}"` |
| Next.js | `resolve-library-id for "nextjs"` -> `query-docs for "{topic}"` |
| React | `resolve-library-id for "react"` -> `query-docs for "{topic}"` |
| AG Grid | `resolve-library-id for "ag-grid"` -> `query-docs for "{topic}"` |

The `{topic}` is extracted from the user's request (e.g., "StateGraph conditional edges" for a LangGraph pipeline request).

-----

## 10. Hooks

### Pre-Session Scan

**File**: `.claude/hooks/pre-session-scan.md`
**Trigger**: Session start

Checks if `skills-registry.json` is missing or >24 hours old. If so, runs the scanner automatically. Ensures `/generate-prompt` always has current data.

### Post-Task Progress

**File**: `.claude/hooks/post-task-progress.md`
**Trigger**: Task completion

If `progress.md` exists in the working directory, automatically checks off the matching task (`- [ ]` -> `- [x]`) and updates the timestamp. Keeps planning files in sync.

-----

## 11. Cross-Platform Support

Every skill in `.claude/skills/` is mirrored in `.agents/skills/` with identical content. This ensures the prompt generator works across:

| Platform | Skill Location |
|----------|---------------|
| Claude Code | `.claude/skills/` |
| OpenAI Codex | `.agents/skills/` |
| Cursor | `.agents/skills/` |
| OpenCode | `.agents/skills/` |

### Synced Skills

```
.claude/skills/skill-discovery/     <-->  .agents/skills/skill-discovery/
.claude/skills/request-classifier/  <-->  .agents/skills/request-classifier/
.claude/skills/prompt-router/       <-->  .agents/skills/prompt-router/
.claude/skills/prompt-generator/    <-->  .agents/skills/prompt-generator/
```

### Verifying Sync

```bash
for skill in skill-discovery request-classifier prompt-router prompt-generator; do
  diff -r ".claude/skills/$skill" ".agents/skills/$skill" > /dev/null 2>&1 \
    && echo "OK: $skill" \
    || echo "DRIFT: $skill"
done
```

-----

## 12. File Map

### Primary Skills (`.claude/skills/`)

```
.claude/skills/
  skill-discovery/
    SKILL.md                          # Discovery instructions
    scripts/scan_registry.sh          # POSIX bash filesystem scanner
    references/registry-schema.md     # JSON schema documentation

  request-classifier/
    SKILL.md                          # Classification instructions + 10 examples
    references/taxonomy.md            # 8 types, scoring algorithm, decision tree

  prompt-router/
    SKILL.md                          # Routing instructions + quick guide
    references/routing-rules.md       # 12-row matrix, domain signals, PromptPlan schema
    references/agent-strategies.md    # Solo, Subagent, Tmux templates

  prompt-generator/
    SKILL.md                          # 5-phase pipeline instructions
    scripts/generate_prompt.sh        # CLI wrapper with flag parsing
    references/prompt-template.md     # Master template (12 {{ variable }} sections)
    references/glossary-builder.md    # Pipeline, Frontend, General term lists
```

### Slash Command

```
.claude/commands/generate-prompt.md   # /generate-prompt entry point
```

### Hooks

```
.claude/hooks/
  pre-session-scan.md                 # Auto-refresh registry on session start
  post-task-progress.md               # Auto-update progress.md on task completion
```

### Generated Artifacts

```
skills-registry.json                  # Scanner output (repo root)
docs/sprint-artifacts/prompt-packs/   # Saved prompt-pack outputs
```

### Cross-Platform Mirrors

```
.agents/skills/
  skill-discovery/    (identical to .claude/)
  request-classifier/ (identical to .claude/)
  prompt-router/      (identical to .claude/)
  prompt-generator/   (identical to .claude/)
```

-----

## 13. Worked Examples

### Example 1: Bug Fix (solo agent, copy-paste)

**Request**: `"Fix the extraction pipeline timeout error"`

| Phase | Result |
|-------|--------|
| Classify | `bug-fix`, complexity 5 (medium), plan ON (debug) |
| Route | `/systematic-debugging` + `/acm-observability` + `/langgraph-fundamentals`, solo agent, Context7 conditional |
| Generate | Prompt with pipeline glossary, key files in `acm_extraction.py`, debug plan scaffold |
| Output | Copy-paste format to terminal |

**Generated skills directive**:
```
/systematic-debugging — structured diagnosis before proposing fixes
/acm-observability — Langfuse traces for root cause analysis
/langgraph-fundamentals — graph node/state patterns
/planning-with-files — debug plan scaffold
```

-----

### Example 2: Complex Feature (tmux team, prompt-pack)

**Request**: `"Add a CSV export button to the item grid with a new /api/acm/export endpoint" --save --tmux`

| Phase | Result |
|-------|--------|
| Classify | `feature`, complexity 7 (complex, cross-cutting), plan ON (full) |
| Route | `/planning-with-files` + `/dispatching-parallel-agents` + `/verification-before-completion` + `/fastapi-router-py` + `/react-best-practices`, tmux team, Context7 for AG Grid |
| Generate | 3-pane tmux config (backend/frontend/verifier), pipeline+frontend glossary |
| Output | Saved to `docs/sprint-artifacts/prompt-packs/2026-03-13-csv-export-item-grid.md` |

**Generated tmux layout**:
```
Pane 1 (backend):  Create /api/acm/export endpoint + service
Pane 2 (frontend): Add Export CSV button to ItemGrid toolbar
Pane 3 (verifier): Run tests after each step, final build check
```

-----

### Example 3: Quick Task (solo, terminal)

**Request**: `"Rename extract_items to extract_acm_items"`

| Phase | Result |
|-------|--------|
| Classify | `quick-task`, complexity 1 (simple), plan OFF |
| Route | No extra skills, solo agent |
| Generate | Minimal prompt with just the rename steps and `ruff check` verification |
| Output | Terminal inline |

-----

### Example 4: Research (parallel subagents, prompt-pack)

**Request**: `"Investigate why correction LLM calls are spiking — check Langfuse traces for the last 10 runs"`

| Phase | Result |
|-------|--------|
| Classify | `research`, complexity 7 (complex, open-ended), plan ON (research) |
| Route | `/acm-observability` + `/planning-with-files` + `/langgraph-fundamentals`, parallel subagents, Context7 for LangGraph |
| Generate | Research plan scaffold, observability glossary, Langfuse trace inspection steps |
| Output | Prompt-pack saved to file |

-----

### Example 5: Pipeline Work (tmux team, prompt-pack)

**Request**: `"Add a caching layer to the extraction graph"`

| Phase | Result |
|-------|--------|
| Classify | `pipeline`, complexity 5 (medium), plan ON (always for pipeline) |
| Route | `/langgraph-fundamentals` + `/acm-observability` + `/planning-with-files` + `/verification-before-completion`, tmux team, Context7 for LangGraph + LangChain |
| Generate | 2-pane tmux (implementation + testing), full pipeline glossary |
| Output | Prompt-pack saved to file |

-----

## 14. Troubleshooting

### "Registry is empty or missing skills"

```bash
# Regenerate from scratch
bash .claude/skills/skill-discovery/scripts/scan_registry.sh

# Verify JSON is valid
python3 -m json.tool skills-registry.json > /dev/null && echo OK
```

### "Classification seems wrong"

The classifier uses keyword priority ordering. If it picks the wrong type:
- Add `"treat as [type]"` to your request to override
- Check if your request has ambiguous keywords (e.g., "fix and improve")
- Review the priority order: pipeline > bug-fix > feature > improvement > research > frontend > documentation > quick-task

### "Skills not in sync across platforms"

```bash
# Re-sync all 4 prompt-generator skills
for skill in skill-discovery request-classifier prompt-router prompt-generator; do
  rm -rf ".agents/skills/$skill"
  cp -r ".claude/skills/$skill" ".agents/skills/$skill"
done
```

### "Plan mode activates when I don't want it"

Add `--no-plan` to your `/generate-prompt` invocation, or include "no plan" / "just do it" in your request text.

### "generate_prompt.sh fails"

```bash
# Check it's executable
chmod +x .claude/skills/prompt-generator/scripts/generate_prompt.sh

# Run with debug output
bash -x .claude/skills/prompt-generator/scripts/generate_prompt.sh "test request"
```

### "Context7 directives are missing"

Context7 is only included when the routing matrix says so. Quick-tasks and documentation never get Context7. For other types, check the conditional rules in `.claude/skills/prompt-router/references/routing-rules.md`.

-----

*Built across 6 implementation sessions (17 SP). Planning documents: [task_plan.md](task_plan.md) | [findings.md](findings.md) | [progress.md](progress.md)*
