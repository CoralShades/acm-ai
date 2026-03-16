---
name: post-task-progress
trigger: PostTask
description: Auto-update progress.md when a task completes, keeping planning files in sync with actual work.
---

# Post-Task Progress Update

After each task completion (commit or explicit "task done"):

1. Check if `progress.md` exists in the current working directory
2. If found:
   - Parse the checklist items (lines matching `- [ ]` or `- [x]`)
   - Match the completed task description against unchecked items
   - Check the matching item: `- [ ]` → `- [x]`
   - Update the "Last Updated" timestamp
   - Update aggregate metrics (e.g., "3 / 7 tasks complete")
3. If NOT found:
   - Do nothing (no progress tracking for this session)

This keeps the planning scaffold from `/planning-with-files` automatically synchronized with actual task completion.
