# Multi-Consultant Story 5: Format-Agnostic Prompts
# Generated via /generate-prompt --save --with-plan --tmux

**SP: 5 | Wave: 3 (parallel with Stories 3, 4) | Dependencies: Story 2 complete**
**Design doc: `docs/architecture/multi-consultant-format-design.md` Section 5.6, Section 7 Story 5**

## Skills to Load

/planning-with-files — persistent markdown plan
/prompt-engineering — design format-conditional prompt templates
/langgraph-fundamentals — understand how prompts are invoked in graph nodes
/test-driven-development — test prompt rendering with different format contexts
/verification-before-completion — verify before claiming done

---

## Prerequisites

- Branch: `git checkout ACMV3`
- Story 2 complete (`InferredSchema` exists with `detected_format` field)
- Pack 6 (SAMP→ARA) complete — prompts already use correct ARA terminology
- Read design doc Section 5.6 (Format-Agnostic Prompts)

---

## Glossary

| Term | Definition |
|------|-----------|
| Format-conditional prompt | Jinja template using `{% if detected_format == "pipe_table" %}` to show format-specific examples |
| `detected_format` | String from format detector: `"standard"`, `"pipe_table"`, `"ara"`, or `"unknown"` |
| `extraction_fields` | Dynamic list of SF fields to extract — from InferredSchema instead of hardcoded 13 fields |
| `sf_field_catalog` | Full SF field schema loaded from `config_loader.py` — used as LLM reference |
| Format-specific example library | YAML/JSON file with worked examples per consultant format |

---

## Key Files

**Read:**
- `docs/architecture/multi-consultant-format-design.md` — Section 5.6
- `prompts/acm/building_inventory.jinja` — currently has hardcoded format sections
- `prompts/acm/row_extraction.jinja` — currently has hardcoded 13-field schema
- `prompts/acm/v3_building_extraction.jinja` — currently has hardcoded worked examples
- `prompts/acm/structure_extraction.jinja` — format classification heuristics
- `open_notebook/extractors/row_extractor.py` — `build_kv_prompt()` uses fixed field list
- `open_notebook/extractors/parsers/config_loader.py` — SF field schema source

**Modify:**
- `prompts/acm/building_inventory.jinja` — add `detected_format` conditional sections
- `prompts/acm/row_extraction.jinja` — accept dynamic `extraction_fields` list
- `prompts/acm/v3_building_extraction.jinja` — format-conditional worked examples
- `open_notebook/extractors/row_extractor.py` — `build_kv_prompt()` accepts dynamic field list from InferredSchema

**Create:**
- `prompts/acm/format_examples/standard.yaml` — DET format worked examples
- `prompts/acm/format_examples/ara.yaml` — ARA format worked examples
- `prompts/acm/format_examples/pipe_table.yaml` — Pipe-table format worked examples (e.g., Greencap pipe-delimited)
- `tests/test_format_agnostic_prompts.py` — test prompt rendering with different format contexts

---

## Plan

Create `docs/sprint-artifacts/mcs5-agnostic-prompts/task_plan.md`:
- [ ] Create format example YAML files (standard, text_header, pipe_table) with worked examples
- [ ] Add `detected_format` Jinja variable to `building_inventory.jinja`
- [ ] Make building_inventory.jinja format-conditional (design doc Section 5.6 template)
- [ ] Add `extraction_fields` Jinja variable to `row_extraction.jinja`
- [ ] Make row_extraction.jinja dynamic — field list from InferredSchema instead of hardcoded 13
- [ ] Make v3_building_extraction.jinja example-conditional based on `detected_format`
- [ ] Update `build_kv_prompt()` in `row_extractor.py` to accept dynamic field list
- [ ] Wire `detected_format` from InferredSchema → prompt template context in graph nodes
- [ ] Write tests: render building_inventory.jinja with each format → verify correct section shown
- [ ] Write tests: render row_extraction.jinja with dynamic fields → verify field list matches
- [ ] Write tests: render v3_building_extraction.jinja with each format → verify correct example
- [ ] Verify backward compatibility: `detected_format=None` renders existing default behavior
- [ ] Run full test suite + lint

---

## Agent Team Strategy: TMUX ( Opus + Claude Agent Teams - Not Subagents)

```
Pane 0 (left):   Prompt templates — modify .jinja files
Pane 1 (right):  Python wiring — row_extractor.py, graph node context
Pane 2 (bottom): Test runner — continuous pytest
```

---

## Context7 Directives

1. resolve-library-id for "jinja2" → query-docs for "conditional blocks if elif else include macro"
2. resolve-library-id for "langchain" → query-docs for "PromptTemplate from_template ChatPromptTemplate"

---

## Verification Checklist

- [ ] `building_inventory.jinja` renders different sections for `standard`, `pipe_table`, `text_header`, `unknown`
- [ ] `row_extraction.jinja` renders dynamic field list when `extraction_fields` provided
- [ ] `row_extraction.jinja` renders default 13 fields when no `extraction_fields` provided
- [ ] `v3_building_extraction.jinja` shows format-appropriate worked example
- [ ] `build_kv_prompt()` accepts and uses dynamic field list from InferredSchema
- [ ] Format example YAML files are valid and loadable
- [ ] `uv run pytest tests/test_format_agnostic_prompts.py -v` — all pass
- [ ] `uv run pytest tests/ -x` — full suite passes
- [ ] `uv run ruff check .` — lint clean

---

## Commit Template

```
feat(prompts): make extraction prompts format-agnostic with dynamic field lists

- Add detected_format conditional sections to building_inventory.jinja
- Make row_extraction.jinja accept dynamic extraction_fields from InferredSchema
- Make v3_building_extraction.jinja example-conditional by format
- Create format example library (standard.yaml, ara.yaml, pipe_table.yaml)
- Update build_kv_prompt() to accept dynamic field list
- Multi-Consultant Story 5 of 7

Co-Authored-By: Claude <noreply@anthropic.com>
```
