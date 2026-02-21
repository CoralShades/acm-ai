# E2E Gap Analysis - Implementation Guide

## Overview

This guide provides BMAD workflow guidance for implementing the 5 stories identified through E2E gap analysis. Use agent teams with sonnet model for systematic implementation.

---

## Story Implementation Order

Prioritize by business impact:

1. **#29: e2e-ci-github-actions-setup** (P0 CRITICAL) - Deploy CI/CD first to prevent regression
2. **#25: E1-S24** (HIGH) - Fix assumed positive detection (2 missing records)
3. **#26: E1-S25** (MEDIUM) - Fix external/internal merging (1 missing record)
4. **#28: E1-S27** (LOW) - Handle duplicate room items (1 missing record)
5. **#27: E1-S26** (MEDIUM) - Reduce false positives (quality improvement)

---

## Workflow 1: CI/CD Setup - e2e-ci-github-actions-setup (#29)

**Workflow**: `bmad:bmm:workflows:testarch-ci`

**Description**: Set up GitHub Actions E2E testing pipeline to prevent accuracy regression from 87% back to 26%.

### Team Structure (2 agents, sonnet model)

1. **CI/CD Specialist** (`ci-lead`) - Designs GitHub Actions workflow
2. **Test Engineer** (`ci-tester`) - Validates workflow, creates test matrix

### Implementation Command

```bash
# Create team and spawn agents
bmad:bmm:workflows:testarch-ci

# Or use Task tool directly:
Task(
  description="Implement e2e-ci-github-actions-setup: GitHub Actions E2E pipeline",
  subagent_type="testarch-ci",
  team_name="ci-cd-setup",
  name="ci-pipeline",
  model="sonnet",
  prompt="""
Set up GitHub Actions E2E testing pipeline:
- Create .github/workflows/e2e-tests.yml
- Run all 34 Playwright tests on PR events
- Upload test artifacts (videos, traces, HTML reports)
- Configure matrix testing (optional: browsers)
- Use official Playwright GitHub Actions
- Follow testarch-ci workflow

Template available in: _bmad-output/e2e-test-suite/browser-pilot/findings.md

Target: Prevent regression from 87% → 26% extraction accuracy
  """
)
```

### Critical Files

- `.github/workflows/e2e-tests.yml` (to be created)
- `playwright.config.ts` (may need CI-specific tweaks)
- `.github/workflows/claude-code-review.yml` (for reference)

### Success Criteria

- [ ] Workflow created and committed
- [ ] Workflow runs on PR events
- [ ] All 34 tests execute successfully
- [ ] Artifacts uploaded (HTML reports, videos, traces)
- [ ] PR status checks enabled

### Estimated Effort

3-5 hours

---

## Workflow 2: Extraction Quality Fixes - E1-S24, E1-S25, E1-S26, E1-S27

**Workflow**: `bmad:bmm:workflows:dev-story`

**Description**: Fix extraction algorithm gaps to improve from 87% to 95%+ accuracy.

### Team Structure (3 agents, sonnet model)

1. **Tech Lead** (`extraction-lead`) - Coordinates implementation, reviews code
2. **Backend Dev** (`extraction-dev`) - Implements extraction algorithm fixes
3. **Test Engineer** (`extraction-tester`) - Writes/updates tests, validates fixes

### Implementation Command

Execute stories in priority order (E1-S24 → E1-S25 → E1-S27 → E1-S26):

```bash
# Example for E1-S24
bmad:bmm:workflows:dev-story

# Or use Task tool directly:
Task(
  description="Implement E1-S24: Fix assumed positive detection",
  subagent_type="dev-story",
  team_name="extraction-fixes",
  name="story-e1-s24",
  model="sonnet",
  prompt="""
Execute story E1-S24 from GitHub issue #25:
- Fix assumed positive ACM detection (50% → 90% recall)
- Handle "No access" entries correctly
- Extract missing records #30 and #31
- Update tests in tests/e2e/acm-extraction.spec.ts
- Follow dev-story workflow: spec → TDD → implement → test → document

Technical context:
- Source: Broadmeadows Police Station SAMP
- Current: 87% overall (27/31 records)
- Target: 90%+ overall (28+/31 records)
  """
)
```

