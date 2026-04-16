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
                result[k] = {pk: _resolve_refs(pv, defs) for pk, pv in v.items()}
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

# Module-level caches for V3 schemas (E30-S7)
_V3_BUILDING_JSON_SCHEMA: dict | None = None
_V3_ITEM_JSON_SCHEMA: dict | None = None


def _get_acm_extraction_schema() -> dict:
    """Lazily generate and cache the JSON Schema for ACMExtractionResult."""
    global _ACM_EXTRACTION_JSON_SCHEMA
    if _ACM_EXTRACTION_JSON_SCHEMA is None:
        from open_notebook.extractors.acm_schemas import ACMExtractionResult

        _ACM_EXTRACTION_JSON_SCHEMA = pydantic_to_openrouter_schema(ACMExtractionResult)
    return _ACM_EXTRACTION_JSON_SCHEMA


def _get_v3_building_schema() -> dict:
    """Lazily generate and cache JSON Schema for BuildingExtractionResult (E30-S7)."""
    global _V3_BUILDING_JSON_SCHEMA
    if _V3_BUILDING_JSON_SCHEMA is None:
        from open_notebook.extractors.acm_schemas_v3 import BuildingExtractionResult

        _V3_BUILDING_JSON_SCHEMA = pydantic_to_openrouter_schema(
            BuildingExtractionResult
        )
    return _V3_BUILDING_JSON_SCHEMA


def _get_v3_item_schema() -> dict:
    """Lazily generate and cache JSON Schema for ACMItemExtractionResult (E30-S7)."""
    global _V3_ITEM_JSON_SCHEMA
    if _V3_ITEM_JSON_SCHEMA is None:
        from open_notebook.extractors.acm_schemas_v3 import ACMItemExtractionResult

        _V3_ITEM_JSON_SCHEMA = pydantic_to_openrouter_schema(ACMItemExtractionResult)
    return _V3_ITEM_JSON_SCHEMA


def _apply_ollama_extraction_settings(
    lc_model: BaseChatModel,
    schema_dict: dict | None = None,
) -> BaseChatModel:
    """Apply Ollama-specific extraction settings: format + num_ctx.

    Separated from _inject_response_format so it can be called without a
    JSON schema (e.g. in provision_extraction_fallback_model where the schema
    is applied later by the calling extraction function).

    - format: When *schema_dict* is provided, passes the full JSON schema to
      Ollama's ``format`` parameter — this uses grammar-constrained generation
      to guarantee output matches the schema exactly. When *schema_dict* is
      ``None``, falls back to ``format="json"`` (free-form JSON).
    - num_ctx: sets the context window to 32768 (or OLLAMA_NUM_CTX env var),
      replacing the Ollama default of 8192 which truncates large ARA docs.

    No-op for non-Ollama models.
    """
    is_ollama = any("ollama" in c.__name__.lower() for c in type(lc_model).__mro__)
    if not is_ollama:
        return lc_model

    model_name = (
        getattr(lc_model, "model_name", "") or getattr(lc_model, "model", "") or ""
    )

    # ChatOllama.format is a first-class Pydantic field — NOT part of
    # model_kwargs. Setting model_kwargs["format"] is silently ignored because
    # ChatOllama builds its request payload from self.format directly
    # (see langchain_ollama/chat_models.py: params["format"] = self.format).
    # ChatOllama.format accepts Union[Literal['', 'json'], dict, None].
    if schema_dict is not None:
        object.__setattr__(lc_model, "format", schema_dict)
    else:
        object.__setattr__(lc_model, "format", "json")

    format_label = "schema" if schema_dict else "json"

    # Set num_ctx for extraction models. Ollama defaults to 8192 tokens which
    # is far too small for 50k+ char ARA documents. Use env var OLLAMA_NUM_CTX
    # if set, otherwise default to 32768 (adequate for qwen2.5:7b/32b and
    # phi4:14b without OOM risk on 16GB VRAM).
    num_ctx_env = os.getenv("OLLAMA_NUM_CTX")
    num_ctx_target = int(num_ctx_env) if num_ctx_env else 32768
    # Only set num_ctx if the caller didn't explicitly configure it.
    # A non-zero current_num_ctx means the caller deliberately chose a value
    # (e.g. per-row extraction uses num_ctx=2048 via ACM_ROW_EXTRACTION_NUM_CTX).
    current_num_ctx = getattr(lc_model, "num_ctx", None) or 0
    if current_num_ctx == 0:
        object.__setattr__(lc_model, "num_ctx", num_ctx_target)

    logger.debug(
        f"Applied Ollama extraction settings: "
        f"format={format_label}, num_ctx={getattr(lc_model, 'num_ctx', None)} "
        f"for model {model_name}"
    )
    return lc_model


