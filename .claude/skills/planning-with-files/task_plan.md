# Multi-Provider Audit: ACM-AI (2026-02-23)

## Goal
Produce a gap report (NO code changes) covering OpenRouter, Ollama, provider isolation,
chunking/token management, and error handling across the ACM-AI codebase.

## Files to Read
- [ ] open_notebook/domain/models.py
- [ ] api/model_provisioning.py
- [ ] open_notebook/graphs/utils.py
- [ ] open_notebook/graphs/acm_extraction.py
- [ ] .env.example
- [ ] Any file importing ChatOpenAI, ChatAnthropic, or Esperanto model classes

## Phases

### Phase 1: Read all target files
- [ ] Read all 5 primary files in parallel
- [ ] Grep for ChatOpenAI / ChatAnthropic / Esperanto imports

### Phase 2: Audit against checklist
- [ ] OR-1 through OR-10 (OpenRouter)
- [ ] OL-1 through OL-5 (Ollama)
- [ ] ISO-1 through ISO-3 (Provider Isolation)
- [ ] TK-1 through TK-3 (Chunking / Token)
- [ ] EH-1 through EH-4 (Error Handling)

### Phase 3: Produce gap report
- [x] Write findings to findings2.md
- [x] Write prioritised P0–P3 list
- [x] Present final report to user
- [x] Save full report to docs/sprint-artifacts/audit-multi-provider-2026-02-23.md

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| (none yet) | — | — |
