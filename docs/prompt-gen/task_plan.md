# Task Plan: Prompt Generator Agent System

**Created**: 2026-03-09
**Status**: Planning Complete — Ready for Implementation
**Approach**: `/planning-with-files` methodology

-----

## Goal

Build a prompt generator agent system for the ACM-AI project that:

1. Scans the project's available skills, agents, workflows, codebase, rules, and hooks
1. Classifies the user's typed request (feature, bug fix, research, improvement, etc.)
1. Generates an optimized Claude Code prompt that invokes the right skills, subagents, workflows, agent teams (tmux), and Context7
1. Auto-detects when plan mode is needed and scaffolds `task_plan.md` + `findings.md` + `progress.md`
1. Works cross-platform (`.claude/skills/` + `.agents/skills/`)

-----

## Architecture Overview

```
User types request in Claude Code
         │
         ▼
┌─────────────────────────────────┐
│  /generate-prompt (slash cmd)   │  ◄── Entry point
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  1. DISCOVERY AGENT             │
│  ─────────────────────          │
│  • Scan .claude/skills/         │
│  • Scan .agents/skills/         │
│  • Scan commands/               │
│  • Read CLAUDE.md rules         │
│  • Read .claude/hooks/          │
│  • Build/update registry        │
│  → Output: SkillRegistry JSON   │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  2. CLASSIFIER AGENT            │
│  ─────────────────────          │
│  • Parse user request           │
│  • Classify type (feature,      │
│    bug, research, refactor...)  │
│  • Detect plan mode triggers    │
│  • Assess complexity (simple/   │
│    medium/complex)              │
│  → Output: RequestClassification│
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  3. ROUTER AGENT                │
│  ─────────────────────          │
│  • Match classification →       │
│    skills from registry         │
│  • Select agent strategy:       │
│    - Solo agent                 │
│    - Subagent dispatch          │
│    - Tmux agent team            │
│  • Determine if Context7 needed │
│  • Select output format         │
│  → Output: PromptPlan           │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  4. GENERATOR AGENT             │
│  ─────────────────────          │
│  • Assemble prompt from plan    │
│  • Include glossary if needed   │
│  • Add verification checklist   │
│  • Scaffold planning files if   │
│    plan mode detected           │
│  • Format for output target     │
│  → Output: Generated Prompt     │
└──────────┴──────────────────────┘
           │
     ┌─────┴──────┐
     ▼            ▼
  Terminal    Markdown file
  output      (docs/sprint-artifacts/)
```

-----

## Implementation Sessions

### Session 1: Discovery Skill + Registry Schema [S — 2 SP]

**Goal**: Create the skill that scans the filesystem and builds/maintains a skills registry.

**Files to Create**:

- `.claude/skills/skill-discovery/SKILL.md` — Discovery skill instructions
- `.claude/skills/skill-discovery/scripts/scan_registry.sh` — Bash scanner script
- `.claude/skills/skill-discovery/references/registry-schema.md` — JSON schema docs
- `.agents/skills/skill-discovery/SKILL.md` — Cross-platform copy (symlink or duplicate)
- `skills-registry.json` (repo root) — Generated registry output

**What to Build**:

1. **`scan_registry.sh`** — Bash script that:
- Walks `.claude/skills/*/SKILL.md` and `.agents/skills/*/SKILL.md`
- Extracts YAML frontmatter (name, description) from each SKILL.md
- Lists `commands/*.md` files and extracts their names
- Checks for `.claude/hooks/` files
- Reads `CLAUDE.md` and extracts rule sections
- Outputs a JSON registry to `skills-registry.json`
1. **Registry JSON Schema**:

   ```json
   {
     "version": "1.0",
     "scanned_at": "ISO-8601",
     "skills": [{
       "name": "string",
       "description": "string",
       "location": "path",
       "capabilities": ["string"],
       "triggers": ["string"],
       "platform": ["claude-code", "agents", "codex", "cursor"]
     }],
     "commands": [{
       "name": "string",
       "description": "string",
       "location": "path"
     }],
     "hooks": [{
       "name": "string",
       "trigger": "string",
       "location": "path"
     }],
     "rules": {
       "source": "CLAUDE.md",
       "sections": ["string"]
     }
   }
   ```
