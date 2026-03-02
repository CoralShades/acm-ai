# Tier 1 + Tier 2 Skills Rollout

Installed and mirrored the ACM-AI prioritized Tier 1 and Tier 2 skills into all local skill roots for independent runtime use.

## Install Targets

- `.claude/skills`
- `.agents/skills`
- `.opencode/skills`
- `.codex/skills`

## Source Catalogs

- `https://github.com/VoltAgent/awesome-agent-skills`
- `https://github.com/travisvn/awesome-claude-skills`

## Tier 1 Installed

- `anthropics/skills`: `pdf`, `xlsx`, `webapp-testing`, `frontend-design`, `mcp-builder`
- `trailofbits/skills`: `codeql`, `semgrep`, `sarif-parsing`, `insecure-defaults`
- `obra/superpowers`: `brainstorming`, `dispatching-parallel-agents`, `executing-plans`, `finishing-a-development-branch`, `receiving-code-review`, `requesting-code-review`, `subagent-driven-development`, `systematic-debugging`, `test-driven-development`, `using-git-worktrees`, `using-superpowers`, `verification-before-completion`, `writing-plans`, `writing-skills`

## Tier 2 Installed

- `anthropics/skills`: `docx`, `pptx`, `skill-creator`
- `trailofbits/skills`: `differential-review`, `modern-python`
- `vercel-labs/next-skills`: `next-best-practices`
- `vercel-labs/agent-skills`: `react-best-practices`, `web-design-guidelines`
- `getsentry/skills`: `code-review`, `find-bugs`, `commit`, `create-pr`
- `lackeyjb/playwright-skill`: `playwright-skill`
- `microsoft/skills`: `pydantic-models-py`, `fastapi-router-py`
- `ibelick/ui-skills`: `baseline-ui`, `fixing-accessibility`, `fixing-metadata`, `fixing-motion-performance`
- `Leonxlnx/taste-skill`: `taste-skill`
- `muratcankoylan/Agent-Skills-for-Context-Engineering`: `context-compression`, `context-optimization`, `multi-agent-patterns`
- `k-kolomeitsev/data-structure-protocol`: `data-structure-protocol`
- `openai/skills`: `security-best-practices`
- `prompt-security/clawsec`: `claw-release`, `clawsec-clawhub-checker`, `clawsec-feed`, `clawsec-nanoclaw`, `clawsec-suite`, `clawtributor`, `openclaw-audit-watchdog`, `prompt-agent`, `soul-guardian`

## Notes

- Existing `bmad-*` skills in `.agents/skills` were preserved.
- `trailofbits/static-analysis` is represented by the shipped sub-skills: `codeql`, `semgrep`, `sarif-parsing`.
