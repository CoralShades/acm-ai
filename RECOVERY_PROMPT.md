# Branch Recovery Prompt for Claude Code

**Copy and paste this entire prompt to Claude Code in the other developer's clone:**

---

I need to recover deleted branches from the CoralShades/acm-ai repository. These branches were accidentally deleted from GitHub today (2026-02-10) but should still exist in my local clone.

**Background:**
- 13 branches were accidentally deleted from GitHub
- My clone still has these branches locally
- I need to push them all back to restore them

**The deleted branches are:**
- E2-Update
- Epic1-S11
- Epic2, Epic2-07, Epic3-07, Epic4, Epic5, Epic6, Epic7, Epic8
- NewEpics
- feature/epic8-complete-with-testing
- claude/validate-workflow-extraction-aV5Yo
- romantic-leavitt (if it exists locally)

**Please do the following:**

1. **List all my local branches** and confirm which of the deleted branches still exist in my local clone

2. **For each branch that exists locally:**
   - Verify it has commits (show the last commit hash and message)
   - Push it to GitHub: `git push origin <branch-name>`
   - If the push fails, force-push with: `git push origin <branch-name> --force-with-lease`

3. **Create a summary table** showing:
   - Branch name
   - Last commit SHA
   - Last commit message
   - Push status (✅ success / ❌ failed)

4. **Verify on GitHub** by checking that all branches now appear in the remote

5. **Important notes:**
   - Do NOT delete any branches
   - Do NOT modify any branch history
   - Only push existing branches to restore them on GitHub
   - If any branch has uncommitted changes, stash them first
   - Skip pushing `main` and `lane-b` if they already exist on remote

**Expected outcome:**
All deleted branches should be restored on GitHub with their complete history intact.

---

**Additional context for Claude:**
- Repository: CoralShades/acm-ai
- Branches were deleted at: 2026-02-10 00:50 UTC
- Target: Restore all branches to origin (GitHub)
- Method: Simple push of existing local branches
