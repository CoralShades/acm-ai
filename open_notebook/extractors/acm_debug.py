"""
ACM Extraction Debug Configuration

This module provides toggleable debug settings for ACM extraction.
All debug flags can be controlled from this single file.
"""

import os
from dataclasses import dataclass
from typing import Optional

from loguru import logger


@dataclass
class ACMDebugConfig:
    """Debug configuration for ACM extraction."""

    # Master debug switch - set to True to enable all debug logging
    DEBUG_ENABLED: bool = True

    # Individual debug flags (only apply when DEBUG_ENABLED is True)
    LOG_PROMPT_CONTENT: bool = True       # Log the full prompt sent to LLM
    LOG_RAW_CONTENT: bool = True          # Log raw source content before processing
    LOG_CHUNK_DETAILS: bool = True        # Log chunk boundaries and sizes
    LOG_LLM_RESPONSE: bool = True         # Log raw LLM response before parsing
    LOG_EXTRACTION_STATS: bool = True     # Log extraction statistics
    LOG_VALIDATION_DETAILS: bool = True   # Log validation steps

    # File output settings
    DUMP_PROMPTS_TO_FILE: bool = True     # Dump prompts to files for inspection
    PROMPT_DUMP_DIR: str = "_debug/acm_prompts"

    # Content preview settings
    MAX_CONTENT_PREVIEW: int = 2000       # Characters to show in previews
    MAX_PROMPT_PREVIEW: int = 5000        # Characters to show for prompt previews

    @classmethod
    def from_env(cls) -> "ACMDebugConfig":
        """Create config from environment variables."""
        return cls(
            DEBUG_ENABLED=os.getenv("ACM_DEBUG", "1").lower() in ("1", "true", "yes"),
            LOG_PROMPT_CONTENT=os.getenv("ACM_DEBUG_PROMPT", "1").lower() in ("1", "true", "yes"),
            LOG_RAW_CONTENT=os.getenv("ACM_DEBUG_RAW", "1").lower() in ("1", "true", "yes"),
            DUMP_PROMPTS_TO_FILE=os.getenv("ACM_DEBUG_DUMP", "1").lower() in ("1", "true", "yes"),
        )


# Global debug config instance
debug_config = ACMDebugConfig.from_env()


def acm_debug(message: str, level: str = "debug") -> None:
    """Log a debug message if debug is enabled."""
    if not debug_config.DEBUG_ENABLED:
        return

    log_func = getattr(logger, level, logger.debug)
    log_func(f"[ACM-DEBUG] {message}")


def dump_prompt_to_file(prompt: str, source_id: str, chunk_index: int = 0) -> Optional[str]:
    """Dump prompt content to file for inspection."""
    if not debug_config.DEBUG_ENABLED or not debug_config.DUMP_PROMPTS_TO_FILE:
        return None

    import datetime

    dump_dir = debug_config.PROMPT_DUMP_DIR
    os.makedirs(dump_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Clean source_id for filename
    clean_source_id = source_id.replace(":", "_").replace("/", "_")
    filename = f"{dump_dir}/prompt_{clean_source_id}_chunk{chunk_index}_{timestamp}.txt"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# ACM Extraction Prompt Debug Dump\n")
            f.write(f"# Source: {source_id}\n")
            f.write(f"# Chunk: {chunk_index}\n")
            f.write(f"# Time: {timestamp}\n")
            f.write(f"# Length: {len(prompt)} chars\n")
            f.write("#" + "=" * 60 + "\n\n")
            f.write(prompt)

        acm_debug(f"Prompt dumped to: {filename}")
        return filename
    except Exception as e:
        logger.warning(f"Failed to dump prompt to file: {e}")
        return None


def dump_content_to_file(content: str, source_id: str, label: str = "content") -> Optional[str]:
    """Dump content to file for inspection."""
    if not debug_config.DEBUG_ENABLED or not debug_config.DUMP_PROMPTS_TO_FILE:
        return None

    import datetime

    dump_dir = debug_config.PROMPT_DUMP_DIR
    os.makedirs(dump_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_source_id = source_id.replace(":", "_").replace("/", "_")
    filename = f"{dump_dir}/{label}_{clean_source_id}_{timestamp}.txt"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {label.upper()} Debug Dump\n")
            f.write(f"# Source: {source_id}\n")
            f.write(f"# Length: {len(content)} chars\n")
            f.write("#" + "=" * 60 + "\n\n")
            f.write(content)

        acm_debug(f"{label} dumped to: {filename}")
        return filename
    except Exception as e:
        logger.warning(f"Failed to dump {label} to file: {e}")
        return None


def log_extraction_preview(content: str, source_id: str) -> None:
    """Log a preview of content being extracted."""
    if not debug_config.DEBUG_ENABLED or not debug_config.LOG_RAW_CONTENT:
        return

    preview_len = debug_config.MAX_CONTENT_PREVIEW
    acm_debug(f"Content preview for {source_id}:")
    acm_debug(f"Total length: {len(content)} chars")

    # Find and show ACM-relevant patterns
    acm_patterns = [
        "Asbestos-containing",
        "No Asbestos",
        "Non Friable",
        "Friable",
        "Floor Coverings",
        "Vinyl Tiles",
        "Detected",
    ]

    for pattern in acm_patterns:
        count = content.count(pattern)
        if count > 0:
            acm_debug(f"  Pattern '{pattern}': {count} occurrences")


def log_prompt_preview(prompt: str, source_id: str) -> None:
    """Log a preview of the prompt being sent."""
    if not debug_config.DEBUG_ENABLED or not debug_config.LOG_PROMPT_CONTENT:
        return

    preview_len = debug_config.MAX_PROMPT_PREVIEW
    acm_debug(f"Prompt for {source_id}:")
    acm_debug(f"Total prompt length: {len(prompt)} chars")
    acm_debug(f"First {preview_len} chars:\n{prompt[:preview_len]}")
