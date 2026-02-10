# Tech Spec: E8-S1 - Install UI/UX Pro Max Skill

> **Story:** E8-S1
> **Epic:** UI Refresh (Bento Grid Design)
> **Status:** Done
> **Created:** 2025-12-08

---

## Overview

Install the UI/UX Pro Max Skill to enhance AI-assisted design decisions and component generation.

---

## User Story

**As a** developer
**I want** the design intelligence skill installed
**So that** I can generate consistent UI components

---

## Acceptance Criteria

- [x] Clone ui-ux-pro-max-skill to `.claude/skills/`
- [x] Verify search functionality works
- [x] Document usage patterns

---

## Technical Design

### 1. Clone Repository

```bash
# Create skills directory if not exists
mkdir -p .claude/skills

# Clone the skill
cd .claude/skills
git clone https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git
```

### 2. Skill Structure

The skill should contain:
```
.claude/skills/ui-ux-pro-max-skill/
├── README.md              # Usage documentation
├── prompts/               # Design prompt templates
│   ├── bento-grid.md
│   ├── color-system.md
│   └── component-library.md
├── examples/              # Component examples
│   ├── bento-card.tsx
│   ├── bento-grid.tsx
│   └── design-tokens.css
└── patterns/              # Design patterns
    ├── dashboard.md
    └── forms.md
```

### 3. Integration with Claude

Create `.claude/commands/design.md`:

```markdown
# Design Command

Use the UI/UX Pro Max Skill for design decisions.

## Available Patterns

- **Bento Grid**: Modern dashboard layouts
- **Design Tokens**: Color, spacing, typography systems
- **Component Library**: Reusable UI components

## Usage

Ask Claude to reference the skill when designing:
- "Using ui-ux-pro-max-skill, create a bento grid layout for..."
- "Apply the design tokens from ui-ux-pro-max-skill to..."
```

### 4. Documentation

Create `.claude/skills/README.md`:

```markdown
# Claude Skills

## UI/UX Pro Max Skill

Design intelligence for consistent UI development.

### Key Features
- Bento grid layout patterns
- OKLch color system
- Modern component patterns
- Responsive design guidelines

### How to Use
Reference the skill in prompts:
"Using the ui-ux-pro-max-skill patterns, create..."

### Examples
See `.claude/skills/ui-ux-pro-max-skill/examples/`
```

---

## File Changes

| File | Change |
|------|--------|
| `.claude/skills/ui-ux-pro-max-skill/` | Clone repository |
| `.claude/skills/README.md` | Documentation |
| `.claude/commands/design.md` | Integration command |
| `.gitignore` | Add .claude/skills/ if needed |

---

## Dependencies

None - foundational for UI refresh

---

## Testing

1. Verify repository cloned successfully
2. Check all expected files present
3. Reference skill in Claude prompt
4. Verify Claude can access skill content
5. Test example component generation

---

## Notes

- May need to update .gitignore if skill should be version controlled
- Consider creating a fork for customization
- Skill content should be reviewed before use

---

## Estimated Complexity

**Low** - Repository clone and documentation

---

## Dev Agent Record

### Implementation Date: 2026-01-11

### Files Created/Modified:
| File | Change |
|------|--------|
| `.claude/skills/ui-ux-pro-max-skill/` | Cloned - Full UI/UX design intelligence skill |
| `.claude/skills/README.md` | Created - Skills directory documentation |
| `.claude/commands/design.md` | Created - Design command integration |

### Implementation Notes:

**Skill Contents:**
- 50+ UI styles (glassmorphism, bento grid, minimalism, etc.)
- 21 color palettes for different product types
- 50 font pairings with Google Fonts
- 20 chart type recommendations
- 9 tech stack guidelines (React, Next.js, shadcn/ui, etc.)

**Search Functionality:**
- Python-based BM25 + regex hybrid search engine
- Domains: product, style, typography, color, landing, chart, ux
- Stack-specific searches available
- Note: Unicode display may have issues on Windows console (functionality works)

**Integration:**
- Design command created at `.claude/commands/design.md`
- Skill can be referenced in prompts: "Using ui-ux-pro-max-skill..."
- Direct search available via Python script

### Verification:
- Repository cloned: PASS
- Scripts exist: PASS (search.py, core.py)
- Data files exist: PASS (9 CSV databases)
- Documentation created: PASS

### Code Review Fixes (2026-01-11):

**M1: `.gitignore` Decision (Intentional)**
- The `.claude/` directory is already in `.gitignore` (excludes sessions, settings, skills)
- Decision: Keep skill NOT version controlled - it's an external dependency
- Rationale: Skill can be re-cloned from GitHub; avoids bloating repo with 3rd-party code
- Team members should run the clone command from tech-spec Section 1 to install

**M2: File Changes Table Clarification**
- `.gitignore` listed in tech-spec but intentionally NOT modified
- The existing `.claude` entry already excludes the skills directory
- No changes needed to achieve desired behavior

**L1: Actual vs Expected Structure**
- Tech-spec Section 2 shows hypothetical structure (prompts/, examples/, patterns/)
- Actual cloned repo uses different organization (.claude/skills/ui-ux-pro-max/, scripts/, data/)
- The actual structure is MORE comprehensive with searchable CSV databases

**L2: Fixed incorrect relative path in `.claude/skills/README.md`**
- Changed `../.claude/commands/design.md` to `../commands/design.md`

---
