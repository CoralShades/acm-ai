"""
ConsensusEngine — per-field confidence-weighted voting.

Takes MatchGroups from RecordMatcher and produces ACMExtractionRecord objects
with consensus_metadata populated.

Story: E31-S3 Consensus Layer Core
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from loguru import logger

from open_notebook.extractors.acm_schemas import ACMExtractionRecord
from open_notebook.extractors.consensus.matcher import MatchGroup
from open_notebook.extractors.consensus.resolver import (
    ConflictResolver,
    FieldVoteResult,
)

# ---------------------------------------------------------------------------
# Fields subject to per-field voting.
# Metadata fields (extraction_confidence, data_issues, page_number,
# consensus_metadata) are deliberately excluded.
# ---------------------------------------------------------------------------

_VOTE_FIELDS: List[str] = [
    "building_id",
    "room_id",
    "product",
    "material_description",
    "result",
    "building_name",
    "building_year",
    "building_construction",
    "room_name",
    "room_area",
    "area_type",
    "extent",
    "location",
    "friable",
    "material_condition",
    "risk_status",
    "disturbance_potential",
    "sample_no",
    "sample_result",
    "no_access",
    "identifying_company",
    "quantity",
    "acm_labelled",
    "acm_label_details",
    "floor_level",
    "date_of_inspection",
    "hygienist_recommendations",
    "psb_supplied_acm_id",
    "removal_status",
    "date_of_removal",
    "quantity_removed",
    "removal_notification_no",
    "epa_certificate_no",
    "additional_comments",
]

# Key fields whose contestation triggers CONTESTED tier
_KEY_FIELDS = {"building_id", "product", "result"}


# ---------------------------------------------------------------------------
# Pure voting / tier helpers
# ---------------------------------------------------------------------------


def _vote_field(
    field_name: str,
    votes: Dict[str, Any],
    weights: Dict[str, float],
) -> FieldVoteResult:
    """Compute weighted majority vote for a single field.

    Steps:
    1. Group providers by their value (normalised to str().strip().lower() for
       comparison, but winner uses the original value from the first provider
       that supplied that normalised form).
    2. Sum weights per value group.
    3. Winner = group with highest total weight.
    4. score = winner_weight / total_weight.
    5. contested = score < 0.6.

    Args:
        field_name: Name of the field being voted on (used in error messages).
        votes: Mapping of provider_id -> raw field value. None values excluded.
        weights: Mapping of provider_id -> weight (default 1.0 if absent).

    Returns:
        FieldVoteResult with winner, score, contested flag, and original votes.

    Raises:
        ValueError: If votes is empty.
    """
    if not votes:
        raise ValueError(f"No votes provided for field '{field_name}'")

    # Accumulate weights per normalised value string
    value_weights: Dict[str, float] = {}  # normalised_value -> cumulative weight
    value_canonical: Dict[str, Any] = {}  # normalised_value -> original value (first seen)

    for provider_id, value in votes.items():
        if value is None:
            continue
        w = weights.get(provider_id, 1.0)
        norm = str(value).strip().lower()
        value_weights[norm] = value_weights.get(norm, 0.0) + w
        if norm not in value_canonical:
            value_canonical[norm] = value

    if not value_weights:
        # All providers returned None for this field
        return FieldVoteResult(
            winner=None,
            score=0.0,
            contested=False,
            votes=votes,
        )

    total_weight = sum(value_weights.values())
    winner_norm = max(value_weights, key=lambda k: value_weights[k])
    winner_score = value_weights[winner_norm] / total_weight if total_weight > 0 else 0.0

    return FieldVoteResult(
        winner=value_canonical[winner_norm],
        score=round(winner_score, 4),
        contested=winner_score < 0.6,
        votes=votes,
    )


def _assign_tier(
    field_votes: Dict[str, FieldVoteResult],
    group: MatchGroup,
) -> str:
    """Assign consensus tier based on agreement across non-None fields.

    Tiers (in priority order):
      CONTESTED — any key field (building_id, product, result) is contested
      HIGH      — all providers agree on all non-None fields (agreement_rate = 1.0)
      MEDIUM    — 2+ providers, agreement_rate >= 0.67
      LOW       — single provider OR agreement_rate < 0.67

    Args:
        field_votes: Dict of field_name -> FieldVoteResult.
        group: The MatchGroup being evaluated.

    Returns:
        One of "HIGH", "MEDIUM", "LOW", "CONTESTED".
    """
    # Single provider → LOW
    provider_ids = {r.provider_id for r in group.rows}
    if len(provider_ids) == 1:
        return "LOW"

    # Check for contested key fields → CONTESTED (highest priority)
    for key_field in _KEY_FIELDS:
        if key_field in field_votes and field_votes[key_field].contested:
            return "CONTESTED"

    # Compute agreement rate over all voted fields
    total_fields = len(field_votes)
    if total_fields == 0:
        return "LOW"

    agreed_fields = sum(1 for fv in field_votes.values() if not fv.contested)
    agreement_rate = agreed_fields / total_fields

    if agreement_rate >= 1.0:
        return "HIGH"
    elif agreement_rate >= 0.67:
        return "MEDIUM"
    else:
        return "LOW"


# ---------------------------------------------------------------------------
# ConsensusEngine
# ---------------------------------------------------------------------------


class ConsensusEngine:
    """Merges MatchGroups into ACMExtractionRecord objects with consensus_metadata.

    Usage:
        engine = ConsensusEngine()
        records = await engine.merge(
            groups,
            provider_weights={"docling": 1.0, "mineru": 1.0},
        )
    """

    def __init__(self, resolver: Optional[ConflictResolver] = None) -> None:
        self._resolver = resolver or ConflictResolver()

    async def merge(
        self,
        groups: List[MatchGroup],
        provider_weights: Optional[Dict[str, float]] = None,
    ) -> List[ACMExtractionRecord]:
        """Merge MatchGroups into final ACMExtractionRecord list.

        Args:
            groups: Output of RecordMatcher.match_groups().
            provider_weights: Per-provider field weights (default 1.0 for all).

        Returns:
            List of ACMExtractionRecord with consensus_metadata populated.
        """
        weights = provider_weights or {}
        results = []
        for group in groups:
            record = await self._merge_group(group, weights)
            results.append(record)
        return results

    async def _merge_group(
        self,
        group: MatchGroup,
        weights: Dict[str, float],
    ) -> ACMExtractionRecord:
        """Merge a MatchGroup into a single ACMExtractionRecord.

        Uses the highest-weight provider's record as the base template.
        Field-level voting then overwrites each field with the winner value.

        Args:
            group: The MatchGroup to merge.
            weights: Provider weights mapping.

        Returns:
            Merged ACMExtractionRecord with consensus_metadata populated.

        Raises:
            ValueError: If group has no rows.
        """
        if not group.rows:
            raise ValueError("Cannot merge an empty MatchGroup")

        # Use highest-weight provider's record as the base template
        def _row_weight(row):  # type: ignore[return]
            return weights.get(row.provider_id, 1.0)

        base_row = max(group.rows, key=_row_weight)
        base_record = base_row.record.model_copy(deep=True)

        field_votes: Dict[str, FieldVoteResult] = {}
        provider_ids = [r.provider_id for r in group.rows]

        for field_name in _VOTE_FIELDS:
            field_votes_for_field: Dict[str, Any] = {}
            for row in group.rows:
                val = getattr(row.record, field_name, None)
                if val is not None:
                    field_votes_for_field[row.provider_id] = val

            if not field_votes_for_field:
                continue  # All providers returned None — leave base value as-is

            if len(field_votes_for_field) == 1:
                # Only one provider has a value — accept without voting
                prov_id, value = next(iter(field_votes_for_field.items()))
                field_votes[field_name] = FieldVoteResult(
                    winner=value,
                    score=1.0,
                    contested=False,
                    votes=field_votes_for_field,
                )
            else:
                fv = _vote_field(field_name, field_votes_for_field, weights)
                field_votes[field_name] = fv

        # Resolve any contested fields through the ConflictResolver
        resolved_votes = await self._resolver.resolve(field_votes, group, weights)

        # Apply winner values to the base record
        for field_name, fv in resolved_votes.items():
            if fv.winner is not None:
                setattr(base_record, field_name, fv.winner)

        # Assign confidence tier
        tier = _assign_tier(resolved_votes, group)

        # Update extraction_confidence from tier
        tier_to_confidence = {
            "HIGH": "high",
            "MEDIUM": "medium",
            "LOW": "low",
            "CONTESTED": "low",
        }
        base_record.extraction_confidence = tier_to_confidence.get(tier, "low")

        # Derive group-level conflict_level and resolver_used from the per-field
        # FieldVoteResult objects instead of reading private resolver state.
        _level_order = {"none": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
        all_results = list(resolved_votes.values())
        conflict_level = max(
            (r.conflict_level for r in all_results if r.conflict_level),
            key=lambda x: _level_order.get(x, 0),
            default="none",
        )
        resolver_used = next(
            (
                r.resolver_used
                for r in all_results
                if r.conflict_level == conflict_level and r.resolver_used != "none"
            ),
            "none",
        )

        # Build consensus_metadata dict
        base_record.consensus_metadata = {
            "tier": tier,
            "providers": sorted(provider_ids),
            "match_method": group.match_method,
            "match_score": round(group.match_score, 4),
            "field_votes": {
                fn: {
                    "winner": fv.winner,
                    "score": fv.score,
                    "contested": fv.contested,
                    "votes": fv.votes,
                    "conflict_level": getattr(fv, "conflict_level", "none"),
                    "resolver_used": getattr(fv, "resolver_used", "none"),
                }
                for fn, fv in resolved_votes.items()
            },
            "conflict_level": conflict_level,
            "resolver_used": resolver_used,
        }

        logger.debug(
            f"ConsensusEngine: group tier={tier}, providers={provider_ids}, "
            f"match_method={group.match_method}, match_score={group.match_score:.3f}"
        )

        return base_record
