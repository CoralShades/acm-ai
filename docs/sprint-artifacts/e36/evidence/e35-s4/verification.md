# V4: E35-S4 — Provider Priority (AC5)

## Verification Date: 2026-03-05

## Code Check: Provider Chain Order

**File**: `open_notebook/graphs/utils.py:857-907`

**Result**: PASS

Function `_provision_extraction_primary_model()` implements priority chain:

1. **Ollama first** (line 871): `if os.getenv("OLLAMA_API_BASE")` → `("ollama", "qwen2.5:7b", None)`
2. **Anthropic Direct** (line 875): `os.getenv("ACM_ANTHROPIC_API_KEY")` → `("anthropic", "claude-sonnet-4-20250514", key)`
3. **OpenRouter** (line 880): `os.getenv("ACM_OPENROUTER_API_KEY")` → `("openrouter", "anthropic/claude-sonnet-4", key)`

## Code Check: ACM-Namespaced Keys

**Result**: PASS

- Line 875: Uses `ACM_ANTHROPIC_API_KEY` (NOT bare `ANTHROPIC_API_KEY`)
- Line 880: Uses `ACM_OPENROUTER_API_KEY` (NOT bare `OPENROUTER_API_KEY`)
- This prevents Claude Code's own API keys from being consumed by extraction

## Code Check: Fallback Model

**File**: `open_notebook/graphs/utils.py:910-997`

`provision_extraction_fallback_model()` also follows the same pattern:
- Excludes the failed model from candidates
- Applies `_apply_ollama_extraction_settings()` on line 990

## Verdict: PASS