def _inject_response_format(
    lc_model: BaseChatModel,
    schema_dict: dict,
    schema_name: str,
) -> BaseChatModel:
    """Inject response_format: json_schema into model's extra_body.

    Stage-specific — called AFTER provision_langchain_model() and BEFORE
    model.ainvoke(). Applies to OpenRouter models (json_schema) and Ollama
    models (format=json + num_ctx).

    This enforces schema validation at the OpenRouter layer, so the LLM
    returns JSON that conforms to the given schema. Combined with
    Response Healing plugin (E27-S3), this provides production-grade
    structured output without with_structured_output().

    For Ollama, delegates to _apply_ollama_extraction_settings() which sets
    format="json" (first-class ChatOllama field, not model_kwargs) and
    num_ctx=32768 to handle large ARA documents.

    Args:
        lc_model: LangChain model (already provisioned with OpenRouter prefs)
        schema_dict: JSON Schema dict (from pydantic_to_openrouter_schema)
        schema_name: Human-readable schema name (e.g. "ACMExtractionResult")

    Returns:
        The same model with response_format injected into extra_body.
    """
    # Ollama: delegate to shared helper with schema for grammar-constrained output
    is_ollama = any("ollama" in c.__name__.lower() for c in type(lc_model).__mro__)
    if is_ollama:
        return _apply_ollama_extraction_settings(lc_model, schema_dict=schema_dict)

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
        f"Injected response_format: json_schema ({schema_name}) into model extra_body"
    )
    return lc_model


# Boundary patterns for Ollama token-budget content splitting (E32-S8)
_BUDGET_ROOM_RE = re.compile(r"B\d{3}\s*-\s*R\d{4,5}")
_BUDGET_ARA_RE = re.compile(r"(?:^|\n)(\d+)\.\s", re.MULTILINE)


def _split_content_by_char_budget(
    content: str,
    max_chars: int,
    content_boundary_re: re.Pattern | None = None,
) -> list[str]:
    """Split content at room/item boundaries to fit within max_chars per chunk.

    Boundary detection (tried in order, first match wins):
    - Custom pattern: caller-supplied content_boundary_re (if provided)
    - Standard DET format: B###-R#### room headers
    - ARA format: numbered items like "1. " at start of line

    If a single boundary segment exceeds max_chars, that segment is
    hard-truncated with a WARNING (graceful degrade — never silently drops).
    """
    boundaries = []
    if content_boundary_re is not None:
        boundaries = list(content_boundary_re.finditer(content))
    if not boundaries:
        boundaries = list(_BUDGET_ROOM_RE.finditer(content))
    if not boundaries:
        boundaries = list(_BUDGET_ARA_RE.finditer(content))

    if not boundaries:
        if len(content) > max_chars:
            logger.info(
                f"Content ({len(content)} chars) exceeds budget "
                f"({max_chars} chars) and no room boundaries found. "
                f"Splitting into character-based chunks."
            )
            return [
                content[i : i + max_chars] for i in range(0, len(content), max_chars)
            ]
        return [content]

    # Build (start, end) segments: preamble + each room
    segments: list[tuple[int, int]] = []
    if boundaries[0].start() > 0:
        segments.append((0, boundaries[0].start()))
    for i, match in enumerate(boundaries):
        end = boundaries[i + 1].start() if i + 1 < len(boundaries) else len(content)
        segments.append((match.start(), end))

    # Greedily accumulate into budget-sized chunks
    chunks: list[str] = []
    chunk_start = segments[0][0]
    chunk_end = segments[0][0]

    for seg_start, seg_end in segments:
        seg_len = seg_end - seg_start
        current_chunk_len = chunk_end - chunk_start

        if seg_len > max_chars:
            # Single oversized segment — flush current chunk, then truncate
            if chunk_end > chunk_start:
                chunks.append(content[chunk_start:chunk_end])
            logger.warning(
                f"Single room/item content ({seg_len} chars) exceeds budget "
                f"({max_chars} chars). Hard-truncating this segment."
            )
            chunks.append(content[seg_start : seg_start + max_chars])
            chunk_start = seg_end
            chunk_end = seg_end
        elif current_chunk_len > 0 and current_chunk_len + seg_len > max_chars:
            # Adding this segment would overflow — flush and start fresh
            chunks.append(content[chunk_start:chunk_end])
            chunk_start = seg_start
            chunk_end = seg_end
        else:
            chunk_end = seg_end

    # Flush final chunk
    if chunk_end > chunk_start:
        chunks.append(content[chunk_start:chunk_end])

    return chunks if chunks else [content]