1. **SKILL.md** for discovery:
- Name: `skill-discovery`
- Description: Triggers on "scan skills", "update registry", "what skills are available", "list agents"
- Instructions: Run the scan script, present results, offer to update registry

**Verification**:

- [ ] `bash .claude/skills/skill-discovery/scripts/scan_registry.sh` produces valid JSON
- [ ] JSON contains all known skills from findings.md §1
- [ ] SKILL.md has proper YAML frontmatter

-----

### Session 2: Classifier Skill [M — 3 SP]

**Goal**: Create the skill that classifies user requests and detects plan mode.

**Files to Create**:

- `.claude/skills/request-classifier/SKILL.md` — Classifier skill instructions
- `.claude/skills/request-classifier/references/taxonomy.md` — Classification taxonomy
- `.agents/skills/request-classifier/SKILL.md` — Cross-platform copy

**What to Build**:

1. **Classification taxonomy** (in `references/taxonomy.md`):

   |Type           |Keywords                                                |Plan Mode          |Complexity Heuristic         |
   |---------------|--------------------------------------------------------|-------------------|-----------------------------|
   |`feature`      |add, implement, create, new, build                      |Yes                |Files mentioned > 3 = complex|
   |`bug-fix`      |fix, broken, error, failing, crash, not working         |Yes (debug plan)   |Stack trace present = complex|
   |`research`     |investigate, analyze, compare, audit, review, understand|Yes (research plan)|Open-ended = complex         |
   |`improvement`  |optimize, refactor, improve, clean up, modernize        |Yes (refactor plan)|"across" or "all" = complex  |
   |`pipeline`     |extraction, graph, node, LangGraph, pipeline            |Yes                |Always medium+               |
   |`frontend`     |component, page, UI, React, Next.js, CSS                |Conditional        |Multiple components = complex|
   |`quick-task`   |rename, move, update, change, simple                    |No                 |Always simple                |
   |`documentation`|document, docs, readme, write up                        |No                 |Usually simple               |
1. **Plan mode detection logic**:
- If type is in `[feature, bug-fix, research, improvement, pipeline]` → plan mode ON
- If request mentions "plan", "research first", "investigate before" → plan mode ON
- If request is < 20 words and type is `quick-task` → plan mode OFF
- User can override with explicit "no plan" or "with planning"
1. **Complexity scoring**:
- **Simple** (1 file, 1 skill, direct execution): Score 1-3
- **Medium** (2-4 files, 2-3 skills, may need subagent): Score 4-6
- **Complex** (5+ files, 3+ skills, needs agent team): Score 7-10

**Verification**:

- [ ] SKILL.md parses with valid frontmatter
- [ ] Taxonomy covers all request types from findings.md §2
- [ ] Example classifications are documented in references/

-----

### Session 3: Router Skill [M — 3 SP]

**Goal**: Create the skill that maps classifications to skills, agents, and strategies.

**Files to Create**:

- `.claude/skills/prompt-router/SKILL.md` — Router skill instructions
- `.claude/skills/prompt-router/references/routing-rules.md` — Routing matrix
- `.claude/skills/prompt-router/references/agent-strategies.md` — Agent strategy patterns
- `.agents/skills/prompt-router/SKILL.md` — Cross-platform copy

**What to Build**:

