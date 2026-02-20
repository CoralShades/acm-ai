Generate a sprint status board from BMAD story files.

## Steps

### 1. Discover Stories
- Read all `.md` files in `_bmad-output/implementation-artifacts/` matching pattern `e*-s*.md`
- If no implementation-artifacts directory exists, fall back to `_bmad-output/planning-artifacts/`
- Skip non-story files (findings.md, progress.md, task_plan.md, tech-spec-*.md, bug-*.md, phase*.md)

### 2. Parse Each Story
For each story file, extract:
- **Story ID**: From filename (e.g., `e1-s7` from `e1-s7-ai-powered-acm-extraction.md`)
- **Title**: From the first `# Story` heading (e.g., `Story 1.7: AI-Powered ACM Extraction`)
- **Status**: From the `Status:` line (`done`, `in progress`, `not started`, or infer from task checkboxes)
- **AC Count**: Count acceptance criteria (lines with `**AC` or numbered criteria under `## Acceptance Criteria`)
- **Checked ACs**: Count checked acceptance criteria (lines with `- [x]`)

### 3. Cross-Reference with Git
- Run `git log --oneline --all` to check for story-related commits
- Look for commits mentioning story IDs (e.g., `e1-s7`, `E1-S7`)
- Look for feature branches matching `feature/story-*`
- Use this to validate or update status (e.g., story has commits but Status says "not started")

### 4. Output Sprint Board
Print a formatted sprint board:

```
# Sprint Status — [Current Date]

## Done ✅
| Story ID | Title | ACs |
|----------|-------|-----|
| E1-S7    | AI-Powered ACM Extraction | 9/9 |
| ...      | ... | ... |

## In Progress 🔄
| Story ID | Title | ACs | Notes |
|----------|-------|-----|-------|
| ...      | ... | ... | ... |

## Backlog 📋
| Story ID | Title | ACs | Priority |
|----------|-------|-----|----------|
| ...      | ... | ... | Next |

## Summary
- Total stories: N
- Done: N | In Progress: N | Backlog: N
```

### 5. Update progress.md
Write the sprint board output to `progress.md` at the project root, replacing its contents entirely.
