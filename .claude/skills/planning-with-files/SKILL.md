# Planning with Files Skill

Persistent markdown-based planning system for session continuity. Adapted from [planning-with-files](https://github.com/OthmanAdi/planning-with-files).

## Three Planning Files

### `task_plan.md` — Active Task Tracker
- Maintained as a checklist of current work items
- Read before starting any implementation work
- Update checkboxes as tasks complete: `[ ]` → `[x]`
- Add new tasks discovered during implementation

### `findings.md` — Research & Discovery Log
- Record technical research, API exploration, architecture decisions
- Include sources, alternatives considered, and rationale
- Reference when making implementation decisions

### `progress.md` — Session Recovery Journal
- Log completed work at end of each session
- Include: what was done, key decisions, next steps
- Read at start of new sessions to recover context
- Contains the 5-question reboot check:
  1. What was the last completed milestone?
  2. What is the current active task?
  3. Are there any blockers?
  4. What files were last modified?
  5. What's the next planned action?

## When to Use
- **Session start:** Read `progress.md` to recover context
- **Before major decisions:** Read `findings.md` for prior research
- **Before implementation:** Read `task_plan.md` for current priorities
- **After completing work:** Update all three files as appropriate
- **Session end:** Update `progress.md` with session summary

## Hook Integration
This skill works with configured hooks in `.claude/settings.json`:
- **PreToolUse**: Reads `task_plan.md` before Write/Edit operations
- **PostToolUse**: Reminds to update `progress.md` after modifications
- **Stop**: Checks for pending tasks in `task_plan.md` before session end