1. **Routing matrix** (classification → skills + strategy):

   |Classification      |Skills to Load                                                                                          |Agent Strategy                      |Context7?              |Output Format    |
   |--------------------|--------------------------------------------------------------------------------------------------------|------------------------------------|-----------------------|-----------------|
   |`feature` + complex |Domain skills + `dispatching-parallel-agents` + `planning-with-files` + `verification-before-completion`|Tmux agent team                     |Yes (for library docs) |Prompt-pack .md  |
   |`feature` + medium  |Domain skills + `subagent-driven-development` + `planning-with-files`                                   |Subagent dispatch                   |If new libraries       |Copy-paste prompt|
   |`feature` + simple  |Domain skills                                                                                           |Solo agent                          |No                     |Terminal output  |
   |`bug-fix`           |`systematic-debugging` + domain skills                                                                  |Solo focused agent                  |If library API issue   |Copy-paste prompt|
   |`research`          |`acm-observability` + domain skills + `planning-with-files`                                             |Parallel research subagents         |Yes                    |Prompt-pack .md  |
   |`improvement`       |Domain skills + `verification-before-completion`                                                        |Subagent with gates                 |If refactoring patterns|Copy-paste prompt|
   |`pipeline`          |`langgraph-fundamentals` + `acm-observability` + `planning-with-files`                                  |Tmux team (graph agent + test agent)|Yes (LangGraph docs)   |Prompt-pack .md  |
   |`frontend` + complex|Frontend skills + `dispatching-parallel-agents`                                                         |Tmux team                           |If new React patterns  |Prompt-pack .md  |
   |`quick-task`        |Minimal                                                                                                 |Solo agent                          |No                     |Terminal output  |
1. **Agent strategy templates**:

   **Solo Agent**:

   ```
   Load skills: /skill-1, /skill-2
   [prompt content]
   Verification: [checklist]
   ```

   **Subagent Dispatch** (via `/dispatching-parallel-agents`):

   ```
   Load skills: /dispatching-parallel-agents, /skill-1, /skill-2
   Parallelize:
   - Subagent A: [task A description]
   - Subagent B: [task B description]
   Main agent: Integrate results from A and B
   Verification: [checklist]
   ```

   **Tmux Agent Team**:

   ```
   Load skills: /dispatching-parallel-agents
   Agent team (tmux mode):
   - Pane 1 (Implementation): /skill-1, /skill-2 → [implementation task]
   - Pane 2 (Testing): /verification-before-completion → [test task]
   - Pane 3 (Research): Context7 → [library docs task]
   Coordination: [how panes interact]
   ```
1. **Context7 integration rules**:
- Always include for `pipeline` type (LangGraph/LangChain docs)
- Include for `feature` if request mentions specific library versions
- Include for `bug-fix` if error relates to library API
- Template: `Use Context7 MCP: resolve-library-id → query-docs for [library]`

**Verification**:

- [ ] Routing matrix covers all classification types
- [ ] Each strategy template is syntactically valid
- [ ] Context7 rules are clear and actionable

-----

### Session 4: Generator Skill + Slash Command [L — 5 SP]

**Goal**: Create the main prompt generator skill and the `/generate-prompt` slash command.

**Files to Create**:

- `.claude/skills/prompt-generator/SKILL.md` — Generator skill instructions
- `.claude/skills/prompt-generator/references/prompt-template.md` — Master prompt template
- `.claude/skills/prompt-generator/references/glossary-builder.md` — How to build glossaries
- `.claude/skills/prompt-generator/scripts/generate_prompt.sh` — CLI wrapper
- `.agents/skills/prompt-generator/SKILL.md` — Cross-platform copy
- `commands/generate-prompt.md` — Slash command definition

**What to Build**:

1. **Master prompt template** (based on S4-S9 proven structure):

   ```markdown
   # {Session Title}

   ## Goal
   {One-sentence goal statement}

   ## Skills to Load
   {List of /skill-name directives, auto-selected by router}

   ## Prerequisites
   {What must be done/checked first — auto-detected from project state}

   ## Context

   ### Project Glossary
   {Auto-generated from CLAUDE.md + domain terms relevant to this request}
   | Term | Definition |
   |------|-----------|
   | ... | ... |

   ### Current State
   {Relevant file paths, recent changes, branch info}

   ### Key Files
   {Exact paths + line numbers for files this prompt will touch}

   ## Plan
   {If plan mode: task_plan.md structure with numbered steps}
   {If no plan mode: "What to Change" numbered steps with specific files}

   ## Agent Strategy
   {Solo / Subagent dispatch / Tmux team — with specific configuration}

   ## Context7 Directives
   {If applicable: specific library-id → query-docs instructions}

   ## Verification Checklist
   {Auto-generated based on project type}
   - [ ] `uv run ruff check .`
   - [ ] `uv run pytest tests/`
   - [ ] `cd frontend && npm run build`
   - [ ] {Task-specific checks}

   ## Files Summary
   - {N} NEW: {list}
   - {N} MODIFY: {list}
   - {N} MOVE: {list}
   ```
