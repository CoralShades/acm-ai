# Claude Code Insights Changelog

Learnings extracted from `/insights` command and applied to project configuration.

## 2026-02-15: Baseline Analysis

**Session Period:** 2026-02-11 to 2026-02-14 (4 days)
**Sessions Analyzed:** 109 sessions, 71 hours, 28 commits
**Projects:** ACM-AI, CurryDash, TTS/Voice setup

### Key Findings

#### 1. Wrong Initial Assumptions Leading to Wasted Effort (11 instances)
- **Finding:** Claude frequently jumped into action based on wrong assumptions about codebase state
- **Examples:**
  - Attempted cherry-picks before discovering branches were already reconciled
  - Misunderstood observer session messages as transcripts vs live triggers
  - Over-engineered ci.yml beyond plan specifications

#### 2. Environment and Credential Failures Blocking Progress (6 instances)
- **Finding:** Authentication and system dependency issues repeatedly blocked progress
- **Examples:**
  - Admin login credentials failed twice during portal audits
  - VoiceMode/Whisper STT setup devolved into CUDA build failures
  - Missing libportaudio2 dependencies blocked TTS setup

#### 3. Over-Engineering and Mode Confusion (4 instances)
- **Finding:** Claude produced solutions more complex than specified or got stuck in wrong modes
- **Examples:**
  - Added unnecessary complexity to ci.yml instead of following blueprint
  - Got stuck in plan mode without write tool access (only 'not_achieved' outcome)
  - Created features beyond plan scope without asking first

#### 4. Memory Observer Pattern Friction (20+ sessions)
- **Finding:** Memory observer role frequently misunderstood initially
- **Examples:**
  - Claude tried to read files and investigate codebase instead of just recording events
  - Processed first messages as transcripts instead of observation triggers
  - Needed extra context/correction messages at start of each session

#### 5. Multi-Agent Coordination Success
- **Finding:** Team-lead delegation pattern produced excellent results
- **Examples:**
  - Parallel portal audits across 3 portals simultaneously
  - 116/116 passing E2E tests achieved
  - 6 GitHub Actions workflows successfully shipped

### Applied Improvements

#### 1. **Safety Hooks to Prevent Wrong Assumptions**
   - **Finding:** 11 instances of wrong_approach, including modifying wrong files
   - **Action:** Created pre-tool-use hooks to block modifications to tests/, migrations/, configs
   - **Location:** `.claude/hooks/pre-tool-use.sh`
   - **Impact:** Prevents accidental modifications to protected files, forces verification before changes

#### 2. **Session Context Reminders**
   - **Finding:** Claude re-discovered project structure repeatedly
   - **Action:** Created session-start hook to display project context automatically
   - **Location:** `.claude/hooks/session-start.sh`
   - **Impact:** Faster onboarding, less time exploring familiar structures

#### 3. **Documentation Index in CLAUDE.md**
   - **Finding:** Tech stack and key docs not documented, causing re-discovery
   - **Action:** Added "Project Documentation" section with links to PRD, Architecture, Sprint Status
   - **Location:** `CLAUDE.md` - new section after "Sub-Agent Model Selection"
   - **Impact:** Agents can quickly find key documents instead of file tree exploration

#### 4. **MCP CLI Mode for Context Savings**
   - **Finding:** Large context window usage with 6 MCP servers preloaded
   - **Action:** Enabled `CLAUDE_CODE_EXPERIMENTAL_MCPCLI` for on-demand tool loading
   - **Location:** `.claude/settings.json` and `~/.claude/settings.json`
   - **Impact:** ~32% context window savings in MCP-heavy sessions

#### 5. **Global Templates Library**
   - **Finding:** Successful patterns (hooks, worktrees, multi-agent) should be reusable
   - **Action:** Created global templates library at `~/.claude/commands/templates/`
   - **Location:** `~/.claude/commands/templates/` with 6+ template files
   - **Impact:** <15 min setup time for new projects using proven patterns

### Recommendations for Future CLAUDE.md Additions

Based on insights analysis, consider adding these sections to CLAUDE.md:

1. **Agent Role Definitions**
   - Clearly define memory observer role (don't read files, only record events)
   - Define team-lead coordinator role
   - Define specialized agent roles (auditor, implementer, etc.)

2. **State Verification Before Execution**
   - "Before executing multi-step plans, verify current state first"
   - "Check if branches are reconciled, files exist, dependencies installed"
   - "Don't assume plan preconditions are still accurate"

3. **Don't Over-Engineer**
   - "Match exact structure specified in plans"
   - "Don't add features beyond what plan calls for"
   - "Ask before adding extras"

4. **Plan Mode Tool Access Check**
   - "Confirm tool access before proceeding in plan mode"
   - "If write tools unavailable, exit plan mode and request approval"
   - "Never loop in plan mode without progress"

5. **GitHub Actions Authentication Pattern**
   - "Always use two-step token generation pattern for GitHub App auth"
   - "Never pass credentials directly as action input parameters"

6. **Tech Stack Documentation**
   - Document core technologies (Python, TypeScript, YAML, Playwright)
   - List main projects (CurryDash, ACM-AI)
   - Note testing frameworks

### Deferred Improvements

The following insights require more investigation or user decision:

1. **Self-Healing CI with Autonomous Test Loops**
   - Opportunity: Auto-run tests, diagnose failures, fix, re-run until green
   - Requires: Testing strategy decision, autonomous fix approval workflow

2. **Credential Pre-validation System**
   - Opportunity: Pre-flight checks before launching complex workflows
   - Requires: Secure credential storage pattern, environment validation framework

3. **Consolidated Multi-Agent Audit Workflow**
   - Opportunity: Standardized audit workflow with shared findings schema
   - Requires: JSON schema definition, consolidation agent implementation

### Next Steps

1. **Monthly insights review:** Run `/insights` command monthly (next: 2026-03-15)
2. **Track friction reduction:** Compare next month's wrong_approach count vs baseline (11)
3. **Apply deferred improvements:** Evaluate self-healing CI and credential pre-validation
4. **Update global templates:** Extract new patterns as they emerge
5. **Measure impact:** Monitor session satisfaction rates (current: 77/109 satisfied)

### Success Metrics Baseline

- **Wrong approach instances:** 11 (target: <5 next month)
- **Satisfaction rate:** 70.6% (77/109 sessions)
- **Achievement rate:** 99.1% (108/109 sessions achieved goals)
- **Memory observer sessions:** 20+ (opportunity for skill consolidation)
- **Commits produced:** 28 in 4 days
- **Test success:** 116/116 E2E tests passing (improvement from 12 failing)
