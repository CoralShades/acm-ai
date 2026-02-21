# Migration Guide: BMAD Configuration Update (2026-02-10)

## Summary

BMAD configuration has been updated to properly organize implementation artifacts. This guide helps you sync your local repository with the new structure.

## Changes Made

### 1. BMAD Configuration Update

**File**: `_bmad/bmm/config.yaml`

```yaml
# BEFORE
implementation_artifacts: "{project-root}/_bmad-output/implementation-artifacts" # ← was checking here
# Files were actually in: docs/sprint-artifacts/

# AFTER
implementation_artifacts: "{project-root}/_bmad-output/implementation-artifacts" # ← now files ARE here
# Files moved from: docs/sprint-artifacts/ → _bmad-output/implementation-artifacts/
```

### 2. File Reorganization

| File Type | Old Location | New Location |
|-----------|-------------|--------------|
| Sprint Status | `docs/sprint-artifacts/sprint-status.yaml` | `_bmad-output/implementation-artifacts/sprint-status.yaml` |
| Tech Specs | `docs/sprint-artifacts/tech-spec-*.md` | `_bmad-output/implementation-artifacts/tech-spec-*.md` |
| Story Specs | `docs/sprint-artifacts/e*.md` | `_bmad-output/implementation-artifacts/e*.md` |
| Workflow Status | `_bmad-output/bmm-workflow-status.yaml` | `_bmad-output/implementation-artifacts/bmm-workflow-status.yaml` |
| Project Index | `_bmad-output/bmm-index.md` | `_bmad-output/bmm-index.md` (unchanged) |

### 3. Tech Spec Cleanup

- **Epic 8 tech specs removed** (10 files): Epic 8 was archived and replaced by Epic 14
- **Backlog tech specs**: Remain in place but are considered outdated (will be recreated when needed)
- **Done/drafted/ready-for-dev tech specs**: Current and reviewed (kept as-is)

## Migration Steps for Developers

### If You Haven't Pushed Local Changes

```bash
# 1. Pull the latest changes
git pull origin main

# 2. Verify your BMAD config
cat _bmad/bmm/config.yaml | grep implementation_artifacts
# Should show: implementation_artifacts: "{project-root}/_bmad-output/implementation-artifacts"

# 3. Verify files are in the right place
ls _bmad-output/implementation-artifacts/sprint-status.yaml
# Should exist

# 4. Clean up old location (optional - can keep as archive)
# Do NOT delete docs/sprint-artifacts/ yet - it may have other files
```

### If You Have Local Changes in `docs/sprint-artifacts/`

```bash
# 1. Backup your local changes
cp docs/sprint-artifacts/sprint-status.yaml sprint-status.backup.yaml

# 2. Pull the latest changes
git pull origin main

# 3. If there are conflicts, resolve them
# Your changes: sprint-status.backup.yaml
# New location: _bmad-output/implementation-artifacts/sprint-status.yaml

# 4. Merge your changes if needed
# Compare and merge manually if you made local edits
```

### If You're on a Feature Branch

```bash
# 1. Commit your current work
git add .
git commit -m "wip: save current work before migration"

# 2. Checkout main and pull
git checkout main
git pull origin main

# 3. Return to your branch and rebase
git checkout your-feature-branch
git rebase main

# 4. Resolve any conflicts in the new file locations
# Old: docs/sprint-artifacts/sprint-status.yaml
# New: _bmad-output/implementation-artifacts/sprint-status.yaml
```

## What's Changed in Sprint Status

### E1-S13 Status
- **Before**: backlog
- **After**: done
- **Reason**: Agentic Extraction Orchestrator was implemented as E1-S20

### Epic 8 Status
- **Status**: archived (was already archived)
- **Reason**: Replaced by Epic 14 (UX & Enterprise Readiness)
- **Action**: All E8 tech specs removed

### Story Counts
- **Total**: 85 stories
- **Done**: 62 (73%)
- **Review**: 1
- **Ready-for-dev**: 4
- **Drafted**: 2
- **Backlog**: 14

## Verification Checklist

- [ ] BMAD config points to `_bmad-output/implementation-artifacts`
- [ ] `sprint-status.yaml` exists in `_bmad-output/implementation-artifacts/`
- [ ] Tech specs exist in `_bmad-output/implementation-artifacts/`
- [ ] Epic 8 tech specs are removed
- [ ] E1-S13 shows as "done" in sprint-status.yaml
- [ ] `/bmad:bmm:workflows:create-story` command works (finds sprint-status.yaml)

## Why This Change?

**Problem**: BMAD workflows were configured to look in `_bmad-output/implementation-artifacts/` but files were actually in `docs/sprint-artifacts/`. This caused workflows to fail when trying to find sprint status and story information.

**Solution**: Move implementation artifacts to the location where BMAD expects them (`_bmad-output/implementation-artifacts/`), maintaining consistency with the BMad Method's file organization conventions.

**Benefits**:
- Workflows work correctly without manual path adjustments
- Clear separation between:
  - Planning artifacts: `_bmad-output/project-planning-artifacts/acm-ai/`
  - Implementation artifacts: `_bmad-output/implementation-artifacts/`
  - General documentation: `docs/`
- Easier for new developers to understand project structure

## Need Help?

If you encounter issues:

1. Check that you're on the latest main branch
2. Verify file locations match this guide
3. Try re-running BMAD workflows to confirm they work
4. If still stuck, check git history: `git log --follow <filename>`

## Questions?

Common scenarios:

**Q: I have uncommitted changes in `docs/sprint-artifacts/sprint-status.yaml`**
A: Copy your file to `_bmad-output/implementation-artifacts/sprint-status.yaml` and commit from there.

**Q: Should I delete `docs/sprint-artifacts/`?**
A: No - keep it as an archive for now. It may still have useful files not moved.

**Q: My workflows still fail to find files**
A: Run `cat _bmad/bmm/config.yaml | grep artifacts` and verify the paths match this guide.

**Q: Which tech specs should I recreate?**
A: Only backlog story tech specs need recreation, and only when you're ready to work on that story. Done/drafted/ready-for-dev specs are current.

---

*Updated*: 2026-02-10
*Related PRs*: (add PR number when this is merged)
