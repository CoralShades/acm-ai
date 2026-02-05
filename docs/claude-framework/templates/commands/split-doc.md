---
description: Split a large documentation file into smaller chunks
allowed-tools: Bash, Read, Write, Edit
argument-hint: <file-path>
---

# Split Large Documentation

Split an oversized documentation file into manageable chunks.

## Input
- File path: $ARGUMENTS (e.g., docs/epics.md)

## Process

1. **Read the file** and analyze structure:
   - Identify natural section breaks (## headings)
   - Count characters per section
   - Determine optimal split points

2. **Create directory** for chunks:
   ```
   docs/epics.md → docs/epics/
   ```

3. **Create index file** (`_index.md`):
   - Summary table of all sections
   - Links using @path syntax
   - Quick reference for navigation

4. **Split content** into chunk files:
   - One file per major section
   - Keep each chunk under 15K chars
   - Preserve heading hierarchy
   - Add cross-references

5. **Update original file**:
   - Replace content with import to index
   - Or delete if index replaces it

6. **Update CLAUDE.md** if needed:
   - Change direct references to index
   - Add import syntax examples

## Splitting Strategy

### For Epics
```
docs/epics.md (54K) →
  docs/epics/_index.md (2K)    # Summary table
  docs/epics/epic-001.md (8K)  # First epic
  docs/epics/epic-002.md (10K) # Second epic
  ...
```

### For API Specs
```
docs/api.md (48K) →
  docs/api/_index.md (3K)      # Endpoint list
  docs/api/auth.md (8K)        # Auth endpoints
  docs/api/users.md (12K)      # User endpoints
  docs/api/resources.md (15K)  # Resource endpoints
  ...
```

### For Requirements
```
docs/requirements.md (60K) →
  docs/requirements/_index.md (2K)
  docs/requirements/functional.md (20K)
  docs/requirements/non-functional.md (15K)
  docs/requirements/constraints.md (10K)
  ...
```

## Index File Template

```markdown
# [Document Name] Index

## Overview
[Brief description of what this documentation covers]

## Sections

| Section | Description | Size | Link |
|---------|-------------|------|------|
| Section 1 | Description | ~8K | @docs/name/section-1.md |
| Section 2 | Description | ~10K | @docs/name/section-2.md |

## Quick Navigation

### [Category 1]
- @docs/name/section-1.md - Brief description

### [Category 2]
- @docs/name/section-2.md - Brief description

## Usage

Import specific sections on-demand:
- Read this index for overview
- Use @path/to/section.md to load details
- Don't load all sections at once
```

## Output

Report:
- Files created with sizes
- Index file location
- Total size before/after
- Context savings achieved