### Per-Story Workflow

For each story (E1-S24, E1-S25, E1-S26, E1-S27):

1. **Tech Lead** creates tech spec from GitHub issue
2. **Test Engineer** writes failing tests (TDD red phase)
3. **Backend Dev** implements algorithm fix (TDD green phase)
4. **Test Engineer** validates fix and refactors (TDD refactor phase)
5. **Tech Lead** reviews code and approves
6. Create PR and merge

### Critical Files for All Extraction Fixes

- `open_notebook/extractors/acm_extractor.py` - Main extraction logic
- `prompts/acm/extraction.jinja` - Extraction prompt template
- `tests/test_acm_ai_extraction.py` - Unit tests
- `tests/e2e/acm-extraction.spec.ts` - E2E tests

### Story-Specific Details

#### E1-S24: Fix Assumed Positive Detection (#25)

**Priority**: HIGH
**Impact**: 2 missing records
**Root Cause**: Low-detail "No access" entries filtered out
**Fix Location**: `open_notebook/extractors/acm_extractor.py` (line ~150-200)

**Algorithm Change**:
- Accept entries with "No access" annotation
- Map "No access" to "Assumed Positive" result
- Preserve location and material type even with limited detail

**Test Cases**:
- Extract record #30 (Lift Foyer - Internal lining)
- Extract record #31 (Main Foyer - Unknown material)
- Verify 6/6 assumed positive records extracted

#### E1-S25: Fix External/Internal Merging (#26)

**Priority**: MEDIUM
**Impact**: 1 missing record
**Root Cause**: Room-based deduplication merges external/internal locations
**Fix Location**: `open_notebook/extractors/acm_extractor.py` (line ~250-300)

**Algorithm Change**:
- Include location qualifier (External/Internal) in deduplication key
- Preserve "Fan Room (External)" separate from "Fan Room"
- Update room name normalization logic

**Test Cases**:
- Extract record #20 (Fan Room (External) - AHU Ductwork)
- Verify "Fan Room (External)" ≠ "Fan Room" in deduplication
- Preserve all location qualifiers

#### E1-S26: Reduce False Positives (#27)

**Priority**: MEDIUM
**Impact**: Quality improvement (precision 87.5% → 95%+)
**Root Cause**: Occasional hallucination creates non-existent records
**Fix Location**: `prompts/acm/extraction.jinja` + `open_notebook/extractors/acm_extractor.py`

**Algorithm Change**:
- Add prompt instruction: "Only extract records explicitly present in source"
- Implement post-extraction validation against source text
- Add confidence threshold for extraction (>0.8)

**Test Cases**:
- Verify no "Ceiling Space" record created
- Precision >95% on Broadmeadows SAMP
- All extracted records verifiable in source

#### E1-S27: Handle Duplicate Room Items (#28)

**Priority**: LOW
**Impact**: 1 missing record
**Root Cause**: Multiple items in same room deduplicated
**Fix Location**: `open_notebook/extractors/acm_extractor.py` (line ~250-300)

**Algorithm Change**:
- Include material/component in deduplication key
- Preserve distinct items: "Switch Room - Fire Alarm" ≠ "Switch Room - Battery Charger"
- Update deduplication to use (room + material + component) tuple

**Test Cases**:
- Extract both #8 and #9 Switch Room records
- Verify distinct materials preserved within same room
- No duplicate items in same location with same material

### Success Criteria (All Stories)

- [ ] All 31 Broadmeadows records extracted (100% recall)
- [ ] Precision >95% (false positive rate <5%)
- [ ] E2E tests pass (tests/e2e/acm-extraction.spec.ts)
- [ ] Unit tests updated and passing
- [ ] Code reviewed and approved
- [ ] Documentation updated

### Estimated Effort (Per Story)

