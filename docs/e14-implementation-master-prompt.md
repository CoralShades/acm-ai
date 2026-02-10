# Epic 14 Implementation Master Prompt: The Ralph Loop

> **Version:** 1.0
> **Created:** 2026-02-08
> **Branch:** `lane-b`
> **Worktree:** `/mnt/d/ailocal/acm-ai-frontend/`
> **Purpose:** Systematically implement all 11 E14 stories with verification at every step

---

## How to Use This Prompt

Copy everything below the `---` separator and paste it into a new Claude Code session on the `lane-b` branch. The prompt will:

1. Initialize progress tracking via `/planning-with-files`
2. Spawn an agent team (dev, UX audit, testing)
3. Execute each story through The Ralph Loop
4. Commit after each verified story
5. Continue until all 11 stories are complete

---

## Master Prompt (paste into Claude Code)

```
You are the **E14 Sprint Lead** implementing Epic 14: UX & Enterprise Readiness for ACM-AI.

## Setup Phase

### Step 1: Initialize Progress Tracking

Run `/planning-with-files` to create:
- `task_plan.md` -- Story execution queue and current focus
- `progress.md` -- Per-story progress (separate from BMAD sprint-status.yaml)
- `findings.md` -- Issues discovered during implementation

Initialize `task_plan.md` with this story queue (in implementation order):

| # | Story | Priority | Tech Spec | Status |
|---|-------|----------|-----------|--------|
| 1 | E14-S1 | P0 | tech-spec-e14-s1-vaea-branding-design-tokens.md | pending |
| 2 | E14-S3 | P0 | tech-spec-e14-s3-hide-brownfield-features.md | pending |
| 3 | E14-S2 | P0 | tech-spec-e14-s2-sidebar-navigation.md | pending |
| 4 | E14-S4 | P1 | tech-spec-e14-s4-skeleton-loading-screens.md | pending |
| 5 | E14-S5 | P1 | tech-spec-e14-s5-toast-system.md | pending |
| 6 | E14-S7 | P1 | tech-spec-e14-s7-unified-documents-view.md | pending |
| 7 | E14-S6 | P1 | tech-spec-e14-s6-wcag-accessibility.md | pending |
| 8 | E14-S8 | P2 | tech-spec-e14-s8-error-recovery-disconnect.md | pending |
| 9 | E14-S9 | P2 | tech-spec-e14-s9-keyboard-navigation.md | pending |
| 10 | E14-S10 | P2 | tech-spec-e14-s10-breadcrumb-navigation.md | pending |
| 11 | E14-S11 | P2 | tech-spec-e14-s11-pydantic-typescript-types.md | pending |

**NOTE:** S3 before S2 because S3 is independent while S2 depends on S1. S7 before S6 because S6 (accessibility audit) benefits from having all UI changes in place first.

### Step 2: Read CLAUDE.md and Existing Architecture

Read these files to understand project patterns:
- `CLAUDE.md` (project rules, commands, verification protocol)
- `frontend/src/app/globals.css` (current design tokens)
- `frontend/src/components/layout/AppSidebar.tsx` (current sidebar)
- `frontend/tailwind.config.ts` (current Tailwind config)

---

## The Ralph Loop (per story)

For EACH story in the queue, execute this loop:

### Phase 1: PLAN (use haiku model for reading)

1. Read the story's tech spec from `_bmad-output/sprint-artifacts/`
2. Read the referenced spec documents (listed in tech spec header)
3. Read ALL files listed in the "File Changes" table
4. Update `progress.md` with story start timestamp and planned changes
5. If the story has complex changes (5+ files), use `/planning-with-files` to create a sub-plan

### Phase 2: IMPLEMENT (use sonnet model)

1. Spawn a **dev agent** (subagent_type: `general-purpose`) with this prompt pattern:

```
Implement story [E14-SX] per the tech spec at _bmad-output/sprint-artifacts/tech-spec-e14-sX-[slug].md.

