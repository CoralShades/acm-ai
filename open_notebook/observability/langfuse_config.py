"""Langfuse observability integration for ACM-AI extraction pipeline."""

import os
from typing import Any, Dict, List, Optional

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from loguru import logger

_TRUE_VALUES = {"1", "true", "yes", "on"}
_DEFAULT_LANGFUSE_HOST = "https://cloud.langfuse.com"


def is_langfuse_enabled() -> bool:
    """Return whether Langfuse tracing is enabled via environment config."""

    return os.getenv("LANGFUSE_ENABLED", "false").strip().lower() in _TRUE_VALUES


def get_langfuse_handler() -> Optional[CallbackHandler]:
    """Create a Langfuse LangChain callback handler when configured.

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
        return CallbackHandler(public_key=public_key, update_trace=True)
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
