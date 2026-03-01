# Findings — E29-S1: JSON Parser Resilience

## Current parse_json_response Behavior (utils.py:497-536)
1. Fenced regex: `r"```(?:json)?\s*\n?(\{.*?\})\s*\n?```"` (DOTALL, non-greedy)
2. If match → `json.loads(match.group(1))`
3. Else → brace-depth scan from first `{`
4. Return `dict` or raise `ValueError`

## Bug: Non-greedy fenced regex
- `\{.*?\}` stops at FIRST `}`, so `{"a":{"b":1}}` → captures `{"a":{"b":1}` → parse fails
- Fix: remove regex fence detection, strip fence markers first, then always use brace-depth scan

## Callers (5 sites)
| File | Line | Context |
|------|------|---------|
| `acm_extraction.py` | 1301 | Direct JSON extraction |
| `acm_extraction.py` | 1450 | Schema fallback path |
| `orchestrator.py` | 557 | Per-building extraction |
| `orchestrator.py` | 623 | Schema fallback path |
| `page_tagger.py` | 379 | Page tag batch parsing |
| `document_structure.py` | 168 | Structure analysis |
| `building_inventory.py` | 502 | Inventory parsing |

All use pattern: `parsed = parse_json_response(text)` with `except ValueError` or `except (ValueError, json.JSONDecodeError)`.

## TruncationError Design
- `class TruncationError(ValueError)` — subclass ensures backward-compat
- Raised when brace-depth > 0 at EOF (JSON started but never closed)
- Message includes: partial content preview, depth at EOF

## Multi-Block Selection
- Extract ALL complete JSON objects via brace-depth scan
- Try `json.loads()` on each candidate
- Return largest valid object (by `len(json.dumps(obj))`)
- Deterministic: same input → same output

## Existing Tests (test_qwen_extraction.py:63-113)
7 tests covering: fenced, unfenced, preamble, nested, no-json, empty-string
All must continue to pass (AC-5).