RULES:
- Read the tech spec FIRST, then read every file in the File Changes table
- Follow code samples in the Technical Design section exactly
- Use existing project patterns (see CLAUDE.md)
- Do NOT add extra features, comments, or refactoring beyond what the spec requires
- Acceptance criteria checkboxes are your definition of done
- After implementation, run: cd frontend && npm run build
- If build fails, fix the errors before finishing

FILES TO READ FIRST:
[List the key files from the tech spec]

CONTEXT:
- Branch: lane-b
- Tech stack: Next.js 15, React 19, Tailwind CSS 4, Zustand, Radix UI
- Design tokens: OKLCH color space in globals.css
- This is story [X] of 11 in Epic 14
```

2. Wait for the dev agent to complete
3. Verify the dev agent ran `npm run build` successfully

### Phase 3: VERIFY (use haiku model for checks)

Run these verification checks sequentially:

```bash
# 1. Build verification (REQUIRED)
cd frontend && npm run build

# 2. Lint check
cd frontend && npm run lint

# 3. TypeScript check (if available)
cd frontend && npx tsc --noEmit 2>/dev/null || echo "No tsconfig strict mode"
```

Then verify file existence:
- Use Glob to confirm every file in the tech spec's "File Changes" table exists
- If ANY file is missing, the story is INCOMPLETE -- go back to Phase 2

### Phase 4: UX AUDIT (use sonnet model)

Spawn a **UX audit agent** (subagent_type: `general-purpose`) with:

```
You are a UX auditor reviewing story [E14-SX] implementation.

1. Read the tech spec: _bmad-output/sprint-artifacts/tech-spec-e14-sX-[slug].md
2. Read the ACCEPTANCE CRITERIA section carefully
3. For each criterion, verify it was implemented by reading the relevant source files
4. Check for:
   - VAEA design token usage (not hardcoded colors)
   - Accessibility: aria-labels, keyboard navigation, focus indicators
   - Dark mode support (if applicable)
   - Responsive behavior (if applicable)
   - No console.log or debug code left behind
5. Report: PASS (all criteria met) or FAIL (list specific failures)

Do NOT modify any files. Read-only audit.
```

If the UX audit reports FAIL:
- Log failures in `findings.md`
- Go back to Phase 2 to fix specific issues
- Re-run Phase 3 and Phase 4

### Phase 5: COMMIT & RECORD

1. Stage only the files changed for this story (no `git add .`)
2. Commit with conventional commit message:
   ```
   feat(e14-sX): [short description]

   Implements E14-SX: [Story Title]

   - [Key change 1]
   - [Key change 2]
   - [Key change 3]

   Tech spec: _bmad-output/sprint-artifacts/tech-spec-e14-sX-[slug].md

   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
   ```
3. Update `progress.md`:
   - Mark story as `done` with completion timestamp
   - Record build status, lint status, UX audit result
   - List files modified
4. Update `task_plan.md`: Mark story as `done`, advance to next story

### Phase 6: NEXT STORY

- Read `task_plan.md` to find the next `pending` story
- If all stories are `done`, proceed to Final Verification
- Otherwise, start Phase 1 for the next story

---

## Model Optimization Guide

Use the cheapest effective model for each task:

| Task | Model | Rationale |
|------|-------|-----------|
| Reading files, status checks, glob/grep | haiku | Pure I/O, no reasoning needed |
| Build/lint/verify commands | haiku | Just running commands |
| Code implementation (dev agent) | sonnet | Good code generation, cost-effective |
| UX audit (review agent) | sonnet | Needs reasoning about UI patterns |
| Complex architectural decisions | opus | Only when stuck or ambiguous |
| Planning sub-tasks | haiku | File management |
| Commit message writing | haiku | Formulaic output |

**Cost Rule:** Start with haiku. Escalate to sonnet only when the task requires code generation or nuanced reasoning. Use opus only for debugging complex failures or architectural judgment calls.

---

## Progress File Format

### progress.md

```markdown
# E14 Implementation Progress

## Current Story: E14-S1
## Stories Completed: 0/11
## Last Updated: [timestamp]

---

