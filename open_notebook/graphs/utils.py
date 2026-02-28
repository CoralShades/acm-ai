import copy
import json
import os
import re
from typing import Any, List, Optional

import httpx
from esperanto import AIFactory, LanguageModel
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from loguru import logger

from open_notebook.domain.models import model_manager
from open_notebook.utils import token_count

# ---------------------------------------------------------------------------
# OpenRouter provider routing — HARD LOCK (E27-S3)
# ---------------------------------------------------------------------------
# Uses provider.only (hard allowlist) instead of provider.order (soft
# preference) to guarantee requests are served by Anthropic ONLY.
# Combined with allow_fallbacks=false, this means if Anthropic is
# unavailable the request FAILS rather than silently routing to
# Google Vertex or another provider with different extraction behavior.
#
# Ref: https://openrouter.ai/docs/guides/routing/provider-selection
# ---------------------------------------------------------------------------

OPENROUTER_ALLOWED_PROVIDERS = ["Anthropic"]


def _apply_openrouter_preferences(
    lc_model: BaseChatModel,
    *,
    source_id: str | None = None,
    building_name: str | None = None,
    stage_name: str | None = None,
) -> BaseChatModel:
    """Apply hard provider lock + production features for OpenRouter models.

    Only applies when the model's base_url points to OpenRouter.

    Configures 6 OpenRouter features:
    1. provider.only — hard allowlist, Anthropic ONLY (no silent Vertex fallback)
    2. allow_fallbacks=False — request FAILS if Anthropic unavailable
    3. zdr=True — Zero Data Retention for Victorian Government data
    4. Response Healing plugin — free auto-fix for malformed JSON (<1ms)
    5. data_collection="deny" — don't train on government data
    6. Request metadata — tags each call for production observability

    Ref: https://openrouter.ai/docs/guides/routing/provider-selection
    Ref: https://openrouter.ai/docs/guides/features/plugins/response-healing
    Ref: https://openrouter.ai/docs/guides/features/zdr
    """
    base_url = (
        getattr(lc_model, "openai_api_base", None)
        or getattr(lc_model, "base_url", None)
        or ""
    )
    if "openrouter.ai" not in str(base_url).lower():
        return lc_model

    # ZDR (Zero Data Retention) requires opt-in at
    # https://openrouter.ai/settings/privacy — if not configured,
    # OpenRouter returns 404 "No endpoints found matching your data policy".
    # Gate behind env var so it doesn't block extraction in dev.
    enable_zdr = os.getenv("OPENROUTER_ZDR", "false").lower() in ("true", "1", "yes")

    provider_config: dict[str, Any] = {
        "only": OPENROUTER_ALLOWED_PROVIDERS,
        "allow_fallbacks": False,
        "require_parameters": True,
        "data_collection": "deny",
    }
    if enable_zdr:
        provider_config["zdr"] = True

    openrouter_body: dict[str, Any] = {
        "provider": provider_config,
        "plugins": [
            {"id": "response-healing"},
        ],
        "transforms": ["middle-out"],
    }

    # Request metadata for production observability
    # OpenRouter: max 16 pairs, key ≤64 chars, value ≤512 chars
    metadata: dict[str, str] = {"app": "acm-ai", "pipeline": "extraction"}
    if source_id:
        metadata["source_id"] = str(source_id)[:512]
    if building_name:
        metadata["building"] = str(building_name)[:512]
    if stage_name:
        metadata["stage"] = str(stage_name)[:512]
    openrouter_body["metadata"] = metadata

    # Deep merge into existing model_kwargs.extra_body
    existing_kwargs = getattr(lc_model, "model_kwargs", {}) or {}
    existing_extra = existing_kwargs.get("extra_body", {}) or {}

    merged_extra = {**existing_extra, **openrouter_body}

    # Deep merge provider dict (preserve any existing provider settings)
    if "provider" in existing_extra and "provider" in openrouter_body:
        merged_extra["provider"] = {
            **existing_extra["provider"],
            **openrouter_body["provider"],
        }

    # Append plugins without duplicates
    if "plugins" in existing_extra and "plugins" in openrouter_body:
        existing_ids = {p.get("id") for p in existing_extra.get("plugins", [])}
        new_plugins = [
            p for p in openrouter_body["plugins"] if p.get("id") not in existing_ids
        ]
        merged_extra["plugins"] = existing_extra["plugins"] + new_plugins

    new_kwargs = {**existing_kwargs, "extra_body": merged_extra}
    object.__setattr__(lc_model, "model_kwargs", new_kwargs)

    logger.info(
        f"Applied OpenRouter hard lock: "
        f"provider.only={OPENROUTER_ALLOWED_PROVIDERS}, "
        f"allow_fallbacks=False, zdr={'ON' if enable_zdr else 'OFF'}, "
        f"response-healing=ON"
    )
    return lc_model


