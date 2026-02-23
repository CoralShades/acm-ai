import json
import re
from typing import Any, List, Optional

from esperanto import LanguageModel
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from loguru import logger

from open_notebook.domain.models import model_manager
from open_notebook.utils import token_count


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
    return model.to_langchain()


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
            raise ValueError(f"Found JSON-like structure but failed to parse: {e}") from e

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
