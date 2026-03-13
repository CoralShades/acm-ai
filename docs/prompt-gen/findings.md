# Research Findings: Prompt Generator Agent System

**Date**: 2026-03-09
**Author**: Claude (planning session)

-----

## 1. Existing Skill Inventory (from project knowledge + GitHub)

### `.claude/skills/` (Claude Code skills)

|Skill Name                      |Purpose                                 |Relevant to Prompt Generator?               |
|--------------------------------|----------------------------------------|--------------------------------------------|
|`pydantic-models-py`            |Multi-model Pydantic patterns           |Yes — registry schema                       |
|`acm-observability`             |6-tool Langfuse observability stack     |Yes — include in extraction prompts         |
|`systematic-debugging`          |Root-cause-first debugging              |Yes — route to for bug-fix requests         |
|`dispatching-parallel-agents`   |Parallel subagent dispatch              |Yes — CORE dependency for multi-task prompts|
|`subagent-driven-development`   |Fresh subagent per task + review        |Yes — CORE dependency for complex prompts   |
|`planning-with-files`           |task_plan.md + findings.md + progress.md|Yes — scaffolding target for plan mode      |
|`verification-before-completion`|Pre-completion verification checklist   |Yes — append to all generated prompts       |

### `.agents/skills/` (Cross-platform skills)

|Skill Name              |Purpose                                   |Relevant?                      |
|------------------------|------------------------------------------|-------------------------------|
|`langgraph-fundamentals`|StateGraph, nodes, edges, Command patterns|Yes — include for pipeline work|
|`langchain-fundamentals`|LangChain agents, tools, middleware       |Yes — include for agent work   |

### `commands/` (Slash commands)

Commands directory exists at repo root. Claude Code slash commands use `/command-name` syntax. The prompt generator will create new slash commands here.

### Key Conventions Discovered

1. **Skill loading**: `/skill-name` in Claude Code loads skill content into context
1. **CLAUDE.md**: Auto-loaded at session start — provides project overview, commands, architecture, code style
1. **Context7 MCP**: Used for live library docs (`resolve-library-id` → `query-docs`)
1. **Subagent dispatch**: Independent subtasks can be parallelized via `/dispatching-parallel-agents`
1. **Verification pattern**: Every session ends with `ruff check`, `pytest`, `npm run build`
1. **Commit convention**: `feat():`, `fix():`, `refactor():` etc.
1. **Runner**: `uv run` for Python, `npm` for frontend
1. **Paths**: Relative to repo root (`D:\ailocal\acm-ai` or `$CLAUDE_PROJECT_DIR`)

-----

## 2. Request Classification Taxonomy

Based on the project's existing prompt-pack structure (S4-S9 sessions) and common developer workflows:

|Request Type            |Keywords/Signals                                      |Plan Mode?          |Skills to Load                               |Agent Strategy           |
|------------------------|------------------------------------------------------|--------------------|---------------------------------------------|-------------------------|
|**Feature**             |"add", "implement", "create", "new"                   |Yes (full plan)     |Relevant domain skills                       |Subagent per component   |
|**Bug Fix**             |"fix", "broken", "error", "failing", "not working"    |Yes (debugging plan)|`systematic-debugging`                       |Single focused agent     |
|**Research/Analysis**   |"investigate", "analyze", "compare", "audit", "review"|Yes (research plan) |`acm-observability`, domain skills           |Parallel research agents |
|**Improvement/Refactor**|"optimize", "refactor", "improve", "clean up"         |Yes (refactor plan) |`verification-before-completion`             |Subagent with gate checks|
|**Pipeline Work**       |"extraction", "graph", "node", "LangGraph"            |Yes                 |`langgraph-fundamentals`, `acm-observability`|Tmux team (graph + test) |
|**Frontend**            |"component", "page", "UI", "React", "Next.js"         |Conditional         |Frontend domain skills                       |Single or parallel       |
|**Quick Task**          |"rename", "move", "update import", short requests     |No                  |Minimal                                      |Direct execution         |
|**Documentation**       |"document", "write docs", "update readme"             |No                  |None specific                                |Direct execution         |

-----

## 3. Prompt Template Structure (from S4-S9 analysis)

The existing prompt-pack format has this proven structure:

```
1. Session identifier + goal statement
2. Skills to load (as /skill-name directives)
3. Prerequisites (what must be done first)
4. Context section with:
   - Glossary of domain terms
   - File locations (exact paths + line numbers)
   - Current state (what was done in prior sessions)
5. "What to Change" section (numbered steps with specific files)
6. Verification Checklist
7. Files Summary (count of NEW/MODIFY/MOVE files)
```

This structure works well because it:

- Eliminates token-wasting definition searches
- Provides exact file paths so Claude Code doesn't grep around
- Includes verification so the session is self-contained
- Follows the "S2 pattern" of front-loading context

-----

## 4. Hook System Analysis

### Current State

- No `.claude/hooks/` directory exists
- Rules live in `CLAUDE.md` (auto-loaded)
- No pre-commit or pre-push hooks specific to Claude Code

### Hooks to Create

Based on Claude Code's hook system, these hooks would support the prompt generator:

|Hook        |Trigger               |Purpose                                                 |
|------------|----------------------|--------------------------------------------------------|
|`PreSession`|Session start         |Auto-scan skills, populate registry, detect request type|
|`PreCommit` |Before `git commit`   |Run verification checklist from generated prompt        |
|`PostTask`  |After task completion |Update progress.md, log metrics                         |
|`SkillRoute`|Request classification|Select and load relevant skills automatically           |

-----

## 5. Registry Design

### Dual Discovery: Filesystem Scan + Registry File

**Filesystem scan** at runtime:

```
.claude/skills/*/SKILL.md    → Parse YAML frontmatter (name, description)
.agents/skills/*/SKILL.md    → Parse YAML frontmatter
commands/*.md                 → Parse command name + description
.claude/hooks/*               → List available hooks
```

**Registry file** (`skills-registry.json`):

```json
{
  "skills": [
    {
      "name": "planning-with-files",
      "location": ".claude/skills/planning-with-files/SKILL.md",
      "capabilities": ["planning", "scaffolding", "progress-tracking"],
      "triggers": ["plan", "research", "analysis", "feature", "bug fix"],
      "platform": ["claude-code", "agents"]
    }
  ],
  "agents": [...],
  "workflows": [...],
  "hooks": [...]
}
```

The registry adds metadata that can't be inferred from filesystem alone (capabilities, trigger words, platform compatibility).

-----

## 6. Output Format Mapping

|User's Request Context            |Output Format                     |File Location                                           |
|----------------------------------|----------------------------------|--------------------------------------------------------|
|Starting a new Claude Code session|Copy-paste prompt (terminal-ready)|`stdout` via slash command                              |
|Planning a multi-session project  |Prompt-pack .md file              |`docs/sprint-artifacts/prompt-packs/`                   |
|Quick task, no planning needed    |Direct terminal output            |`stdout`                                                |
|Complex feature with planning     |Structured pack + scaffolded files|`docs/` + `task_plan.md` + `findings.md` + `progress.md`|

-----

## 7. Tmux Mode / Agent Teams Discovery

From the project's existing patterns:

- `start-all-tmux.sh` creates 5-pane tmux layout (4 services + health dashboard)
- Claude Code's tmux mode can spawn parallel agents in separate panes
- The prompt generator should emit tmux-compatible agent team configurations when:
  - Task has 3+ independent subtasks
  - Task spans both frontend and backend
  - Task requires parallel research + implementation