# ---------------------------------------------------------------------------
# JSON Schema utilities for OpenRouter response_format (E27-S4)
# ---------------------------------------------------------------------------


def pydantic_to_openrouter_schema(model_class: type) -> dict:
    """Convert a Pydantic model to an OpenRouter-compatible JSON Schema.

    OpenRouter's strict mode requires:
    1. All $defs (forward references) inlined into their usage sites
    2. additionalProperties: false on all object types
    3. Optional fields represented as anyOf with null normalized
    """
    raw_schema = model_class.model_json_schema()

    def _resolve_refs(node: Any, defs: dict) -> Any:
        """Recursively resolve all $ref entries by inlining definitions."""
        if not isinstance(node, dict):
            return node

        if "$ref" in node:
            ref_path = node["$ref"]
            def_name = ref_path.split("/")[-1]
            if def_name in defs:
                resolved = copy.deepcopy(defs[def_name])
                for k, v in node.items():
                    if k != "$ref":
                        resolved[k] = v
                return _resolve_refs(resolved, defs)
            return node

        result = {}
        for k, v in node.items():
            if k == "properties" and isinstance(v, dict):
                result[k] = {
                    pk: _resolve_refs(pv, defs)
                    for pk, pv in v.items()
                }
            elif k == "items":
                result[k] = _resolve_refs(v, defs)
            elif k in ("anyOf", "oneOf", "allOf") and isinstance(v, list):
                result[k] = [_resolve_refs(s, defs) for s in v]
            else:
                result[k] = v

        return result

    def _add_additional_properties_false(node: Any) -> Any:
        """Add additionalProperties: false to all object schemas."""
        if not isinstance(node, dict):
            return node

        if node.get("type") == "object" or "properties" in node:
            node["additionalProperties"] = False

        if "properties" in node:
            for k in node["properties"]:
                node["properties"][k] = _add_additional_properties_false(
                    node["properties"][k]
                )
        if "items" in node and isinstance(node["items"], dict):
            node["items"] = _add_additional_properties_false(node["items"])
        for key in ("anyOf", "oneOf", "allOf"):
            if key in node and isinstance(node[key], list):
                node[key] = [_add_additional_properties_false(s) for s in node[key]]

        return node

    # Extract and inline $defs
    defs = raw_schema.pop("$defs", {})
    resolved = _resolve_refs(copy.deepcopy(raw_schema), defs)

    # Add additionalProperties: false to all objects
    resolved = _add_additional_properties_false(resolved)

    # Remove Pydantic metadata not needed in JSON Schema
    resolved.pop("title", None)

    return resolved


# Module-level cache for ACM extraction schema (E27-S4)
_ACM_EXTRACTION_JSON_SCHEMA: dict | None = None


def _get_acm_extraction_schema() -> dict:
    """Lazily generate and cache the JSON Schema for ACMExtractionResult."""
    global _ACM_EXTRACTION_JSON_SCHEMA
    if _ACM_EXTRACTION_JSON_SCHEMA is None:
        from open_notebook.extractors.acm_schemas import ACMExtractionResult

        _ACM_EXTRACTION_JSON_SCHEMA = pydantic_to_openrouter_schema(
            ACMExtractionResult
        )
    return _ACM_EXTRACTION_JSON_SCHEMA


def _inject_response_format(
    lc_model: BaseChatModel,
    schema_dict: dict,
    schema_name: str,
) -> BaseChatModel:
    """Inject response_format: json_schema into model's extra_body.

    Stage-specific — called AFTER provision_langchain_model() and BEFORE
    model.ainvoke(). Only applies to OpenRouter models.

    This enforces schema validation at the OpenRouter layer, so the LLM
    returns JSON that conforms to the given schema. Combined with
    Response Healing plugin (E27-S3), this provides production-grade
    structured output without with_structured_output().

    Args:
        lc_model: LangChain model (already provisioned with OpenRouter prefs)
        schema_dict: JSON Schema dict (from pydantic_to_openrouter_schema)
        schema_name: Human-readable schema name (e.g. "ACMExtractionResult")

    Returns:
        The same model with response_format injected into extra_body.
    """
    base_url = (
        getattr(lc_model, "openai_api_base", None)
        or getattr(lc_model, "base_url", None)
        or ""
    )
    if "openrouter.ai" not in str(base_url).lower():
        return lc_model

    existing_kwargs = getattr(lc_model, "model_kwargs", {}) or {}
    existing_extra = existing_kwargs.get("extra_body", {}) or {}

    merged_extra = {
        **existing_extra,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": schema_dict,
            },
        },
    }

    new_kwargs = {**existing_kwargs, "extra_body": merged_extra}
    object.__setattr__(lc_model, "model_kwargs", new_kwargs)

    logger.debug(
        f"Injected response_format: json_schema ({schema_name}) "
        f"into model extra_body"
    )
    return lc_model


