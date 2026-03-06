"""Langfuse observability integration for ACM-AI extraction pipeline."""

import os
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Tuple

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from loguru import logger

_TRUE_VALUES = {"1", "true", "yes", "on"}
_DEFAULT_LANGFUSE_HOST = "https://cloud.langfuse.com"


def is_langfuse_enabled() -> bool:
    """Return whether Langfuse tracing is enabled via environment config."""

    return os.getenv("LANGFUSE_ENABLED", "false").strip().lower() in _TRUE_VALUES


def _try_inject_otel_trace_context(trace_id: str) -> Any:
    """Inject a Langfuse trace_id into the OTel context so Logfire spans nest under it.

    When LOGFIRE_ENABLED=true and logfire.instrument_pydantic(include={...}) is active,
    Pydantic validation spans created inside the current asyncio task will carry this
    trace_id as their traceparent. Langfuse routes them under the matching trace.

    Returns an OTel context token to pass to _try_detach_otel_context(), or None if
    opentelemetry is unavailable or OTel context injection fails (non-fatal).
    """
    try:
        from opentelemetry import context as otel_ctx
        from opentelemetry import trace as otel_trace
        from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags

        trace_id_int = int(trace_id.replace("-", ""), 16)
        span_ctx = SpanContext(
            trace_id=trace_id_int,
            span_id=0x1A2B3C4D5E6F7A8B,  # fixed dummy parent span_id
            is_remote=True,
            trace_flags=TraceFlags(TraceFlags.SAMPLED),
        )
        ctx = otel_trace.set_span_in_context(NonRecordingSpan(span_ctx))
        return otel_ctx.attach(ctx)
    except Exception:
        return None


def _try_detach_otel_context(token: Any) -> None:
    """Detach OTel context token set by _try_inject_otel_trace_context()."""
    if token is None:
        return
    try:
        from opentelemetry import context as otel_ctx

        otel_ctx.detach(token)
    except Exception:
        pass


def get_langfuse_handler(trace_id: Optional[str] = None) -> Optional[CallbackHandler]:
    """Create a Langfuse LangChain callback handler when configured.

    Args:
        trace_id: Optional pre-generated UUID string to use as the Langfuse trace_id.
            Pass this when you also inject the same ID into the OTel context via
            _try_inject_otel_trace_context() so that Logfire spans nest under this trace.

    Returns:
        CallbackHandler when Langfuse is enabled and credentials are present,
        otherwise None.
    """

    if not is_langfuse_enabled():
        return None

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_BASE_URL", _DEFAULT_LANGFUSE_HOST)

    if not public_key or not secret_key:
        logger.warning(
            "LANGFUSE_ENABLED=true but LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY "
            "are missing. Continuing without Langfuse tracing."
        )
        return None

    try:
        # Initialize client first so CallbackHandler(public_key=...) can bind to it.
        Langfuse(public_key=public_key, secret_key=secret_key, host=host)
        trace_context = {"trace_id": trace_id} if trace_id else None
        return CallbackHandler(
            public_key=public_key,
            update_trace=True,
            **({"trace_context": trace_context} if trace_context else {}),
        )
    except Exception as exc:
        logger.warning(
            "Failed to initialize Langfuse callback handler: {error}. "
            "Continuing without Langfuse tracing.",
            error=str(exc),
        )
        return None


def build_langfuse_metadata(
    source_id: str,
    extraction_model: Optional[str] = None,
    document_type: Optional[str] = None,
    command_id: Optional[str] = None,
    pipeline_version: str = "E26+",
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build metadata payload for LangGraph/LangChain runnable config.

    Includes Langfuse-specific metadata keys recognized by CallbackHandler:
    - langfuse_session_id
    - langfuse_user_id
    - langfuse_tags
    """

    clean_source_id = str(source_id)
    clean_doc_type = (document_type or "unknown").strip() or "unknown"
    tags = ["acm-extraction"]
    if clean_doc_type.lower() != "unknown":
        tags.append(clean_doc_type.lower())

    metadata: Dict[str, Any] = {
        "source_id": clean_source_id,
        "document_type": clean_doc_type,
        "extraction_model": extraction_model or "default",
        "pipeline_version": pipeline_version,
        "docling_enabled": os.getenv("DOCLING_DIRECT_TABLE_EXTRACTION", "true"),
        "langfuse_session_id": f"extraction-{clean_source_id}",
        "langfuse_user_id": f"source-{clean_source_id}",
        "langfuse_tags": tags,
    }

    if command_id:
        metadata["command_id"] = str(command_id)

    if extra_metadata:
        metadata.update(extra_metadata)

    return metadata


def append_langfuse_callback(
    callbacks: Optional[List[Any]],
    handler: Optional[CallbackHandler],
) -> List[Any]:
    """Append Langfuse callback handler without replacing existing callbacks."""

    merged: List[Any] = list(callbacks) if callbacks else []
    if handler is not None:
        merged.append(handler)
    return merged


def flush_langfuse_handler(handler: Optional[CallbackHandler]) -> None:
    """Flush pending Langfuse observations without raising errors."""

    if handler is None:
        return

    try:
        client = getattr(handler, "client", None)
        if client is not None and hasattr(client, "flush"):
            client.flush()
    except Exception as exc:
        logger.debug("Langfuse flush skipped due to error: {error}", error=str(exc))


@contextmanager
def langfuse_tracing(
    graph_name: str,
    source_id: str = "N/A",
    notebook_id: Optional[str] = None,
    operation_type: Optional[str] = None,
    extra_tags: Optional[List[str]] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Generator[Tuple[List[Any], Dict[str, Any]], None, None]:
    """Context manager that yields (callbacks, metadata) and auto-flushes.

    Usage::

        with langfuse_tracing("chat", source_id="chat", operation_type="chat") as (cb, meta):
            config = merge_langfuse_into_config(base_config, cb, meta)
            graph.invoke(input, config=config)
    """
    # Pre-generate trace_id so we can pass it to both the CallbackHandler and
    # the OTel context. This makes Logfire Pydantic validation spans nest under
    # this Langfuse trace when LOGFIRE_ENABLED=true and instrument_pydantic() is active.
    trace_id = str(uuid.uuid4())
    handler = get_langfuse_handler(trace_id=trace_id)
    callbacks = append_langfuse_callback([], handler)

    # Inject trace_id into OTel context so Logfire spans inherit it as traceparent.
    # Non-fatal: returns None if opentelemetry not available or Logfire disabled.
    otel_token = _try_inject_otel_trace_context(trace_id) if handler else None

    tags = [operation_type or graph_name]
    if extra_tags:
        tags.extend(extra_tags)

    metadata = build_langfuse_metadata(
        source_id=source_id,
        extraction_model=graph_name,
        document_type=operation_type or graph_name,
        extra_metadata={
            **({"notebook_id": notebook_id} if notebook_id else {}),
            "langfuse_tags": tags,
            **(extra_metadata or {}),
        },
    )
    try:
        yield callbacks, metadata
    finally:
        _try_detach_otel_context(otel_token)
        flush_langfuse_handler(handler)


def merge_langfuse_into_config(
    config: Dict[str, Any],
    callbacks: List[Any],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """Merge Langfuse callbacks/metadata into an existing RunnableConfig dict."""
    if not callbacks:
        return config
    merged = dict(config)
    merged["callbacks"] = callbacks
    merged["metadata"] = metadata
    return merged