1. **Glossary builder** (in `references/glossary-builder.md`):
- Extract terms from CLAUDE.md glossary section
- Add pipeline-specific terms (Phase 1, Phase 2, ExtractionState, etc.) when request is pipeline-related
- Add frontend terms when request is frontend-related
- Include Salesforce terms when SF-related
- Keep glossary under 20 entries (most relevant only)
1. **Slash command** (`commands/generate-prompt.md`):

   ```markdown
   ---
   name: generate-prompt
   description: Generate an optimized Claude Code prompt for your request
   ---

   Usage: /generate-prompt <your request description>

   This command:
   1. Scans available skills, agents, and workflows
   2. Classifies your request type
   3. Routes to the right skills and agent strategy
   4. Generates a complete, copy-paste-ready prompt

   Options:
   - Add "with planning" to force plan mode
   - Add "no plan" to skip planning
   - Add "save" to write output to docs/sprint-artifacts/prompt-packs/
   - Add "tmux" to force agent team mode
   ```
1. **Plan mode scaffolding**:
   When plan mode is detected, the generator also creates:
- `task_plan.md` — Populated with the generated plan steps
- `findings.md` — Template with sections for the research phase
- `progress.md` — Template with checkboxes matching the plan steps

**Verification**:

- [ ] `/generate-prompt "add a new extraction provider"` produces a valid prompt
- [ ] Plan mode generates 3 scaffold files
- [ ] Output includes correct skills, agent strategy, and verification checklist
- [ ] Glossary is relevant to the request type
- [ ] Prompt follows the S4-S9 proven structure

-----

### Session 5: Hooks + CLAUDE.md Integration [S — 2 SP]

**Goal**: Create Claude Code hooks and update CLAUDE.md to reference the prompt generator system.

**Files to Create**:

- `.claude/hooks/pre-session-scan.md` — Auto-scan skills on session start
- `.claude/hooks/post-task-progress.md` — Update progress.md after task completion
- Update `CLAUDE.md` — Add prompt generator section

**What to Build**:

1. **Pre-session scan hook** (`.claude/hooks/pre-session-scan.md`):
- Trigger: Session start
- Action: Run `scan_registry.sh` silently, update `skills-registry.json`
- Result: Registry is always current when prompts are generated
1. **Post-task progress hook** (`.claude/hooks/post-task-progress.md`):
- Trigger: After task completion (commit or explicit "done")
- Action: If `progress.md` exists in working directory, update the relevant checkbox
- Result: Progress tracking is automatic
1. **CLAUDE.md additions**:

   ```markdown
   ## Prompt Generator

   Use `/generate-prompt <request>` to generate optimized prompts that
   auto-load relevant skills, select the right agent strategy, and include
   verification checklists.

   ### Available Skills
   Run `/skill-discovery` to see all available skills, or check
   `skills-registry.json` for the full registry.

   ### Plan Mode
   Automatically activated for features, bug fixes, research, and
   improvements. Creates task_plan.md + findings.md + progress.md.
   Override with "no plan" or "with planning" in your request.
   ```

**Verification**:

- [ ] Hook files have correct format
- [ ] CLAUDE.md changes don't break existing sections
- [ ] Pre-session hook produces updated registry

-----

### Session 6: Integration Testing + Cross-Platform Sync [S — 2 SP]

**Goal**: End-to-end test the full pipeline and ensure cross-platform compatibility.

