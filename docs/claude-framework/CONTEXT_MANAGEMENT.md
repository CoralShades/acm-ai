# Context Management Guide

> **Solving the "Large docs will impact performance" warning**

This guide addresses the warning: `⚠Large docs\epics.md will impact performance (54.7k chars > 40.0k)`

---

## Understanding the Problem

Claude Code loads documentation at session start. Large files consume context window space, leaving less room for reasoning.

```
┌─────────────────────────────────────────────────────────┐
│                    CONTEXT WINDOW (200K tokens)         │
├─────────────────────────────────────────────────────────┤
│  CLAUDE.md + .claude/rules/ (auto-loaded)              │
│  ────────────────────────────────────────               │
│  Large docs like epics.md (if loaded)    ← PROBLEM     │
│  ────────────────────────────────────────               │
│  Current conversation                                   │
│  ────────────────────────────────────────               │
│  ▼▼▼ ROOM FOR REASONING ▼▼▼                            │
│  (The more space here, the better the output)          │
└─────────────────────────────────────────────────────────┘
```

---

## Size Limits Reference

| Content Type | Recommended Limit | Hard Limit |
|--------------|-------------------|------------|
| CLAUDE.md | <200 lines (~8K chars) | <500 lines |
| Individual rule file | <500 lines | <1000 lines |
| Reference document | <1000 lines (~40K chars) | ~25K tokens |
| Single file read | N/A | ~25K tokens |
| Import nesting | 2-3 levels | 5 levels max |

---

## Solution 1: Document Splitting

For files over 40K chars (like `epics.md`), split into smaller chunks.

### Before (Problem)
```
docs/
└── epics.md                 # 54.7K chars - TOO LARGE
```

### After (Solution)
```
docs/
├── epics/
│   ├── _index.md            # Summary + links (~2K chars)
│   ├── epic-001-auth.md     # Authentication epic (~8K chars)
│   ├── epic-002-dashboard.md # Dashboard epic (~10K chars)
│   ├── epic-003-api.md      # API epic (~12K chars)
│   └── epic-004-mobile.md   # Mobile epic (~15K chars)
└── epics.md                 # Now just imports _index.md
```

### Index File Template

```markdown
# Epics Index

Quick reference to all project epics. Import specific epics on-demand.

## Active Epics
| ID | Name | Status | File |
|----|------|--------|------|
| E-001 | User Authentication | In Progress | @docs/epics/epic-001-auth.md |
| E-002 | Dashboard | Planning | @docs/epics/epic-002-dashboard.md |
| E-003 | API Gateway | Backlog | @docs/epics/epic-003-api.md |

## How to Use
- Read this index for overview
- Import specific epic with `@docs/epics/epic-XXX-name.md`
- Don't load all epics at once
```

---

## Solution 2: On-Demand Imports

Use `@path/to/file` syntax to load documentation only when needed.

### In CLAUDE.md

```markdown
## Documentation References

For detailed specifications, import on-demand:

- **Epics Overview**: @docs/epics/_index.md
- **API Specs**: @docs/api/openapi.md
- **Architecture**: @docs/architecture/overview.md

⚠️ Do NOT load these at session start. Reference when needed.
```

### During Conversation

```
User: What are the requirements for the auth epic?
Claude: Let me read the auth epic documentation.
        @docs/epics/epic-001-auth.md
        [Claude reads and responds with specific details]
```

---

## Solution 3: Path-Scoped Rules

Use `.claude/rules/` with path patterns to load rules only for relevant files.

### File: `.claude/rules/epics.md`

```yaml
---
paths:
  - "docs/epics/**/*.md"
  - "**/epic-*.md"
---

# Epic Documentation Rules

When working with epic files:
- Each epic should have: ID, Title, Status, Stories, Acceptance Criteria
- Keep individual epic files under 15K chars
- Use story references, not full story content
- Link to related epics with @path syntax
```

This rule only loads when you're working on epic files, not for every session.

---

## Solution 4: RAG Integration (For Very Large Docs)

For documentation that can't be reasonably split (100K+ chars), use RAG.

### When to Use RAG

| Doc Size | Strategy |
|----------|----------|
| <40K chars | Keep as-is |
| 40K-100K chars | Split into chunks |
| >100K chars | Use RAG vector search |

### RAG Agent Pattern

```markdown
# In CLAUDE.md

## Large Documentation Lookup

For large documentation (specs, epics, requirements):
1. Use the RAG lookup tool to search semantically
2. Don't load entire documents into context
3. Query specific sections as needed

RAG Endpoint: http://localhost:5678/webhook/rag-lookup
```

