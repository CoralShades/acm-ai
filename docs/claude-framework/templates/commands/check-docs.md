---
description: Check documentation sizes and identify files that need splitting
allowed-tools: Bash, Glob
---

# Check Documentation Sizes

Identify documentation files that exceed recommended size limits.

## Size Limits

| Type | Recommended | Warning | Critical |
|------|-------------|---------|----------|
| CLAUDE.md | <8K chars | >15K | >25K |
| Rule files | <20K chars | >30K | >40K |
| Reference docs | <40K chars | >50K | >75K |

## Process

1. **Find all markdown files**:
   ```bash
   find . -name "*.md" -not -path "./.git/*" -not -path "./node_modules/*"
   ```

2. **Check file sizes**:
   ```bash
   find . -name "*.md" -not -path "./.git/*" -exec wc -c {} \; | sort -rn | head -20
   ```

3. **Flag oversized files**:
   - Any file over 40K chars → Needs splitting or RAG
   - Any file over 25K chars → Consider splitting
   - CLAUDE.md over 8K chars → Needs trimming

4. **Check loaded memory**:
   - Use `/memory` to see what's currently loaded
   - Identify redundant or unused loaded files

## Output

Report with:
- List of oversized files with sizes
- Splitting recommendations
- Files that should use RAG instead
- Estimated context savings

## Example Output

```
📊 Documentation Size Report

⚠️ OVERSIZED (needs action):
  54.7K  docs/epics.md         → SPLIT into chunks
  48.2K  docs/api-spec.md      → SPLIT or RAG

⚡ LARGE (monitor):
  35.1K  docs/architecture.md  → Consider splitting
  28.4K  docs/requirements.md  → OK for now

✅ OPTIMAL:
  6.2K   CLAUDE.md             → Good
  4.1K   .claude/rules/*.md    → Good

💡 Recommendations:
  1. Split docs/epics.md into docs/epics/*.md
  2. Create index file for docs/api-spec.md
  3. Total context savings: ~60K chars
```
