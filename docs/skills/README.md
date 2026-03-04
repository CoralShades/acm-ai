# ACM-AI Skill Invocation Guide

This guide documents how to invoke every installed Tier 1 and Tier 2 skill across OpenCode, Claude, and Codex.

## Where Skills Are Installed

- OpenCode: `.opencode/skills/<skill>/SKILL.md`
- Claude: `.claude/skills/<skill>/SKILL.md`
- Codex primary: `.agents/skills/<skill>/SKILL.md`
- Codex mirror: `.codex/skills/<skill>/SKILL.md`

## Invocation Pattern

Use `@docs/...` references so the agent always has category context.

- OpenCode template:
  - `@docs/skills/<category>/README.md Use the <skill-name> skill to <task>.`
- Claude template:
  - `@docs/skills/<category>/README.md Use the <skill-name> skill to <task>.`
- Codex template:
  - `@docs/skills/<category>/README.md Use the <skill-name> skill to <task>.`

## Categories

- `@docs/skills/01-document-office/README.md` - PDF and Office document skills
- `@docs/skills/02-testing-quality/README.md` - Testing and quality skills
- `@docs/skills/03-frontend-ui/README.md` - Frontend and UI redesign skills
- `@docs/skills/04-backend-api-data/README.md` - Backend, API, and model skills
- `@docs/skills/05-security-analysis/README.md` - Security and static analysis skills
- `@docs/skills/06-planning-execution/README.md` - Planning and execution workflow skills
- `@docs/skills/07-git-review-pr/README.md` - Git, review, and PR skills
- `@docs/skills/08-context-memory/README.md` - Context and memory engineering skills
- `@docs/skills/09-prompt-security-suite/README.md` - Prompt-security and ClawSec suite skills
- `@docs/skills/10-skill-authoring/README.md` - Skill authoring and creation skills

## Quick Tips

- Be explicit about desired output format in the same prompt.
- Pair one primary skill with one supporting skill for best results.
- Keep category doc references in your prompt for reproducible behavior.
