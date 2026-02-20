from typing import List, Optional

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
    If context > 105_000, returns the large_context_model
    If model_id is specified in Config, returns that model
    Otherwise, returns the default model for the given type
    """
    tokens = token_count(content)

    if tokens > 105_000:
        logger.debug(
            f"Using large context model because the content has {tokens} tokens"
        )
        model = await model_manager.get_default_model("large_context", **kwargs)
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

    Checks for the bind_tools method and known tool-calling capable model types.
    """
    if not hasattr(model, "bind_tools"):
        return False

    # Models that are known to support tool calling
    # Most modern LangChain chat model wrappers support bind_tools
    return callable(model.bind_tools)
