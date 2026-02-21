# E17-S3: Reasoning Token Display

## Story Info
- **Epic**: E17 — Live Extraction Intelligence
- **Status**: drafted
- **Priority**: P1
- **Size**: S (Small)
- **Created**: 2026-02-22
- **Dependencies**: E17-S1
- **Blocks**: None

## Description

When using reasoning models (DeepSeek R1, Claude with extended thinking), capture and display the model's reasoning tokens in a collapsible panel during extraction.

## Acceptance Criteria

- [ ] Collapsible "Agent Thinking" panel in ExtractionProgressPanel
- [ ] Streams reasoning tokens character-by-character
- [ ] Works for DeepSeek R1 (`<think>` blocks) and Claude extended thinking
- [ ] Hidden by default, user can expand
- [ ] Non-reasoning models: panel doesn't appear

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/components/acm/ExtractionThinkingPanel.tsx` | CREATE | Collapsible reasoning display with monospace streaming text |
| `open_notebook/graphs/acm_extraction.py` | MODIFY | Parse reasoning from LLM response before structured output |
| `frontend/src/components/acm/ExtractionProgressPanel.tsx` | MODIFY | Add ExtractionThinkingPanel below stage pills |

## Technical Notes

- `model.with_structured_output()` and streaming are mutually exclusive
- For reasoning models: invoke with stream=True, collect reasoning tokens, then pass to structured parser
- Detection: check model.name against known reasoning model patterns (deepseek-r1, claude.*thinking)