### E14-S1: VAEA Branding & Design Tokens
- **Status:** [pending|in-progress|done|blocked]
- **Started:** [timestamp]
- **Completed:** [timestamp]
- **Build:** [PASS|FAIL]
- **Lint:** [PASS|FAIL]
- **UX Audit:** [PASS|FAIL]
- **Files Modified:** [list]
- **Commit:** [hash]
- **Notes:** [any issues encountered]

### E14-S3: Hide Brownfield Features
- **Status:** pending
...
```

### findings.md

```markdown
# E14 Implementation Findings

## Issues Found During Implementation

### [Story ID] - [Issue Title]
- **Severity:** [blocker|major|minor]
- **Found in:** [Phase where discovered]
- **Description:** [What's wrong]
- **Resolution:** [How it was fixed]
- **Files affected:** [list]
```

---

## Final Verification (after all 11 stories)

After all stories are implemented:

1. **Full build test:**
   ```bash
   cd frontend && rm -rf .next && npm run build
   ```

2. **Full lint:**
   ```bash
   cd frontend && npm run lint
   ```

3. **Cross-story integration check:**
   Spawn a review agent to verify:
   - All VAEA tokens are consistent across components
   - Sidebar navigation matches spec (WORKSPACE + CONFIGURE)
   - No brownfield features visible in nav
   - Skeleton screens load on all major pages
   - Toast system works with extraction/export flows
   - Breadcrumbs appear on detail pages
   - Keyboard shortcuts work (Cmd+K, ?, Escape)
   - Error boundaries catch route-level errors

4. **Update BMAD tracking:**
   - Update `progress.md` with final summary
   - Note: Do NOT modify `sprint-status.yaml` (Lane A owned)
   - The change proposal at `_bmad-output/sprint-artifacts/change-proposal-epic-14.md`
     should be updated to reflect completed stories

5. **Final commit:**
   ```
   docs: update E14 progress tracking after full implementation
   ```

---

## Recovery Protocol

If a session runs out of context mid-story:

1. The new session reads `progress.md` to know where we left off
2. The new session reads `task_plan.md` for the story queue
3. The new session reads `findings.md` for known issues
4. Resume at the current story's current phase
5. This is why /planning-with-files progress is critical -- it survives session boundaries

If a story is blocked:

1. Log the blocker in `findings.md`
2. Mark story as `blocked` in `task_plan.md` with reason
3. Skip to next non-blocked story
4. Return to blocked story after blocker is resolved

---

## Key Files Reference

| Category | Path |
|----------|------|
| Tech Specs | `_bmad-output/sprint-artifacts/tech-spec-e14-s*.md` |
| Design System | `docs/design-system.md` |
| Navigation Spec | `docs/navigation-cleanup-spec.md` |
| Loading/State Spec | `docs/state-loading-spec.md` |
| UX Audit | `docs/ux-audit.md` |
| UI/UX Spec | `docs/ui-ux-spec.md` |
| Pipeline Spec | `docs/ag-ui-pipeline-spec.md` |
| Change Proposal | `_bmad-output/sprint-artifacts/change-proposal-epic-14.md` |
| Current Tokens | `frontend/src/app/globals.css` |
| Current Sidebar | `frontend/src/components/layout/AppSidebar.tsx` |
| Tailwind Config | `frontend/tailwind.config.ts` |
| Branding | `frontend/src/config/branding.ts` |
| Logo | `frontend/src/components/brand/Logo.tsx` |

---

## Critical Rules

1. **One story at a time.** Complete the Ralph Loop for each story before starting the next.
2. **Build must pass.** Never commit if `npm run build` fails.
3. **No scope creep.** Implement exactly what the tech spec says. No extras.
4. **Progress is sacred.** Update progress.md after every phase change.
5. **Files over memory.** Use /planning-with-files to persist state across sessions.
6. **Verify before commit.** Every story passes build + lint + UX audit.
7. **Cheap models first.** Use haiku for reading, sonnet for coding, opus only when stuck.
8. **Lane B only.** Never modify backend code or sprint-status.yaml.
9. **Preserve existing.** Brownfield features are hidden, not deleted.
10. **Recovery-ready.** Any new session can pick up from progress.md.
```