async def _verify_provider_routing(
    response: Any,
    stage_name: str,
    *,
    expected_provider: str = "Anthropic",
) -> dict | None:
    """Verify which OpenRouter provider actually served the request.

    Uses TWO methods:
    1. response_metadata (fast, inline)
    2. Generation API fallback (definitive, async HTTP call)

    Returns the generation data dict, or None if lookup failed.
    Non-blocking — extraction continues if this fails.

    Ref: https://openrouter.ai/docs/api-reference/get-a-generation
    """
    # Method 1: Check response_metadata (fast path)
    metadata = getattr(response, "response_metadata", {}) or {}
    actual_provider = metadata.get("provider", None)
    actual_model = metadata.get("model", None)
    gen_id = metadata.get("id", None)

    if actual_provider:
        if actual_provider.lower() != expected_provider.lower():
            logger.warning(
                f"[{stage_name}] PROVIDER MISMATCH — "
                f"Expected: {expected_provider}, Got: {actual_provider} "
                f"(model: {actual_model}, gen_id: {gen_id})"
            )
        else:
            logger.info(
                f"[{stage_name}] Provider: {actual_provider} | "
                f"Model: {actual_model}"
            )
        return {"provider_name": actual_provider, "model": actual_model}

    # Method 2: Query Generation API (definitive, async)
    if not gen_id:
        gen_id = (
            metadata.get("id")
            or (getattr(response, "additional_kwargs", {}) or {}).get("id")
        )

    if not gen_id:
        logger.debug(
            f"[{stage_name}] No generation ID — cannot verify provider"
        )
        return None

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.debug(
            f"[{stage_name}] No OPENROUTER_API_KEY — skipping Generation API lookup"
        )
        return None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://openrouter.ai/api/v1/generation",
                params={"id": gen_id},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                gen_data = resp.json().get("data", {})
                prov = gen_data.get("provider_name", "unknown")
                total_cost = gen_data.get("total_cost", 0)
                cache_discount = gen_data.get("cache_discount", 0)
                latency = gen_data.get("latency", 0)
                tokens_in = gen_data.get("tokens_prompt", 0)
                tokens_out = gen_data.get("tokens_completion", 0)

                if prov.lower() != expected_provider.lower():
                    logger.warning(
                        f"[{stage_name}] PROVIDER MISMATCH (GenAPI) — "
                        f"Expected: {expected_provider}, Got: {prov} | "
                        f"Cost: ${total_cost:.4f} | Tokens: {tokens_in}->{tokens_out}"
                    )
                else:
                    logger.info(
                        f"[{stage_name}] Provider: {prov} | "
                        f"Cost: ${total_cost:.4f} | Cache: -${cache_discount:.4f} | "
                        f"Latency: {latency}ms | Tokens: {tokens_in}->{tokens_out}"
                    )

                for pr in gen_data.get("provider_responses", []):
                    logger.debug(
                        f"[{stage_name}]   Provider attempt: "
                        f"{pr.get('provider_name')} -> status {pr.get('status')}"
                    )

                return gen_data
            else:
                logger.debug(
                    f"[{stage_name}] Generation API returned {resp.status_code} "
                    f"for gen_id={gen_id}"
                )
    except Exception as e:
        logger.debug(f"[{stage_name}] Generation API lookup failed: {e}")

    return None


async def provision_langchain_model(
    content, model_id, default_type, **kwargs
) -> BaseChatModel:
    """
    Returns the best model to use based on the context size and on whether there is a specific model being requested in Config.
    If context > 105_000, returns the large_context_model (if configured), else falls back to default.
    If model_id is specified in Config, returns that model
    Otherwise, returns the default model for the given type
    """
    tokens = token_count(content)

    if tokens > 105_000:
        logger.debug(
            f"Using large context model because the content has {tokens} tokens"
        )
        model = await model_manager.get_default_model("large_context", **kwargs)
        if model is None:
            # large_context_model not configured — fall back to default model type
            logger.warning(
                "large_context_model is not configured; falling back to default "
                f"{default_type} model for {tokens}-token content"
            )
            model = await model_manager.get_default_model(default_type, **kwargs)
    elif model_id:
        model = await model_manager.get_model(model_id, **kwargs)
    else:
        model = await model_manager.get_default_model(default_type, **kwargs)

    logger.debug(f"Using model: {model}")
    assert isinstance(model, LanguageModel), f"Model is not a LanguageModel: {model}"
    lc_model = model.to_langchain()
    return _apply_openrouter_preferences(lc_model)