See [RAG_INTEGRATION.md](./RAG_INTEGRATION.md) for full setup.

---

## Solution 5: Memory Optimization Commands

### Check What's Loaded

```bash
/memory
```

Shows all loaded CLAUDE.md files, rules, and imports.

### Compact Session Context

```bash
/compact
```

Summarizes conversation history to free context space. Use sparingly - loses detail.

### Create /optimize-context Command

Create `.claude/commands/optimize-context.md`:

```markdown
---
description: Analyze and optimize loaded context
allowed-tools: Bash, Read, Glob
---

# Optimize Context

Check for oversized documentation and suggest optimizations.

## Process

1. List all loaded memory files with /memory
2. Check file sizes in docs/ directory
3. Flag any files over 40K chars
4. Suggest splitting strategy for large files
5. Recommend path-scoped rules for conditional loading
```

---

## Migration Strategy for Existing Projects

### Step 1: Identify Large Files

```bash
# Find files over 40K chars
find docs -name "*.md" -exec sh -c 'wc -c "$1" | awk "{if (\$1 > 40000) print \$1, \$2}"' _ {} \;
```

### Step 2: Prioritize by Usage

| Priority | File Type | Action |
|----------|-----------|--------|
| High | Loaded at session start | Split immediately |
| Medium | Referenced frequently | Create index + chunks |
| Low | Rarely accessed | Move to RAG |

### Step 3: Create Split Structure

For each large file:
1. Create subdirectory: `docs/filename/`
2. Create index: `docs/filename/_index.md`
3. Split content into logical chunks
4. Update original file to import index
5. Update CLAUDE.md references

### Step 4: Update CLAUDE.md

```markdown
## Documentation

### Quick Reference (always available)
- Project overview in this file
- Essential commands below

### On-Demand (import when needed)
- Epics: @docs/epics/_index.md
- API Specs: @docs/api/_index.md
- Architecture: @docs/architecture/_index.md

### Large Documentation (use RAG)
- Full requirements database
- Historical decision logs
- Complete API documentation
```

---

## BMAD v6 Specific Guidance

For BMAD projects with large `docs/epics.md`:

### Recommended Structure

```
_bmad/
├── epics/
│   ├── _index.md           # Epic summary table
│   ├── active/             # Currently worked on
│   │   ├── epic-001.md
│   │   └── epic-002.md
│   ├── backlog/            # Future epics
│   │   └── epic-003.md
│   └── completed/          # Done epics (archive)
│       └── epic-000.md
├── stories/
│   ├── _index.md           # Story summary
│   └── by-epic/            # Grouped by epic
│       ├── e001/
│       │   ├── s001.md
│       │   └── s002.md
│       └── e002/
└── sprints/
    ├── current.md          # Active sprint only
    └── archive/            # Past sprints
```

### Epic Index Template for BMAD

```markdown
# Epic Index

## Active Sprint Epics
| Epic | Title | Stories | Status |
|------|-------|---------|--------|
| E-001 | Auth System | 5/8 | 🟡 In Progress |

For details: @_bmad/epics/active/epic-001.md

## Backlog
| Epic | Title | Priority |
|------|-------|----------|
| E-003 | Mobile App | High |

## Completed
See @_bmad/epics/completed/ for archived epics.
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│              CONTEXT MANAGEMENT QUICK REF               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  FILE SIZE LIMITS                                       │
│  ─────────────────                                      │
│  CLAUDE.md: <200 lines                                  │
│  Rules: <500 lines each                                 │
│  Reference docs: <40K chars                             │
│                                                         │
│  LARGE FILE STRATEGIES                                  │
│  ────────────────────                                   │
│  40K-100K: Split into chunks                            │
│  >100K: Use RAG search                                  │
│                                                         │
│  IMPORT SYNTAX                                          │
│  ─────────────                                          │
│  @path/to/file.md  → On-demand import                   │
│  @~/global/file.md → From home directory                │
│                                                         │
│  COMMANDS                                               │
│  ────────                                               │
│  /memory  → See what's loaded                           │
│  /compact → Reduce session context                      │
│                                                         │
│  PATH-SCOPED RULES                                      │
│  ────────────────                                       │
│  ---                                                    │
│  paths:                                                 │
│    - "docs/**/*.md"                                     │
│  ---                                                    │
│  [rule content only loads for matching paths]           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Sources

- Claude Code Official Memory Documentation
- Agentic Engineering Methodology (Cole Medin)
- Claude Platform Context Window Guidelines
