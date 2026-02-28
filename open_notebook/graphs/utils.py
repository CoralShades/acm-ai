import json
import os
import re
from typing import Any, List, Optional

from esperanto import AIFactory, LanguageModel
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from loguru import logger

from open_notebook.domain.models import model_manager
from open_notebook.utils import token_count

# ---------------------------------------------------------------------------
# OpenRouter provider routing preferences
# ---------------------------------------------------------------------------

# Providers that reject complex structured-output schemas or have
# incompatible beta-header requirements.  Excluding these forces
# OpenRouter to route to direct-API providers (Anthropic, OpenAI, etc.)
# that reliably support tool-calling / JSON-mode extraction.
OPENROUTER_IGNORED_PROVIDERS = [
    "Amazon Bedrock",
    "Azure",
]

# Preferred provider order — direct providers first.
# OpenRouter selects from top to bottom based on availability.
OPENROUTER_PROVIDER_ORDER = [
    "Anthropic",
    "Google",
    "OpenAI",
]


def _apply_openrouter_preferences(lc_model: BaseChatModel) -> BaseChatModel:
    """Inject OpenRouter provider routing into a LangChain model.

    Only applies when the model's base_url points to OpenRouter.
    Adds ``provider.ignore``, ``provider.order``, and the
    ``middle-out`` transform for response healing.

    Model-aware routing: Anthropic/Claude models are restricted to the
    Anthropic provider only, because other providers (e.g. Google) reject
    the ``anthropic-beta: structured-outputs-*`` header that LangChain
    sends with ``with_structured_output()``.
    """
    base_url = (
        getattr(lc_model, "openai_api_base", None)
        or getattr(lc_model, "base_url", None)
        or ""
    )
    if "openrouter.ai" not in str(base_url).lower():
        return lc_model

    # Detect model family from LangChain model attributes
    model_name = (
        getattr(lc_model, "model_name", None) or getattr(lc_model, "model", None) or ""
    )
    model_name_lower = str(model_name).lower()
    is_anthropic = "claude" in model_name_lower or model_name_lower.startswith(
        "anthropic/"
    )

    if is_anthropic:
        # Anthropic models MUST only route to the Anthropic provider.
        # Other providers (Google, etc.) reject the anthropic-beta header
        # that LangChain injects for structured output.
        ignore_list = OPENROUTER_IGNORED_PROVIDERS + ["Google"]
        order_list = ["Anthropic"]
    else:
        ignore_list = OPENROUTER_IGNORED_PROVIDERS
        order_list = OPENROUTER_PROVIDER_ORDER

    openrouter_body = {
        "provider": {
            "ignore": ignore_list,
            "order": order_list,
            "require_parameters": True,
        },
        "transforms": ["middle-out"],
    }
    existing = getattr(lc_model, "model_kwargs", {}) or {}
    # Merge into extra_body so the OpenAI SDK passes these in the HTTP
    # request body (not as create() kwargs which it would reject).
    prev_extra = existing.get("extra_body", {})
    object.__setattr__(
        lc_model,
        "model_kwargs",
        {
            **existing,
            "extra_body": {**prev_extra, **openrouter_body},
        },
    )
    logger.info(
        f"Applied OpenRouter provider preferences: "
        f"ignore={ignore_list}, "
        f"order={order_list}"
    )
    return lc_model


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