**What to Test**:

1. **Classification accuracy** — Test 10 example requests:
- "Fix the extraction pipeline timeout error" → bug-fix, medium, systematic-debugging
- "Add MinerU as a new extraction provider" → feature, complex, tmux team
- "Investigate why correction calls are high" → research, medium, parallel subagents
- "Rename the extract_items function" → quick-task, simple, solo agent
- "Refactor the pre-extraction stages to reduce LLM calls" → improvement, complex, subagent dispatch
- "Add SSE streaming to the upload wizard" → feature + frontend, complex, tmux team
- "Update the README with V3 features" → documentation, simple, solo agent
- "Compare Docling vs MinerU extraction accuracy" → research, complex, parallel subagents
- "Build a new validation gate for SF picklists" → pipeline, medium, subagent
- "Clean up unused imports across the codebase" → quick-task, simple, solo agent
1. **Cross-platform sync**:
- Verify `.claude/skills/` and `.agents/skills/` have identical SKILL.md content
- Verify `skills-registry.json` includes both locations
- Test that skills load correctly from both paths
1. **Output format validation**:
- Terminal output is clean and copy-pasteable
- Markdown file output has correct frontmatter
- Prompt-pack output follows S4-S9 structure
- Planning scaffolds create all 3 files

**Verification**:

- [ ] 10/10 test requests classified correctly
- [ ] Cross-platform skills are in sync
- [ ] All 4 output formats produce valid output
- [ ] `uv run ruff check .` passes
- [ ] `uv run pytest tests/` passes

-----

## Session Dependency Graph

```
S1 (Discovery) ──────┐
                      ├──→ S4 (Generator + Slash Command)
S2 (Classifier) ─────┤           │
                      │           ▼
S3 (Router) ──────────┘     S5 (Hooks + CLAUDE.md)
                                  │
                                  ▼
                            S6 (Integration Testing)
```

S1, S2, S3 can be **parallelized** (independent skills).
S4 depends on all three. S5 depends on S4. S6 depends on S5.

-----

## Total Effort

|Session       |Size  |SP       |Parallelizable?  |
|--------------|------|---------|-----------------|
|S1: Discovery |Small |2        |Yes (with S2, S3)|
|S2: Classifier|Medium|3        |Yes (with S1, S3)|
|S3: Router    |Medium|3        |Yes (with S1, S2)|
|S4: Generator |Large |5        |No (needs S1-S3) |
|S5: Hooks     |Small |2        |No (needs S4)    |
|S6: Testing   |Small |2        |No (needs S5)    |
|**Total**     |      |**17 SP**|**~4-6 sessions**|

With parallelization of S1-S3, this is achievable in **4 Claude Code sessions**.

-----

## Files Summary (All Sessions)

### NEW Files (16)

```
.claude/skills/skill-discovery/SKILL.md
.claude/skills/skill-discovery/scripts/scan_registry.sh
.claude/skills/skill-discovery/references/registry-schema.md
.claude/skills/request-classifier/SKILL.md
.claude/skills/request-classifier/references/taxonomy.md
.claude/skills/prompt-router/SKILL.md
.claude/skills/prompt-router/references/routing-rules.md
.claude/skills/prompt-router/references/agent-strategies.md
.claude/skills/prompt-generator/SKILL.md
.claude/skills/prompt-generator/references/prompt-template.md
.claude/skills/prompt-generator/references/glossary-builder.md
.claude/skills/prompt-generator/scripts/generate_prompt.sh
.claude/hooks/pre-session-scan.md
.claude/hooks/post-task-progress.md
commands/generate-prompt.md
skills-registry.json
```

### COPY Files (4 — cross-platform sync to .agents/skills/)

```
.agents/skills/skill-discovery/SKILL.md
.agents/skills/request-classifier/SKILL.md
.agents/skills/prompt-router/SKILL.md
.agents/skills/prompt-generator/SKILL.md
```

### MODIFY Files (1)

```
CLAUDE.md (add prompt generator section)
```
