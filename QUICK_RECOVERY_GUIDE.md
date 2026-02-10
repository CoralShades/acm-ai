# Quick Branch Recovery Guide

## 🚨 For Other Developer (has the branches)

**Copy this entire prompt to Claude Code:**

```
I have a git repository clone with branches that were accidentally deleted from GitHub.
I need to push these branches back to restore them:

Branches to recover:
- E2-Update, Epic1-S11, Epic2, Epic2-07, Epic3-07, Epic4, Epic5, Epic6, Epic7, Epic8
- NewEpics, feature/epic8-complete-with-testing, claude/validate-workflow-extraction-aV5Yo

Please:
1. List all my local branches
2. For each branch above that exists locally:
   - Show me the last commit
   - Push it to origin: git push origin <branch-name>
   - If push fails, use: git push origin <branch-name> --force-with-lease
3. Create a summary showing which branches were successfully pushed
4. Do NOT delete any branches
5. Do NOT modify any history

Repository: CoralShades/acm-ai
```

---

## ✅ For You (waiting for recovery)

**After other developer confirms they pushed:**

```bash
# Run this in your clone
./verify-recovery.sh
```

**That's it!** The script will:
- Fetch latest from GitHub
- Check all 13 branches
- Show which are recovered
- Tell you what to do next

---

## 📞 If Problems

**Branch won't push:**
→ Other developer should use `--force-with-lease`

**Branch missing in their clone:**
→ Check if anyone else has the repo, or contact GitHub Support

**Push succeeded but verify fails:**
→ Wait 1 minute and run `./verify-recovery.sh` again

---

## ⏱️ Timeline

- **5 minutes:** Other developer pushes branches
- **1 minute:** You verify recovery
- **Done!** All branches restored

---

## 📄 Full Details

See `RECOVERY_INSTRUCTIONS.md` for complete step-by-step guide.
