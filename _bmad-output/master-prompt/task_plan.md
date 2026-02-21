# Task Plan: Create Master Prompt for BMAD-Driven E2E Gap Analysis & Fix

## Goal
Create a comprehensive master prompt that uses BMAD workflows, agent teams, available skills, and MCP servers (including Playwright) to:
1. Diagnose WHY the E2E test scored 5.0/10 FAIL
2. Map failures to incomplete/missing stories in PRD/epics
3. Fix the identified issues
4. Re-test to verify

## Phases

### Phase 1: Research [complete]
- [ ] Get Claude sub-agent documentation (Task tool, agent teams, TeamCreate)
- [ ] Get skills documentation (available skills, how to invoke)
- [ ] Read E2E test findings from _bmad-output/e2e-test-2026-02-11/
- [ ] Read BMAD agent definitions from .claude/agents/
- [ ] Read BMAD workflow/skill definitions
- [ ] Read MCP server capabilities

### Phase 2: Analysis [complete]
- [ ] Map E2E failures to sprint stories
- [ ] Identify which BMAD workflows apply to each failure type
- [ ] Design agent team structure for the master prompt
- [ ] Define skill invocation sequence

### Phase 3: Compose Master Prompt [complete]
- [ ] Write the master prompt with full context
- [ ] Include agent team definitions
- [ ] Include BMAD workflow sequence
- [ ] Include MCP tool usage patterns
- [ ] Include planning-with-files integration

## Decisions
- (none yet)

## Errors Encountered
- (none yet)
