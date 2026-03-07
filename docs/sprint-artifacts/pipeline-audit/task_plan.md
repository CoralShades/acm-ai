# Task Plan: Revise Prompt Pack for Claude Code Sessions

## Goal
Revise `prompt-pack.md` (S4-S9) into self-contained Claude Code session prompts that:
1. Include all necessary context inline (no undefined references to "Phase 1/2", "S2", etc.)
2. Use proper Claude Code skill invocation patterns
3. Leverage subagents, tools, and context7 effectively
4. Minimize token waste from context searching

## Tasks

### Phase 1: Research (subagents running)
- [x] Read existing prompt-pack.md
- [x] Read trace-audit-report.md for context
- [x] Spawn subagent: Claude Code skills/tools/subagent patterns
- [x] Spawn subagent: ACM pipeline terminology glossary
- [x] Spawn subagent: Skill file contents analysis

### Phase 2: Analysis
- [x] Collect subagent findings
- [x] Identify all undefined/ambiguous references in prompt-pack.md
- [x] Map each reference to its concrete definition (see findings.md)
- [x] Identify optimal Claude Code patterns for each session

### Phase 3: Write Revised Document
- [x] Write preamble with full pipeline glossary
- [x] Revise S4: Merge Pre-Extraction — self-contained prompt
- [x] Revise S5: Per-Building Parallelization — self-contained prompt
- [x] Revise S6: Docling Tables — self-contained prompt
- [x] Revise S7: SF Normalization — self-contained prompt
- [x] Revise S8: Dead Code Cleanup — self-contained prompt
- [x] Revise S9: Benchmark — self-contained prompt
- [x] Add Claude Code usage guide section
- [x] Save to `docs/sprint-artifacts/pipeline-audit/prompt-pack-v2.md`

### Phase 4: Validation
- [x] Compare v1 vs v2 side-by-side for scope preservation (all 6 sessions match)
- [x] Verify all undefined terms are resolved (8/8 terms resolved in glossary)
- [x] Verify skill invocations match actual skill names (6/6 verified against .claude/skills/)
