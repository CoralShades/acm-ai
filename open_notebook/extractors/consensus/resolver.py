"""
ConflictResolver — L1-L4 escalation chain for contested ACM field values.

L1: Weighted Majority (accept if winner score > 0.5 — clear majority, not a tie)
L2: Priority Hierarchy (docling > mineru > other)
L3: LLM Arbitration (async stub — returns L2 result, real call in E31-S5)
L4: Human Queue (confidence < 0.4, use L2 as provisional)

Story: E31-S3 Consensus Layer Core
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List

from loguru import logger

from open_notebook.extractors.consensus.matcher import MatchGroup


@dataclass
class FieldVoteResult:
    """
    Result of a per-field confidence-weighted vote.

    This is the canonical definition — imported by engine.py.

    Attributes:
        winner: The winning field value (or None if all providers returned None).
        score: Normalised weight of the winning value (0.0–1.0).
        contested: True when winner score < 0.6.
        votes: Mapping of provider_id → raw field value.
        conflict_level: Escalation level reached for this field ("L1"/"L2"/"L3"/"L4"/"none").
        resolver_used: Strategy name used to resolve the field.
    """

    winner: Any
    score: float
    contested: bool
    votes: Dict[str, Any]
    conflict_level: str = "none"
    resolver_used: str = "none"


# Provider priority for L2 resolution
PROVIDER_PRIORITY: List[str] = ["docling", "mineru"]


class ConflictResolver:
    """
    Resolves contested field votes via L1-L4 escalation.

    Each resolved FieldVoteResult carries conflict_level and resolver_used
    directly. ConsensusEngine derives group-level conflict metrics from those
    per-field results rather than reading internal resolver state.

    Attributes:
        PRIORITY_ORDER: Provider priority list for L2 resolution.
    """

    PRIORITY_ORDER: ClassVar[List[str]] = PROVIDER_PRIORITY

    async def resolve(
        self,
        field_votes: Dict[str, FieldVoteResult],
        group: MatchGroup,
        weights: Dict[str, float],
    ) -> Dict[str, FieldVoteResult]:
        """
        Resolve all contested fields in field_votes.

        Args:
            field_votes: Dict of field_name -> FieldVoteResult from ConsensusEngine.
            group: The MatchGroup being resolved (used for context).
            weights: Provider weights mapping provider_id -> float.

        Returns:
            Updated field_votes dict with contested fields resolved.
        """
        resolved = dict(field_votes)
        any_contested = any(fv.contested for fv in resolved.values())

        if not any_contested:
            return resolved

        for field_name, fv in list(resolved.items()):
            if not fv.contested:
                continue
            resolved[field_name] = await self._escalate(field_name, fv, weights)

        return resolved

    async def _escalate(
        self,
        field_name: str,
        fv: FieldVoteResult,
        weights: Dict[str, float],
    ) -> FieldVoteResult:
        """Run L1 through L4 escalation for a single contested field.

        Args:
            field_name: Name of the field being resolved.
            fv: The contested FieldVoteResult to resolve.
            weights: Provider weights.

        Returns:
            Resolved FieldVoteResult with conflict_level and resolver_used set.
        """
        # L1: Accept if clear majority (score > 0.5, not a true tie).
        # contested=True is set when score < 0.6 by _vote_field, so using
        # score >= 0.6 here was unreachable. score > 0.5 allows L1 to resolve
        # scores in the range (0.5, 0.6), escalating only true ties (score <= 0.5).
        if fv.score > 0.5:
            return FieldVoteResult(
                winner=fv.winner,
                score=fv.score,
                contested=False,
                votes=fv.votes,
                conflict_level="L1",
                resolver_used="weighted_majority",
            )

        # L2: Priority Hierarchy
        l2_result = self._l2_priority(fv, weights)
        if l2_result.score >= 0.4:
            return FieldVoteResult(
                winner=l2_result.winner,
                score=l2_result.score,
                contested=False,
                votes=fv.votes,
                conflict_level="L2",
                resolver_used="priority_hierarchy",
            )

        # L3: LLM Arbitration (stub — real implementation in E31-S5)
        l3_result = await self._l3_llm_stub(field_name, fv, l2_result)
        if l3_result.score >= 0.4:
            return FieldVoteResult(
                winner=l3_result.winner,
                score=l3_result.score,
                contested=False,
                votes=fv.votes,
                conflict_level="L3",
                resolver_used="llm_arbitration",
            )

        # L4: Human Queue
        logger.warning(
            f"ConflictResolver: field '{field_name}' escalated to L4 human queue. "
            f"Using L2 provisional result."
        )
        return FieldVoteResult(
            winner=l2_result.winner,
            score=l2_result.score,
            contested=True,  # Remains contested — flagged for human review
            votes=fv.votes,
            conflict_level="L4",
            resolver_used="human_queue",
        )

    def _l2_priority(
        self,
        fv: FieldVoteResult,
        weights: Dict[str, float],
    ) -> FieldVoteResult:
        """
        L2: Select the value from the highest-priority provider that has a vote.

        Priority order: docling > mineru > (other providers in alphabetical order).

        Args:
            fv: The contested FieldVoteResult.
            weights: Provider weights (not used for ordering, reserved for future).

        Returns:
            FieldVoteResult with the priority-selected winner.
        """
        priority_order = list(PROVIDER_PRIORITY)
        # Add any remaining providers alphabetically
        extra = sorted(p for p in fv.votes if p not in priority_order)
        priority_order.extend(extra)

        for provider_id in priority_order:
            if provider_id in fv.votes and fv.votes[provider_id] is not None:
                return FieldVoteResult(
                    winner=fv.votes[provider_id],
                    score=0.6,  # Provisional confidence from priority hierarchy
                    contested=False,
                    votes=fv.votes,
                    conflict_level="L2",
                    resolver_used="priority_hierarchy",
                )

        # Fallback: return original if no priority provider found
        return fv

    async def _l3_llm_stub(
        self,
        field_name: str,
        original: FieldVoteResult,
        l2_result: FieldVoteResult,
    ) -> FieldVoteResult:
        """
        L3: LLM Arbitration stub.

        In E31-S3, this returns the L2 result with a 0.5 confidence score.
        Real LLM arbitration is implemented in E31-S5.

        Args:
            field_name: Name of the field being arbitrated.
            original: The original contested FieldVoteResult.
            l2_result: The L2 priority-resolved result to use as the stub answer.

        Returns:
            FieldVoteResult with L2 winner and confidence=0.5.
        """
        logger.info(
            f"ConflictResolver: L3 stub called for field '{field_name}' "
            f"(real LLM arbitration deferred to E31-S5)"
        )
        return FieldVoteResult(
            winner=l2_result.winner,
            score=0.5,
            contested=False,
            votes=original.votes,
            conflict_level="L3",
            resolver_used="llm_arbitration",
        )
