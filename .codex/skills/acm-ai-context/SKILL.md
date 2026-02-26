---
name: acm-ai-context
description: >
  ACM-AI project context for Codex. Use when working in this repository.
  Provides tech stack, conventions, and BMAD integration points.
---

# ACM-AI Project Context (Codex)

Read the full project context from `CLAUDE.md` in the project root.

## Quick Reference
- Backend: FastAPI + SurrealDB + LangGraph (Python)
- Frontend: Next.js 15 + AG Grid (TypeScript)
- BMAD artifacts: `_bmad-output/`
- Implementation plans: `docs/plans/`
- Protected files: migrations/, tests/, hooks/
- Model: qwen2.5:7b via Ollama/OpenRouter

## Critical Rules
- ALWAYS use superpowers:test-driven-development for coding
- ALWAYS read BMAD story files before implementing
- NEVER modify protected files without explicit approval
- API calls cost real money — be efficient with extraction jobs