async def provision_langchain_model_with_tools(
    content: str,
    model_id: Optional[str],
    default_type: str,
    tools: List[BaseTool],
    **kwargs,
) -> BaseChatModel:
    """Provision a LangChain model with tool-calling support.

    Gets the appropriate model and binds tools to it. If the model does not
    support tool calling, returns the base model without tools bound (the
    caller should fall back to non-tool behavior).

    Args:
        content: Content string for token counting / model selection
        model_id: Specific model ID override
        default_type: Default model type (e.g. "chat")
        tools: List of LangChain tools to bind
        **kwargs: Additional kwargs passed to model provisioning

    Returns:
        BaseChatModel with tools bound (if supported)
    """
    model = await provision_langchain_model(content, model_id, default_type, **kwargs)

    if not tools:
        return model

    if supports_tool_calling(model):
        logger.debug(f"Binding {len(tools)} tools to model")
        return model.bind_tools(tools)
    else:
        logger.warning(
            f"Model {model.__class__.__name__} does not support tool calling, "
            "returning model without tools"
        )
        return model


def supports_tool_calling(model: BaseChatModel) -> bool:
    """Check if a LangChain model supports tool calling.

    Checks the model's supports_tool_calling capability field when available,
    then falls back to checking for the bind_tools method.  Models on the
    blocklist have bind_tools but produce unreliable tool-call output.

    Note: For domain-level Model objects use model.supports_tool_calling directly.
    This function operates on LangChain BaseChatModel instances returned by
    provision_langchain_model.
    """
    if not hasattr(model, "bind_tools"):
        return False

    # Models that technically expose bind_tools but don't reliably produce
    # well-formed tool_use output (JSON mode works, function calling does not).
    TOOL_CALLING_BLOCKLIST = ["qwen2.5", "phi4", "gemma-3"]
    model_name = getattr(model, "model_name", "") or getattr(model, "model", "") or ""
    if any(blocked in model_name.lower() for blocked in TOOL_CALLING_BLOCKLIST):
        return False

    # Most modern LangChain chat model wrappers support bind_tools
    return callable(model.bind_tools)


def _is_qwen_model(model: "BaseChatModel") -> bool:
    """Check if a LangChain model instance is a Qwen2.5 model.

    Matches both Ollama (qwen2.5:32b) and OpenRouter (qwen/qwen2.5-32b-instruct).
    Qwen3+ models are NOT matched — they support tool calling.
    """
    model_name = getattr(model, "model_name", "") or getattr(model, "model", "") or ""
    if not isinstance(model_name, str):
        return False
    return "qwen2.5" in model_name.lower()


def _unwrap_completion_state(parsed: Any) -> Any:
    """Unwrap OpenRouter's completionState JSON envelope if present.

    OpenRouter + claude-sonnet-4 sometimes wraps with_structured_output() responses in:
        {"completionState": "complete", "result": {"records": [...]}, "type": "Object"}

    This function extracts the inner "result" dict. If no envelope is detected,
    returns the input unchanged (safe pass-through).

    Args:
        parsed: Parsed JSON (dict, list, or other). Expected to be the output of
                parse_json_response().

    Returns:
        Unwrapped dict if completionState envelope detected, otherwise input unchanged.
    """
    if not isinstance(parsed, dict):
        return parsed

    if "completionState" in parsed and "result" in parsed:
        inner = parsed["result"]
        if isinstance(inner, dict):
            return inner

    return parsed


def parse_json_response(response_text: str) -> dict[str, Any]:
    """Extract and parse a JSON object from LLM response text.

    Tries fenced ```json blocks first, then falls back to raw brace-depth
    matching. Returns the parsed dict. Raises ValueError if no JSON found
    or if the extracted structure is not valid JSON.
    """
    # E27-S4 TEMPORARY: Debug raw response to observe completionState behavior
    if os.environ.get("ACM_DEBUG_RAW_RESPONSE"):
        logger.debug(
            f"[parse_json_response] RAW INPUT (first 500 chars): "
            f"{response_text[:500]}"
        )
        logger.debug(
            f"[parse_json_response] completionState present: "
            f"{'completionState' in response_text}"
        )
    # Try ```json ... ``` blocks first
    json_match = re.search(
        r"```(?:json)?\s*\n?(\{.*?\})\s*\n?```",
        response_text,
        re.DOTALL,
    )
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Found JSON-like structure but failed to parse: {e}"
            ) from e

    # Fall back to raw brace-depth matching
    brace_start = response_text.find("{")
    if brace_start >= 0:
        depth = 0
        for idx, c in enumerate(response_text[brace_start:]):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    json_str = response_text[brace_start : brace_start + idx + 1]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError as e:
                        raise ValueError(
                            f"Found JSON-like structure but failed to parse: {e}"
                        ) from e

    raise ValueError("No JSON object found in response text")