- E1-S24: 5-8 hours (HIGH priority, complex logic)
- E1-S25: 3-5 hours (MEDIUM priority, focused change)
- E1-S26: 5-8 hours (MEDIUM priority, prompt + validation)
- E1-S27: 3-5 hours (LOW priority, deduplication logic)

**Total**: 16-26 hours for all 4 extraction fixes

---

## Combined Timeline

| Phase | Task | Effort | Priority |
|-------|------|--------|----------|
| 1 | e2e-ci (#29) | 3-5h | P0 CRITICAL |
| 2 | E1-S24 (#25) | 5-8h | HIGH |
| 3 | E1-S25 (#26) | 3-5h | MEDIUM |
| 4 | E1-S27 (#28) | 3-5h | LOW |
| 5 | E1-S26 (#27) | 5-8h | MEDIUM |

**Total Estimated Effort**: 19-31 hours

---

## Recommended Approach

### This Sprint (Immediate)

1. **Deploy CI/CD first** (#29) - 3-5 hours
   - Prevents regression from 87% → 26%
   - Enables automated validation of all future fixes
   - Use `testarch-ci` workflow

2. **Fix highest impact gaps** (#25, #26) - 8-13 hours
   - E1-S24: +2 records (50% → 90% assumed positive recall)
   - E1-S25: +1 record (external/internal distinction)
   - Combined: 87% → 90%+ extraction accuracy
   - Use `dev-story` workflow

### Next Sprint (Follow-up)

3. **Quality improvements** (#27, #28) - 8-13 hours
   - E1-S26: Reduce false positives (precision 87.5% → 95%+)
   - E1-S27: +1 record (duplicate room items)
   - Combined: 90% → 95%+ with <5% false positive rate
   - Use `dev-story` workflow

---

## Agent Team Best Practices

### Model Selection

- **ALWAYS use `model="sonnet"`** for team members (per CLAUDE.md requirement)
- **NEVER use `model="opus"`** for team members (cost control)
- Use `model="haiku"` only for simple, focused tasks

### Team Coordination

- Tech Lead coordinates work and reviews PRs
- Backend Dev implements algorithm changes
- Test Engineer ensures quality via TDD
- All agents communicate via TaskList and TaskUpdate

### Workflow Steps

1. **Spec Phase**: Tech Lead creates tech spec from GitHub issue
2. **Red Phase**: Test Engineer writes failing tests
3. **Green Phase**: Backend Dev implements fix to pass tests
4. **Refactor Phase**: Test Engineer optimizes and validates
5. **Review Phase**: Tech Lead reviews and approves
6. **Deploy Phase**: Create PR, merge, verify in CI

---

## Verification Checklist

After implementing each story:

- [ ] Build passes (`npm run build`, `uv run ruff check .`)
- [ ] Unit tests pass (`uv run pytest`)
- [ ] E2E tests pass (`npm run test:e2e`)
- [ ] GitHub issue acceptance criteria met
- [ ] PR created with semantic commit message
- [ ] Code review completed
- [ ] GitHub Actions CI passes
- [ ] Issue closed with reference to PR

---

## Resources

- **E2E Test Suite**: `_bmad-output/e2e-test-suite/`
- **Executive Summary**: `_bmad-output/e2e-test-suite/EXECUTIVE-SUMMARY.md`
- **Gap Analysis**: `_bmad-output/e2e-test-suite/reporter/scorecard.md`
- **GitHub Actions Template**: `_bmad-output/e2e-test-suite/browser-pilot/findings.md`
- **Sprint Status**: `docs/sprint-artifacts/sprint-status.yaml`
- **GitHub Issues**: #25, #26, #27, #28, #29

---

## Next Steps

1. Review this implementation guide
2. Start with #29 (CI/CD setup) to establish automated testing
3. Execute #25 and #26 to reach 90%+ accuracy
4. Continue with #27 and #28 for 95%+ target
5. Verify all changes via automated E2E tests in CI

**Expected Outcome**: 95%+ extraction accuracy with zero regression risk via automated CI/CD pipeline.
