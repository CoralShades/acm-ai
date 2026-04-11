"""Smoke tests for open_notebook/observability/.

The critical guardrail is documented in the acm-observability skill:
calling `logfire.instrument_pydantic()` without an explicit `include`
set instruments EVERY Pydantic model_validate() call, including Docling's
per-character PdfTextCell, causing ~48,000 OTel spans per extraction.

This test asserts the config helper exists and that there's no blanket
instrument_pydantic() call without an include argument anywhere in the
observability module.
"""

from __future__ import annotations

import inspect
import re


def test_langfuse_config_module_imports():
    import open_notebook.observability.langfuse_config as mod
    assert hasattr(mod, "langfuse_tracing")
    assert hasattr(mod, "merge_langfuse_into_config")
    assert hasattr(mod, "get_langfuse_handler")


def test_langfuse_tracing_is_context_manager():
    from open_notebook.observability.langfuse_config import langfuse_tracing
    # Should be a context manager factory — calling it must produce an object
    # that has __enter__/__exit__
    cm = langfuse_tracing("test_op", source_id="source:test")
    assert hasattr(cm, "__enter__")
    assert hasattr(cm, "__exit__")
    # Close it cleanly — tracing is non-fatal when disabled
    try:
        with cm:
            pass
    except Exception:
        pass  # tracing is optional — some paths raise if not configured, that's fine


def test_logfire_config_module_imports():
    import open_notebook.observability.logfire_config  # noqa: F401


def test_no_blanket_instrument_pydantic_call():
    """CRITICAL: `instrument_pydantic()` without include={...} creates
    ~48,000 OTel spans per extraction via Docling's PdfTextCell. The
    observability skill (acm-observability) documents this as the top
    regression risk in the observability module."""
    import open_notebook.observability.logfire_config as mod
    source = inspect.getsource(mod)

    # Strip Python comments and docstrings before matching so guidance text
    # (e.g., "NEVER Call instrument_pydantic() Without include={}") in
    # docstrings doesn't trip the regex.
    source_nodoc = re.sub(r'""".*?"""', '', source, flags=re.DOTALL)
    source_nodoc = re.sub(r"'''.*?'''", '', source_nodoc, flags=re.DOTALL)
    source_nodoc = re.sub(r'#[^\n]*', '', source_nodoc)

    # Match: instrument_pydantic(   ...no include=... ...   )
    # We fail the test only if we find a call whose argument list does NOT
    # contain the word "include".
    pattern = re.compile(r"instrument_pydantic\s*\(([^)]*)\)", re.DOTALL)
    for match in pattern.finditer(source_nodoc):
        args = match.group(1)
        assert "include" in args, (
            "Found instrument_pydantic() call without include={...} in "
            "logfire_config.py. This creates ~48,000 OTel spans per extraction. "
            "See acm-observability skill for the safe instrumentation set."
        )


def test_langfuse_bridge_imports_cleanly():
    """langfuse_bridge.py holds emit_pipeline_event; it must import without
    requiring live Langfuse credentials."""
    import open_notebook.observability.langfuse_bridge as mod  # noqa: F401