def is_auth_error(error: Exception) -> bool:
    """Best-effort detection for provider authentication errors."""
    error_text = str(error).lower()
    error_type = type(error).__name__.lower()
    auth_markers = [
        "authenticationerror",
        "unauthorized",
        "invalid api key",
        "user not found",
        "error code: 401",
        "status code: 401",
        "access denied",
    ]
    return any(marker in error_text or marker in error_type for marker in auth_markers)


def is_provider_schema_error(error: Exception) -> bool:
    """Detect provider-specific structured output / schema rejection errors.

    These occur when an OpenRouter provider backend (e.g. Amazon Bedrock,
    Google Vertex AI) cannot handle the structured output request — either
    the JSON grammar is too complex, or the provider doesn't support the
    required beta headers/features.

    Unlike auth errors (401/403), these are 400-class errors that can be
    recovered from by falling back to manual JSON parsing
    (free-text + parse_json_response).
    """
    error_text = str(error).lower()

    # Direct schema/grammar complexity markers
    schema_markers = [
        "compiled grammar is too large",
        "grammar too large",
        "simplify your tool schemas",
        "properties maximum, minimum are not supported",
        "properties are not supported",
        "schema is too complex",
        "tool schema",
        "json schema",
        "structured output",
        "constrained decoding",
    ]

    # Provider incompatibility markers (e.g., Google Vertex AI rejecting
    # Anthropic beta headers, or Bedrock not supporting certain features)
    provider_compat_markers = [
        "provider returned error",
        "anthropic-beta",
        "unexpected value",
        "unsupported header",
        "not supported by this provider",
        "invalid_request_error",
    ]

    status_400 = "status code: 400" in error_text or "error code: 400" in error_text
    has_schema_keyword = any(marker in error_text for marker in schema_markers[:6])

    # Match if any direct schema marker hit
    if has_schema_keyword:
        return True

    # Match 400 errors with schema or provider compatibility markers
    if status_400:
        all_markers = schema_markers + provider_compat_markers
        if any(marker in error_text for marker in all_markers):
            return True

    return False


async def provision_extraction_fallback_model(
    failed_model_name: str,
    *,
    temperature: float,
    max_tokens: int,
) -> Optional[BaseChatModel]:
    """Provision a fallback extraction model when primary auth fails.

    Priority:
    1) Anthropic direct (preferred — native structured output support)
    2) OpenAI direct (fallback — reliable JSON mode)
    3) Ollama Qwen local fallbacks
    """
    lower_name = (failed_model_name or "").lower()
    candidates: list[tuple[str, str]] = []

    # Always try Anthropic direct first — most reliable for extraction
    if os.getenv("ANTHROPIC_API_KEY"):
        candidates.append(("anthropic", "claude-sonnet-4-20250514"))

    # OpenAI direct second
    if os.getenv("OPENAI_API_KEY"):
        candidates.append(("openai", "gpt-4o"))

    # Ollama local fallbacks
    if os.getenv("OLLAMA_API_BASE"):
        candidates.extend(
            [
                ("ollama", "qwen2.5:32b"),
                ("ollama", "qwen3:32b"),
            ]
        )

    seen: set[str] = set()
    unique_candidates: list[tuple[str, str]] = []
    for provider, model_name in candidates:
        key = f"{provider}/{model_name}".lower()
        if key in seen or model_name.lower() == lower_name:
            continue
        seen.add(key)
        unique_candidates.append((provider, model_name))

    for provider, model_name in unique_candidates:
        try:
            logger.warning(
                "Attempting extraction fallback model after auth failure: "
                f"{provider}/{model_name}"
            )
            model = AIFactory.create_language(
                model_name=model_name,
                provider=provider,
                config={
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            assert isinstance(model, LanguageModel), (
                f"Fallback model is not a LanguageModel: {model}"
            )
            lc_model = model.to_langchain()
            return _apply_openrouter_preferences(lc_model)
        except Exception as fallback_error:
            logger.warning(
                f"Fallback candidate {provider}/{model_name} failed: {fallback_error}"
            )

    return None
