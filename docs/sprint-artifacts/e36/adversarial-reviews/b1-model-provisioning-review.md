# Adversarial Review: B1 — Model Provisioning (Anthropic Model IDs)

## Fix Summary
Added three new Anthropic model IDs to `MODEL_CATALOG` in `api/model_provisioning.py`:
- `claude-haiku-4-5-20251001`
- `claude-sonnet-4-5-20250514`
- `claude-opus-4-6-20250610`

Updated `FALLBACK_MODELS["anthropic"]` to use `claude-haiku-4-5-20251001` (chat) and
`claude-sonnet-4-5-20250514` (all other purposes). Legacy IDs retained as dead entries.

## Files Reviewed
- `api/model_provisioning.py`

## Findings

### [CONCERN] Invented/Future Model IDs Cannot Be Verified
**What**: `claude-opus-4-6-20250610` and the `-4-5-` suffix variants are not standard
Anthropic release naming patterns as of the knowledge cutoff. The Opus entry is in the
catalog but notably absent from `FALLBACK_MODELS`, which limits its blast radius.
However, if the IDs are wrong, `find_or_create_model()` will silently create a DB record
for a model that the Anthropic API will reject at inference time — no startup error,
no warning, just a failed chat at runtime.
**Why it matters**: A user who selects `claude-opus-4-6-20250610` from the model picker
will get a silent inference failure, with no actionable error in the UI.
**Evidence**: `find_or_create_model()` calls `new_model.save()` without any live API
validation. `seed_model_catalog()` counts and logs "N models available" even for
unvalidatable IDs.
**Recommendation**: Add a comment citing the Anthropic changelog URL where each model ID
was sourced. Consider a dry-run invocation at startup (e.g., a 1-token prompt) for newly
added models to surface bad IDs before they reach users.

### [CONCERN] OpenRouter Model IDs Use Speculative Naming
**What**: Several OpenRouter entries use names that appear to be forward-looking or
invented (e.g., `qwen/qwen3-next-80b-a3b-instruct:free`, `openai/gpt-5.2`,
`minimax/minimax-m2.1`, `deepseek/deepseek-v3.2`, `anthropic/claude-sonnet-4.6`).
OpenRouter IDs are fragile — providers rename models without notice.
**Why it matters**: Same silent-failure risk as above. A stale or wrong OpenRouter ID
produces a 404 from OpenRouter, which propagates as a generic tool failure in chat.
**Evidence**: `MODEL_CATALOG` lines 159–178. No validation or provenance comments.
**Recommendation**: Source these from `openrouter.ai/api/v1/models` at startup (or at
least document where each ID was confirmed). Flag catalog additions in PR review as
requiring source verification.

### [NITPICK] `get_fallback_providers()` Default Includes `anthropic` Before `openai`
**What**: Default fallback order is `"ollama,anthropic,openai,openrouter"`. If only
OpenAI is configured (no Anthropic key), the chain skips Anthropic correctly via
`is_provider_available()`. But the ordering embeds an unstated business priority
(prefer Anthropic over OpenAI as second cloud fallback).
**Why it matters**: Ops teams may not notice this implicit priority when configuring
deployments with only an OpenAI key.
**Recommendation**: Document the intended fallback priority in an inline comment.

## Verdict: PASS WITH CONCERNS

The fix is structurally sound. The catalog pattern and idempotent `find_or_create_model`
logic are correct. The concerns are about model ID accuracy and the absence of any
runtime validation, which could produce confusing silent failures in production.
