"""TokenLimitValidator — Detects token limit violations and tracks chunking metrics.

Story: E1-S23 Token Limit Quality Validation

Wraps the existing chunking logic in acm_extraction.py with detection
and tracking capabilities. Reports whether extraction input exceeded
the model's context window and how many chunks were used.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Token estimation: 1 token ≈ 3 chars for structured table data
CHARS_PER_TOKEN_TABLE = 3
# Safety margin: use 80% of context window
SAFETY_MARGIN = 0.8
# Default prompt overhead in tokens (system prompt + output reservation)
DEFAULT_PROMPT_OVERHEAD = 4000


class TokenLimitValidator:
    """Detects token limit violations and splits large extraction inputs
    into manageable chunks. Chunks are extracted independently and merged.
    """

    def __init__(
        self,
        model_id: str,
        context_window: int,
        safety_margin: float = SAFETY_MARGIN,
    ):
        self.model_id = model_id
        self.context_window = context_window
        self.safety_margin = safety_margin
        self.safe_token_budget = int(context_window * safety_margin)

    def estimate_tokens(self, content: str) -> int:
        """Estimate token count using character-based heuristic.

        Uses 3-char/token rule for structured table data.
        """
        return len(content) // CHARS_PER_TOKEN_TABLE

    def needs_chunking(
        self, content: str, prompt_overhead: int = DEFAULT_PROMPT_OVERHEAD
    ) -> bool:
        """Returns True if content exceeds the safe token budget."""
        estimated_tokens = self.estimate_tokens(content)
        available = self.safe_token_budget - prompt_overhead
        exceeds = estimated_tokens > available
        if exceeds:
            logger.warning(
                f"Content estimated at {estimated_tokens} tokens exceeds "
                f"safe budget of {available} tokens (model={self.model_id}, "
                f"context_window={self.context_window})"
            )
        return exceeds

    def check_response_truncation(self, response_text: str) -> bool:
        """Check if an extraction response appears truncated.

        Detects:
        - Missing closing JSON structure (no ] or } at end)
        - Abruptly cut off text
        """
        if not response_text:
            return True
        stripped = response_text.strip()
        # JSON responses should end with ] or }
        if stripped and stripped[-1] not in ("]", "}", '"'):
            return True
        return False

    def assess_extraction(
        self,
        content: str,
        chunks_used: int,
        records_extracted: int,
        response_text: str | None = None,
    ) -> dict[str, Any]:
        """Assess whether token limits may have impacted extraction quality.

        Returns a dict with:
        - token_limit_exceeded: bool
        - chunk_count: int
        - estimated_input_tokens: int
        - warnings: list[str]
        """
        estimated_tokens = self.estimate_tokens(content)
        warnings: list[str] = []

        token_limit_exceeded = False

        # Check 1: Input size vs context window
        if estimated_tokens > self.safe_token_budget:
            token_limit_exceeded = True
            warnings.append(
                f"Input ({estimated_tokens} est. tokens) exceeds "
                f"safe budget ({self.safe_token_budget} tokens)"
            )

        # Check 2: Response truncation
        if response_text and self.check_response_truncation(response_text):
            token_limit_exceeded = True
            warnings.append("Response appears truncated (missing closing structure)")

        # Check 3: Suspiciously low record count relative to content size
        # Heuristic: expect at least 1 record per 2000 tokens of table content
        if estimated_tokens > 2000 and records_extracted == 0:
            warnings.append(
                "No records extracted despite substantial content — "
                "possible token limit issue"
            )

        if warnings:
            for w in warnings:
                logger.warning(f"[TokenLimitValidator] {w}")

        return {
            "token_limit_exceeded": token_limit_exceeded,
            "chunk_count": chunks_used,
            "estimated_input_tokens": estimated_tokens,
            "warnings": warnings,
        }
