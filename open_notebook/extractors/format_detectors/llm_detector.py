"""LLM-based format auto-detection.

Runs in parallel with heuristic detectors when enabled via
ACM_LLM_FORMAT_DETECT=true environment variable. Proposes a
format configuration for human review.

Gated by env var because Ollama is single-threaded and concurrent
LLM calls would block the pipeline.
"""

import os
from typing import Any, Dict, Optional

from loguru import logger


async def detect_format_with_llm(
    content: str,
    model_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Use LLM to detect document format and propose column mapping.

    Returns proposed format config:
        {
            "format_name": str,
            "detection_patterns": list[str],
            "column_mapping_hint": dict[str, str],
        }

    Returns None if:
    - Feature is disabled (ACM_LLM_FORMAT_DETECT != true)
    - LLM call fails
    - No format detected
    """
    if os.getenv("ACM_LLM_FORMAT_DETECT", "false").lower() != "true":
        return None

    try:
        from ai_prompter import Prompter
        from langchain_core.messages import HumanMessage, SystemMessage

        from open_notebook.graphs.utils import (
            _apply_ollama_extraction_settings,
            parse_json_response,
            provision_langchain_model,
        )

        # Use only first 5000 chars for format detection (fast)
        sample = content[:5000]

        system_prompt = (
            "You are a document format classifier for ACM (Asbestos Containing Material) registers. "
            "Analyze the document sample and identify the consultant format.\n\n"
            "Known formats:\n"
            "- 'samp': NSW DoE School Asbestos Management Plan (uses ## B00A - Building headers)\n"
            "- 'clutch': Clutch/Greencap registers (pipe-delimited tables with | Building Name: |)\n"
            "- 'ara': Greencap/Prensa ARA format (Building Name: text headers)\n"
            "- 'unknown': Format not recognized\n\n"
            'Return JSON: {"format_name": "...", "detection_patterns": ["pattern1", ...], '
            '"column_mapping_hint": {"DocumentColumn": "canonical_field", ...}}'
        )

        model = await provision_langchain_model(
            sample, model_id, "extraction", temperature=0.0, max_tokens=1024
        )
        _apply_ollama_extraction_settings(model)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"## Document Sample\n\n{sample}"),
        ]

        raw_response = await model.ainvoke(messages)
        response_text = (
            raw_response.content
            if hasattr(raw_response, "content")
            else str(raw_response)
        )
        parsed = parse_json_response(response_text)

        if parsed.get("format_name") and parsed["format_name"] != "unknown":
            logger.info(
                f"LLM format detection: {parsed['format_name']} "
                f"(patterns: {parsed.get('detection_patterns', [])})"
            )
            return parsed

        return None

    except Exception as e:
        logger.warning(f"LLM format detection failed: {e}")
        return None
