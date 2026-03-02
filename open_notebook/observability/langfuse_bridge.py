"""Bridge PipelineLogger events into Langfuse via LangChain custom events."""

from typing import Any, Dict, Optional

from langchain_core.callbacks.manager import dispatch_custom_event
from langchain_core.runnables import RunnableConfig
from loguru import logger

PIPELINE_EVENT_NAME = "acm.pipeline.stage"


def emit_pipeline_event(
    event_type: str,
    payload: Dict[str, Any],
    config: Optional[RunnableConfig] = None,
) -> None:
    """Emit a custom pipeline event to active callback handlers.

    When Langfuse callback handling is active, these custom events are attached
    to the same trace as LangGraph node execution, enabling cross-view analysis
    between LangChain-level spans and ACM pipeline stage events.
    """

    data = dict(payload)
    data["event_type"] = event_type

    try:
        dispatch_custom_event(PIPELINE_EVENT_NAME, data, config=config)
    except Exception as exc:
        # Non-fatal: tracing must never break extraction execution.
        logger.debug(
            "Pipeline custom event dispatch skipped: {error}",
            error=str(exc),
        )
