# Findings: Master Prompt Research

## E2E Test Failure -> Story Mapping (15 failures mapped)

| # | Failure | Severity | Story | Status | Gap Type |
|---|---------|----------|-------|--------|----------|
| 1 | Negative records skipped (20/31) | Critical | E1-S7 | Done | Incomplete AC |
| 2 | Race condition (acm_extract before process_source) | Critical | E1-S5/E1-S20 | Done | Missing AC |
| 3 | Model config not persisted (OpenRouter 404) | Critical | NONE | N/A | Missing Story |
| 4 | Compliance fields missing from API | Critical | E1-S4 | Done | Incomplete AC |
| 5 | Product/location column confusion | High | E1-S7 | Done | Prompt quality |
| 6 | location field always null | High | E1-S7 | Done | Prompt quality |
| 7 | Result conflates Positive/Assumed Positive | High | E1-S3 | Done | Incomplete AC |
| 8 | building_name empty | Medium | E1-S17 | Done | Incomplete AC |
| 9 | page_number empty | Medium | E3-S4/E1-S13 | Done | Incomplete impl |
| 10 | Friable dropdown blank | Medium | E1-S9/E14-S11 | Done | Enum mismatch |
| 11 | Search filter broken | Medium | E2-S6 | Done | Incomplete impl |
| 12 | False positive record | Medium | E1-S15 | Done | Validation gap |
| 13 | school_name = filename | Low | E1-S19 | Done | Metadata quality |
| 14 | area_type "Interior" vs "Internal" | Low | E1-S3 | Done | Enum normalization |
| 15 | Classification never populated | Low | E1-S9 | Done | Not integrated |

## Gap Type Distribution
- Incomplete Acceptance Criteria: 7 stories
- Missing Story: 2 (model validation, command dependencies)
- Incomplete Implementation: 2 (page numbers, search filter)
- Prompt Engineering Quality: 3 (product/location, school_name, negatives)
- Enum/Vocabulary Mismatch: 3 (friable, area_type, result)
- Validation Incomplete: 1 (false positive detection)

## BMAD Workflow Sequence
1. `/bmad:bmm:workflows:sprint-status` - Current state assessment
2. 3-agent gap analysis team (analyst + extraction-core + schema-expert)
3. `/bmad:bmm:workflows:correct-course` - Sprint change proposal
4. `/bmad:bmm:agents:sm` - Apply changes to sprint artifacts
5. 5-agent implementation team (sprint-lead + 3 devs + QA)
6. `/bmad:bmm:workflows:dev-story` - Per-task execution
7. 5-agent E2E re-test team
8. `/bmad:bmm:workflows:retrospective` - Lessons learned

## Agent Team Architecture
- **Phase 1**: 3 agents (analyst, extraction-reviewer, schema-reviewer) - parallel gap analysis
- **Phase 3**: 5 agents (sprint-lead, backend-dev, extraction-specialist, schema-dev, qa-tester) - implementation
- **Phase 4**: 5 agents (health-checker, log-monitor, browser-pilot, data-validator, reporter) - re-test
- Total: 13 agent spawns across 3 team instances

## MCP Servers Available
- Playwright: Browser automation for E2E testing (browser_navigate, browser_snapshot, etc.)
- GitHub: Issue management (issue_read, issue_write, add_issue_comment)
- Memory: Persistent context (save_memory, search, get_observations)
- Serena: Semantic code tools (find_symbol, replace_symbol_body)
- Context7: Library documentation lookup
- Firebase: Not relevant to this task