def _ollama_split_by_budget(
    content: str,
    lc_model: BaseChatModel,
    content_boundary_re: re.Pattern | None = None,
) -> list[str]:
    """Split content into Ollama token-budget chunks (E32-S8).

    Returns [content] unchanged for non-Ollama models or content within budget.
    For Ollama, splits at room/item boundaries to stay within the effective
    context window. If a single room still exceeds the budget, hard-truncates
    that room with a WARNING (graceful degrade — never silently drops records).

    Limit priority:
      1. OLLAMA_MAX_CONTENT_CHARS env var (explicit override)
      2. model.num_ctx * 3.5 chars/token (model-size aware)
      3. 8192 * 3.5 = 28672 chars (default fallback)
    """
    is_ollama = any("ollama" in c.__name__.lower() for c in type(lc_model).__mro__)
    if not is_ollama:
        return [content]

    env_override = os.getenv("OLLAMA_MAX_CONTENT_CHARS")
    if env_override:
        max_chars = int(env_override)
    else:
        num_ctx = getattr(lc_model, "num_ctx", None) or 8192
        output_reserve_ratio = 0.3
        max_chars = int(num_ctx * 3.5 * (1 - output_reserve_ratio))

    if len(content) <= max_chars:
        return [content]

    logger.info(
        f"Ollama content ({len(content)} chars) exceeds budget ({max_chars} chars). "
        f"Splitting into budget chunks."
    )
    return _split_content_by_char_budget(content, max_chars, content_boundary_re)


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
                f"[{stage_name}] Provider: {actual_provider} | Model: {actual_model}"
            )
        return {"provider_name": actual_provider, "model": actual_model}

    # Method 2: Query Generation API (definitive, async)
    if not gen_id:
        gen_id = metadata.get("id") or (
            getattr(response, "additional_kwargs", {}) or {}
        ).get("id")

    if not gen_id:
        logger.debug(f"[{stage_name}] No generation ID — cannot verify provider")
        return None

    # E30-S8: prefer ACM-namespaced key, fall back to bare key for
    # non-extraction callers (e.g. general chat workflows)
    api_key = os.getenv("ACM_OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.debug(
            f"[{stage_name}] No ACM_OPENROUTER_API_KEY — skipping Generation API lookup"
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
    elif default_type == "extraction":
        # E35-S4: Primary extraction priority chain (Ollama -> Anthropic -> OpenRouter)
        lc_model = await _provision_extraction_primary_model(**kwargs)
        if lc_model is not None:
            return lc_model
        # Fall through to DB default if no provider available
        model = await model_manager.get_default_model(default_type, **kwargs)
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


class TruncationError(ValueError):
    """Raised when JSON is structurally incomplete (truncated by LLM output limit)."""

    pass


def _extract_json_objects(text: str) -> tuple[list[str], bool]:
    """Extract all complete top-level JSON objects and detect truncation.

    Returns:
        (list of complete JSON object strings, truncated flag)
    """
    objects: list[str] = []
    i = 0
    n = len(text)
    truncated = False
    while i < n:
        if text[i] == "{":
            start = i
            depth = 0
            in_string = False
            j = i
            while j < n:
                c = text[j]
                if in_string:
                    if c == "\\" and j + 1 < n:
                        j += 2
                        continue
                    if c == '"':
                        in_string = False
                else:
                    if c == '"':
                        in_string = True
                    elif c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                        if depth == 0:
                            objects.append(text[start : j + 1])
                            break
                j += 1
            else:
                # Hit EOF with open braces — truncated JSON
                truncated = True
            i = j + 1
        else:
            i += 1
    return objects, truncated


def parse_json_response(response_text: str) -> dict[str, Any]:
    """Extract and parse a JSON object from LLM response text.

    Resilient parser that handles:
    - Markdown fences (```json ... ```)
    - Conversational preamble/suffix text
    - Multiple JSON blocks (returns the largest valid object)
    - Truncated JSON (raises TruncationError)

    Returns the parsed dict. Raises ValueError if no JSON found,
    or TruncationError if JSON is structurally incomplete.
    """
    # Step 1: Strip markdown fence markers
    stripped = re.sub(r"```(?:json|JSON)?\s*\n?", "", response_text)
    # Also strip trailing ``` that aren't part of a fence open
    stripped = stripped.replace("```", "")

    # Step 2: Extract all complete JSON objects via brace-depth scan
    candidates, truncated = _extract_json_objects(stripped)

    # Step 3: Try to parse each candidate, keep valid dicts
    valid: list[tuple[dict[str, Any], str]] = []
    for raw in candidates:
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                valid.append((obj, raw))
        except json.JSONDecodeError:
            continue

    # Step 4: Return largest valid object
    if valid:
        # Select by serialized length (deterministic)
        best = max(valid, key=lambda pair: len(pair[1]))
        return best[0]

    # Step 5: No valid objects — check for truncation
    if truncated:
        # Find the incomplete JSON for error context
        brace_start = stripped.find("{")
        preview = stripped[brace_start : brace_start + 100] if brace_start >= 0 else ""
        raise TruncationError(
            f"JSON is truncated (incomplete braces at end of response). "
            f"Preview: {preview!r}..."
        )

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


async def _get_db_extraction_model() -> Optional[str]:
    """Read user-configured extraction model from SurrealDB defaults.

    Returns a plain model name (e.g. "qwen2.5:7b") suitable for passing to
    any provider. Provider prefixes like "ollama/" or "anthropic/" are stripped.
    If the resolved model belongs to a non-Ollama provider, returns None so
    the caller falls back to env var / hardcoded default.
    """
    try:
        from open_notebook.database.repository import repo_query

        result = await repo_query(
            "SELECT default_extraction_model FROM open_notebook:default_models LIMIT 1;"
        )
        if result and isinstance(result, list) and len(result) > 0:
            model_val = result[0].get("default_extraction_model")
            if not model_val:
                return None
            model_val = str(model_val)
            # model_val may be a SurrealDB record ID (e.g. "model:znay2wr8u9q39lxj2q37")
            # — resolve it to the actual model name from the model table.
            if model_val.startswith("model:"):
                # Use direct record reference — SurrealDB param binding
                # doesn't auto-cast strings to record IDs.
                # Sanitize: record ID part should be alphanumeric only
                record_part = model_val[len("model:") :]
                if not record_part.isalnum():
                    logger.warning(f"Invalid model record ID format: {model_val}")
                    return None
                model_record = await repo_query(
                    f"SELECT name, provider FROM model:{record_part};"
                )
                if model_record and len(model_record) > 0:
                    resolved = model_record[0].get("name")
                    provider = model_record[0].get("provider", "")
                    if resolved:
                        # Only return if this is an Ollama model — non-Ollama
                        # models (e.g. openrouter/anthropic/claude-sonnet-4)
                        # should not be passed to the Ollama candidate.
                        if provider and provider != "ollama":
                            logger.warning(
                                f"DB extraction model {model_val} is {provider}/{resolved}, "
                                "not Ollama — skipping for Ollama candidate"
                            )
                            return None
                        logger.info(
                            f"Resolved extraction model {model_val} -> {resolved}"
                        )
                        return str(resolved)
                logger.warning(
                    f"Could not resolve extraction model record ID: {model_val}"
                )
                return None
            # Plain string model name (e.g. "ollama/qwen2.5:32b" or "llama3.1:8b")
            if "/" in model_val:
                model_val = model_val.split("/", 1)[1]
            return model_val
    except Exception as e:
        logger.debug(f"Could not read DB extraction model default: {e}")
    return None


async def _provision_extraction_primary_model(
    **kwargs,
) -> Optional[BaseChatModel]:
    """Primary extraction model provisioning with Ollama->Anthropic->OpenRouter priority.

    E35-S4: When default_type='extraction' and no explicit model_id, use this
    priority chain instead of only reading the DB-stored default.
    Uses ACM-namespaced API keys only (never bare ANTHROPIC_API_KEY).

    Returns None if no provider is available (caller falls through to DB default).
    """
    candidates: list[tuple[str, str, Optional[str]]] = []

    # 1) Ollama first — free, local (only if reachable)
    ollama_base = os.getenv("OLLAMA_API_BASE")
    if ollama_base:
        try:
            import urllib.request

            urllib.request.urlopen(f"{ollama_base}/api/tags", timeout=2)
            db_model = await _get_db_extraction_model()
            model_name = db_model or os.getenv("ACM_EXTRACTION_MODEL", "llama3.1:8b")
            candidates.append(("ollama", model_name, None))
        except Exception:
            logger.info("Ollama not reachable at %s — skipping", ollama_base)

    # 2) Anthropic Direct — ACM-namespaced key ONLY
    acm_anthropic_key = os.getenv("ACM_ANTHROPIC_API_KEY")
    if acm_anthropic_key:
        candidates.append(("anthropic", "claude-sonnet-4-20250514", acm_anthropic_key))

    # 3) OpenRouter — ACM-namespaced key ONLY
    acm_openrouter_key = os.getenv("ACM_OPENROUTER_API_KEY")
    if acm_openrouter_key:
        candidates.append(
            ("openrouter", "anthropic/claude-sonnet-4", acm_openrouter_key)
        )

    # 4) OpenAI — fallback if no ACM-specific keys are set
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        candidates.append(("openai", "gpt-4o-mini", openai_key))

    for provider, model_name, api_key in candidates:
        try:
            config: dict = {**kwargs}
            if api_key:
                config["api_key"] = api_key
            # Cap max_tokens for models with lower limits
            if provider == "openai" and config.get("max_tokens", 0) > 16384:
                config["max_tokens"] = 16384
            model = AIFactory.create_language(
                model_name=model_name,
                provider=provider,
                config=config,
            )
            assert isinstance(model, LanguageModel)
            lc_model = model.to_langchain()
            lc_model = _apply_openrouter_preferences(lc_model)
            lc_model = _apply_ollama_extraction_settings(lc_model)
            logger.info(f"Primary extraction model: {provider}/{model_name}")
            return lc_model
        except Exception as e:
            logger.warning(
                f"Primary extraction candidate {provider}/{model_name} failed: {e}"
            )

    return None


async def provision_extraction_fallback_model(
    failed_model_name: str,
    *,
    temperature: float,
    max_tokens: int,
) -> Optional[BaseChatModel]:
    """Provision a fallback extraction model when primary auth fails.

    E30-S8 — ACM extraction uses ONLY ACM-namespaced env vars:
      ACM_ANTHROPIC_API_KEY (not bare ANTHROPIC_API_KEY)
      ACM_OPENROUTER_API_KEY (not bare OPENROUTER_API_KEY)

    Priority (first available wins):
    1) Ollama local (if OLLAMA_API_BASE set) — zero cost, low latency
    2) Anthropic direct (if ACM_ANTHROPIC_API_KEY set) — best extraction quality
    3) OpenRouter (if ACM_OPENROUTER_API_KEY set) — cloud fallback
    """
    lower_name = (failed_model_name or "").lower()
    # (provider, model_name, api_key_override)
    candidates: list[tuple[str, str, Optional[str]]] = []

    # 1) Ollama first — free, local, no API key needed
    if os.getenv("OLLAMA_API_BASE"):
        candidates.extend(
            [
                ("ollama", "qwen2.5:7b", None),  # E32-S6 spike winner
                ("ollama", "qwen2.5:32b", None),
                ("ollama", "qwen3:32b", None),
            ]
        )

    # 2) Anthropic direct — ACM-namespaced key ONLY
    acm_anthropic_key = os.getenv("ACM_ANTHROPIC_API_KEY")
    if acm_anthropic_key:
        candidates.append(("anthropic", "claude-sonnet-4-20250514", acm_anthropic_key))

    # 3) OpenRouter — ACM-namespaced key ONLY
    acm_openrouter_key = os.getenv("ACM_OPENROUTER_API_KEY")
    if acm_openrouter_key:
        candidates.append(
            ("openrouter", "anthropic/claude-sonnet-4", acm_openrouter_key)
        )

    seen: set[str] = set()
    unique_candidates: list[tuple[str, str, Optional[str]]] = []
    for provider, model_name, api_key in candidates:
        key = f"{provider}/{model_name}".lower()
        if key in seen or model_name.lower() == lower_name:
            continue
        seen.add(key)
        unique_candidates.append((provider, model_name, api_key))

    for provider, model_name, api_key in unique_candidates:
        try:
            logger.warning(
                "Attempting extraction fallback model after auth failure: "
                f"{provider}/{model_name}"
            )
            config: dict = {
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if api_key:
                config["api_key"] = api_key
            model = AIFactory.create_language(
                model_name=model_name,
                provider=provider,
                config=config,
            )
            assert isinstance(model, LanguageModel), (
                f"Fallback model is not a LanguageModel: {model}"
            )
            lc_model = model.to_langchain()
            lc_model = _apply_openrouter_preferences(lc_model)
            # Apply format=json and num_ctx for Ollama fallback models.
            # _inject_response_format returns early after applying Ollama
            # settings so the empty schema args are never used.  For non-Ollama
            # fallbacks (Anthropic, OpenRouter) the caller is responsible for
            # injecting the schema via _inject_response_format after selecting
            # the schema appropriate to the extraction stage.
            lc_model = _apply_ollama_extraction_settings(lc_model)
            return lc_model
        except Exception as fallback_error:
            logger.warning(
                f"Fallback candidate {provider}/{model_name} failed: {fallback_error}"
            )

    return None
