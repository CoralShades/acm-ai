# Claude Skills

This directory contains AI skills that enhance Claude Code's capabilities for this project.

## Installed Skills

### UI/UX Pro Max Skill

**Location:** `ui-ux-pro-max-skill/`

Design intelligence for consistent, professional UI development.

#### Key Features

- **50+ UI Styles**: Glassmorphism, bento grid, minimalism, neumorphism, brutalism, dark mode, and more
- **21 Color Palettes**: Optimized for different product types (SaaS, healthcare, fintech, e-commerce)
- **50 Font Pairings**: Professional typography with Google Fonts imports
- **20 Chart Types**: Data visualization recommendations with library suggestions
- **9 Tech Stacks**: React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui

#### How to Use

Reference the skill in prompts:

```
Using the ui-ux-pro-max-skill patterns, create a bento grid dashboard layout
```

Or search the design database directly:

```bash
# Search for style guidelines
python .claude/skills/ui-ux-pro-max-skill/.claude/skills/ui-ux-pro-max/scripts/search.py "bento grid" --domain style

# Search for color palettes
python .claude/skills/ui-ux-pro-max-skill/.claude/skills/ui-ux-pro-max/scripts/search.py "dashboard saas" --domain color

# Search for stack-specific patterns
python .claude/skills/ui-ux-pro-max-skill/.claude/skills/ui-ux-pro-max/scripts/search.py "card layout" --stack shadcn
```

#### Search Domains

| Domain | Description |
|--------|-------------|
| `product` | Product type recommendations |
| `style` | UI styles, colors, effects |
| `typography` | Font pairings |
| `color` | Color palettes |
| `landing` | Page structure |
| `chart` | Chart recommendations |
| `ux` | Best practices |

#### Examples

See `ui-ux-pro-max-skill/screenshots/` for visual examples.

#### Documentation

- **Full skill definition**: `ui-ux-pro-max-skill/.claude/skills/ui-ux-pro-max/SKILL.md`
- **Project README**: `ui-ux-pro-max-skill/README.md`
- **Design command**: `../commands/design.md`

## Adding New Skills

To add a new skill:

1. Clone or create the skill in this directory
2. Add documentation to this README
3. Create a command in `.claude/commands/` if needed
4. Update `.gitignore` if the skill should not be version controlled

## Notes

- Skills enhance AI capabilities with domain-specific knowledge
- Each skill may have its own dependencies (check individual READMEs)
- The UI/UX Pro Max Skill requires Python 3.x (no external dependencies)
