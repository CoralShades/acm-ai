# Branch Recovery Instructions

## What Happened
13 development branches were accidentally deleted from the CoralShades/acm-ai repository on 2026-02-10. These branches still exist in other local clones and need to be pushed back to GitHub.

## Deleted Branches
- E2-Update
- Epic1-S11
- Epic2, Epic2-07, Epic3-07, Epic4, Epic5, Epic6, Epic7, Epic8
- NewEpics
- feature/epic8-complete-with-testing
- claude/validate-workflow-extraction-aV5Yo
- romantic-leavitt

---

## Recovery Process

### Step 1: Other Developer (has the branches)

**Send them this file:** `RECOVERY_PROMPT.md`

They should:
1. Open their local clone of the repository
2. Open Claude Code
3. Copy and paste the entire content of `RECOVERY_PROMPT.md` into Claude Code
4. Let Claude Code execute the recovery process
5. Verify all branches were pushed successfully

**Expected output from Claude Code:**
- A list of all local branches
- Push status for each branch (✅ success)
- Confirmation that branches now exist on GitHub

---

### Step 2: You (verification)

Once the other developer confirms they've pushed the branches:

**Option A: Run the verification script**
```bash
./verify-recovery.sh
```

**Option B: Manual verification**
```bash
# Fetch latest from GitHub
git fetch origin --prune

# List all remote branches
git branch -r

# Check specific branch
git ls-remote --heads origin Epic1-S11
```

**Expected result:** All 13 branches should appear in `git branch -r`

---

### Step 3: Update Your Local Repository

Once branches are back on GitHub:

```bash
# Fetch all branches
git fetch origin

# Create local tracking branches (optional)
git checkout Epic1-S11    # Creates local branch tracking origin/Epic1-S11
git checkout Epic2
# ... etc for each branch you need to work on
```

---

## Troubleshooting

### If some branches don't push:

**Error: "rejected - non-fast-forward"**
```bash
# Other developer should force-push
git push origin <branch-name> --force-with-lease
```

### If branch doesn't exist in other clone:

That branch is lost. Options:
1. Check if anyone else has a clone
2. Contact GitHub Support (branches kept for 30 days)
3. Recreate the branch from scratch if needed

### If you get "branch already exists":

Good! It's already recovered. Skip to Step 2.

---

## After Recovery

### Optional: Apply author cleanup to recovered branches

If you want to clean up the contributor history on these branches too:

1. **DO NOT DELETE THE BRANCHES**
2. Instead, apply author filtering to each branch:

```bash
# For each branch
git checkout <branch-name>

# Apply author cleanup (run this carefully)
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f --env-filter '
if [ "$GIT_AUTHOR_NAME" = "LUIS NOVO" ] || [ "$GIT_AUTHOR_NAME" = "Luis Novo" ] || [ "$GIT_AUTHOR_NAME" = "Troy Kelly" ] || [ "$GIT_AUTHOR_NAME" = "dependabot[bot]" ] || [ "$GIT_AUTHOR_NAME" = "heecheol.park" ] || [ "$GIT_AUTHOR_NAME" = "Bui Thanh Son" ] || [ "$GIT_AUTHOR_NAME" = "熊鑫伟 Xinwei Xiong" ] || [ "$GIT_AUTHOR_NAME" = "OrbisAI Sec" ] || [ "$GIT_AUTHOR_NAME" = "Suvrat Jain" ] || [ "$GIT_AUTHOR_NAME" = "dkdnd" ] || [ "$GIT_AUTHOR_NAME" = "neo" ] || [ "$GIT_AUTHOR_NAME" = "pchuri" ]; then
    export GIT_AUTHOR_NAME="demigod97"
    export GIT_AUTHOR_EMAIL="demi@coralshades.ai"
    export GIT_COMMITTER_NAME="demigod97"
    export GIT_COMMITTER_EMAIL="demi@coralshades.ai"
fi
if [ "$GIT_AUTHOR_NAME" = "sanju96" ] || [ "$GIT_AUTHOR_NAME" = "Sanju" ]; then
    export GIT_AUTHOR_NAME="sanju-cmyk"
fi
if [ "$GIT_AUTHOR_EMAIL" = "40735979+demigod97@users.noreply.github.com" ]; then
    export GIT_AUTHOR_EMAIL="demi@coralshades.ai"
fi
if [ "$GIT_COMMITTER_EMAIL" = "40735979+demigod97@users.noreply.github.com" ]; then
    export GIT_COMMITTER_EMAIL="demi@coralshades.ai"
fi
' <branch-name>

# Force push the cleaned branch
git push origin <branch-name> --force
```

---

## Summary

1. ✅ Other developer pushes branches from their clone
2. ✅ You verify branches are back on GitHub
3. ✅ You fetch and can work with branches again
4. ⏩ (Optional) Apply author cleanup later if needed

**Timeline:** This should take less than 10 minutes once the other developer starts.

---

## Questions?

- **How long will this take?** 5-10 minutes for the other developer to push all branches
- **Will I lose any work?** No - the branches exist in the other clone with full history
- **Do I need to do anything special?** No - just wait for confirmation then run `verify-recovery.sh`
- **What if a branch is truly lost?** Contact GitHub Support or recreate from scratch

---

## Contact

If you need help during recovery, the other developer can share their Claude Code session output for troubleshooting.
