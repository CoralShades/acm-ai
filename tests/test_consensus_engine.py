"""
Unit tests for ConsensusEngine, ConflictResolver, and supporting helpers (E31-S3).

Tests cover:
- _vote_field() per-field weighted majority voting
- _assign_tier() confidence tier assignment
- ConsensusEngine.merge() integration
- ConflictResolver L1-L4 escalation chain

Story: E31-S3 Consensus Layer Core
"""

import asyncio
from typing import Any, Dict

import pytest

from open_notebook.extractors.acm_schemas import ACMExtractionRecord
from open_notebook.extractors.consensus.engine import (
    ConsensusEngine,
    _assign_tier,
    _vote_field,
)
from open_notebook.extractors.consensus.matcher import CandidateRow, MatchGroup
from open_notebook.extractors.consensus.resolver import (
    ConflictResolver,
    FieldVoteResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_record(**kwargs) -> ACMExtractionRecord:
    """Create a minimal valid ACMExtractionRecord for testing."""
    defaults = {
        "building_id": "B1",
        "product": "Ceiling Tiles",
        "result": "Positive",
    }
    defaults.update(kwargs)
    return ACMExtractionRecord(**defaults)


def make_candidate(
    provider_id: str = "docling",
    row_index: int = 0,
    **record_kwargs,
) -> CandidateRow:
    """Create a CandidateRow for testing."""
    return CandidateRow(
        provider_id=provider_id,
        record=make_record(**record_kwargs),
        row_index=row_index,
    )


def make_group(
    candidates: list,
    method: str = "key_field_anchor",
    score: float = 1.0,
) -> MatchGroup:
    """Create a MatchGroup for testing."""
    return MatchGroup(rows=list(candidates), match_method=method, match_score=score)


def make_fvr(
    winner: Any = "Positive",
    score: float = 1.0,
    contested: bool = False,
    votes: Dict[str, Any] = None,
) -> FieldVoteResult:
    """Create a FieldVoteResult for testing."""
    return FieldVoteResult(
        winner=winner,
        score=score,
        contested=contested,
        votes=votes or {"docling": winner},
    )


def run_async(coro):
    """Run an async coroutine in a test."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# _vote_field() tests
# ---------------------------------------------------------------------------


class TestVoteField:
    """Tests for _vote_field() per-field voting."""

    def test_vote_field_unanimous_returns_score_1(self):
        """Both providers return 'Positive' → score=1.0, contested=False."""
        votes = {"docling": "Positive", "mineru": "Positive"}
        result = _vote_field("result", votes, {})
        assert result.winner == "Positive"
        assert result.score == 1.0
        assert result.contested is False

    def test_vote_field_majority_wins(self):
        """2 providers say 'Positive', 1 says 'Negative' → winner='Positive', score~0.67."""
        votes = {"docling": "Positive", "mineru": "Positive", "third": "Negative"}
        result = _vote_field("result", votes, {})
        assert result.winner == "Positive"
        assert result.score == pytest.approx(2 / 3, abs=0.001)
        assert result.contested is False  # 0.67 >= 0.6

    def test_vote_field_contested_when_winner_score_below_0_6(self):
        """50/50 split → contested=True (score=0.5 < 0.6)."""
        votes = {"docling": "Positive", "mineru": "Negative"}
        result = _vote_field("result", votes, {})
        assert result.contested is True
        assert result.score == 0.5

    def test_vote_field_single_provider_score_1(self):
        """Single provider vote → score=1.0, contested=False."""
        votes = {"docling": "Negative"}
        result = _vote_field("result", votes, {})
        assert result.winner == "Negative"
        assert result.score == 1.0
        assert result.contested is False

    def test_vote_field_respects_weights(self):
        """docling weight=2.0, mineru weight=1.0, docling='Positive', mineru='Negative' → winner='Positive', score=0.67."""
        votes = {"docling": "Positive", "mineru": "Negative"}
        weights = {"docling": 2.0, "mineru": 1.0}
        result = _vote_field("result", votes, weights)
        assert result.winner == "Positive"
        # docling weight 2.0, total weight 3.0 → score = 2/3
        assert result.score == pytest.approx(2 / 3, abs=0.001)
        assert result.contested is False  # 0.67 >= 0.6

    def test_vote_field_all_none_returns_none_winner(self):
        """All providers return None for a field → winner=None."""
        votes = {"docling": None, "mineru": None}
        result = _vote_field("result", votes, {})
        assert result.winner is None

    def test_vote_field_empty_votes_raises(self):
        """Empty votes dict raises ValueError."""
        with pytest.raises(ValueError, match="No votes provided"):
            _vote_field("result", {}, {})

    def test_vote_field_case_insensitive_grouping(self):
        """Values are normalised to lowercase for grouping; winner uses original casing."""
        votes = {"docling": "Positive", "mineru": "positive"}
        result = _vote_field("result", votes, {})
        # Both vote for the same value (case-insensitively)
        assert result.score == 1.0
        assert result.contested is False
        # Winner is the canonical form (first seen — "Positive")
        assert result.winner.lower() == "positive"

    def test_vote_field_votes_preserved_in_result(self):
        """The original votes dict is preserved in the result."""
        votes = {"docling": "Positive", "mineru": "Negative"}
        result = _vote_field("result", votes, {})
        assert result.votes == votes


# ---------------------------------------------------------------------------
# _assign_tier() tests
# ---------------------------------------------------------------------------


class TestAssignTier:
    """Tests for _assign_tier() confidence tier assignment."""

    def test_tier_low_single_provider(self):
        """Single-provider MatchGroup → 'LOW'."""
        row = make_candidate(provider_id="docling")
        group = make_group([row])
        field_votes = {"result": make_fvr("Positive", 1.0, False)}
        assert _assign_tier(field_votes, group) == "LOW"

    def test_tier_high_all_agree(self):
        """Multi-provider, all fields agree (all scores == 1.0) → 'HIGH'."""
        row_a = make_candidate(provider_id="docling")
        row_b = make_candidate(provider_id="mineru")
        group = make_group([row_a, row_b])
        field_votes = {
            "result": make_fvr("Positive", 1.0, False),
            "building_id": make_fvr("B1", 1.0, False),
            "product": make_fvr("Ceiling Tiles", 1.0, False),
        }
        assert _assign_tier(field_votes, group) == "HIGH"

    def test_tier_medium_majority_agree(self):
        """Multi-provider, 3/4 fields agree → 'MEDIUM' (agreement_rate=0.75 >= 0.67)."""
        row_a = make_candidate(provider_id="docling")
        row_b = make_candidate(provider_id="mineru")
        group = make_group([row_a, row_b])
        field_votes = {
            "result": make_fvr(
                "Positive", 1.0, False, {"docling": "Positive", "mineru": "Positive"}
            ),
            "building_id": make_fvr(
                "B1", 1.0, False, {"docling": "B1", "mineru": "B1"}
            ),
            "product": make_fvr(
                "Ceiling Tiles",
                1.0,
                False,
                {"docling": "Ceiling Tiles", "mineru": "Ceiling Tiles"},
            ),
            # Fourth field disagrees — but NOT a key field (room_name)
            "room_name": make_fvr(
                "Classroom", 0.5, True, {"docling": "Classroom", "mineru": "Office"}
            ),
        }
        # 3/4 = 0.75 >= 0.67 → MEDIUM (and none of the key fields are contested)
        assert _assign_tier(field_votes, group) == "MEDIUM"

    def test_tier_low_poor_agreement(self):
        """Multi-provider, agreement_rate < 0.67 → 'LOW' (uses only non-key contested fields)."""
        row_a = make_candidate(provider_id="docling")
        row_b = make_candidate(provider_id="mineru")
        group = make_group([row_a, row_b])
        # 1 out of 4 fields agrees; contested fields are non-key fields only
        # so CONTESTED is not triggered
        field_votes = {
            "result": make_fvr(
                "Positive", 1.0, False
            ),  # agrees (key field, not contested)
            "room_name": make_fvr("Classroom", 0.5, True),  # contested non-key
            "location": make_fvr("Ceiling", 0.5, True),  # contested non-key
            "extent": make_fvr("Whole room", 0.5, True),  # contested non-key
        }
        # 1/4 = 0.25 < 0.67 and no key fields are contested → LOW
        assert _assign_tier(field_votes, group) == "LOW"

    def test_tier_contested_key_field_contested(self):
        """'result' field is contested → 'CONTESTED'."""
        row_a = make_candidate(provider_id="docling")
        row_b = make_candidate(provider_id="mineru")
        group = make_group([row_a, row_b])
        field_votes = {
            "result": make_fvr("Positive", 0.5, True),  # contested
            "building_id": make_fvr("B1", 1.0, False),
        }
        assert _assign_tier(field_votes, group) == "CONTESTED"

    def test_tier_contested_building_id_contested(self):
        """'building_id' field is contested → 'CONTESTED'."""
        row_a = make_candidate(provider_id="docling")
        row_b = make_candidate(provider_id="mineru")
        group = make_group([row_a, row_b])
        field_votes = {
            "building_id": make_fvr("B1", 0.5, True),  # contested key field
            "result": make_fvr("Positive", 1.0, False),
        }
        assert _assign_tier(field_votes, group) == "CONTESTED"

    def test_tier_contested_product_contested(self):
        """'product' field is contested → 'CONTESTED'."""
        row_a = make_candidate(provider_id="docling")
        row_b = make_candidate(provider_id="mineru")
        group = make_group([row_a, row_b])
        field_votes = {
            "product": make_fvr("Ceiling Tiles", 0.5, True),  # contested key field
            "result": make_fvr("Positive", 1.0, False),
        }
        assert _assign_tier(field_votes, group) == "CONTESTED"

    def test_tier_empty_field_votes_single_provider_is_low(self):
        """Empty field_votes with single provider → 'LOW'."""
        row = make_candidate(provider_id="docling")
        group = make_group([row])
        assert _assign_tier({}, group) == "LOW"

    def test_tier_empty_field_votes_multi_provider_is_low(self):
        """Empty field_votes with multiple providers → 'LOW'."""
        row_a = make_candidate(provider_id="docling")
        row_b = make_candidate(provider_id="mineru")
        group = make_group([row_a, row_b])
        assert _assign_tier({}, group) == "LOW"


# ---------------------------------------------------------------------------
# ConsensusEngine.merge() integration tests
# ---------------------------------------------------------------------------


class TestConsensusEngineMerge:
    """Integration tests for ConsensusEngine.merge()."""

    def test_merge_empty_groups_returns_empty_list(self):
        """merge([]) returns []."""
        engine = ConsensusEngine()
        result = run_async(engine.merge([]))
        assert result == []

    def test_merge_single_group_single_provider(self):
        """Single MatchGroup with 1 row → returns record with tier='LOW', consensus_metadata set."""
        record = make_record(building_id="B1", product="Ceiling Tiles")
        row = make_candidate(provider_id="docling")
        row.record = record
        group = make_group([row], method="single_provider", score=1.0)

        engine = ConsensusEngine()
        result = run_async(engine.merge([group]))

        assert len(result) == 1
        merged = result[0]
        assert merged.consensus_metadata is not None
        assert merged.consensus_metadata["tier"] == "LOW"
        assert merged.extraction_confidence == "low"

    def test_merge_two_providers_agree(self):
        """Two providers agree on all fields → tier='HIGH'."""
        record_a = make_record(
            building_id="B1",
            product="Ceiling Tiles",
            result="Positive",
            room_id="R101",
        )
        record_b = make_record(
            building_id="B1",
            product="Ceiling Tiles",
            result="Positive",
            room_id="R101",
        )
        row_a = CandidateRow(provider_id="docling", record=record_a, row_index=0)
        row_b = CandidateRow(provider_id="mineru", record=record_b, row_index=0)
        group = make_group([row_a, row_b], method="key_field_anchor", score=1.0)

        engine = ConsensusEngine()
        result = run_async(engine.merge([group]))

        assert len(result) == 1
        merged = result[0]
        assert merged.consensus_metadata["tier"] == "HIGH"
        assert merged.extraction_confidence == "high"

    def test_merge_two_providers_disagree_key_field(self):
        """Providers disagree on 'result' — ConflictResolver resolves via L2 (priority hierarchy).

        After the ConflictResolver runs, the contested field is resolved (docling wins via L2),
        so the final tier reflects the post-resolution state. Since all fields are resolved
        (no remaining contested fields after L2), tier depends on agreement_rate.
        The consensus_metadata conflict_level shows the highest escalation reached (L2).
        """
        record_a = make_record(
            building_id="B1", product="Ceiling Tiles", result="Positive"
        )
        record_b = make_record(
            building_id="B1", product="Ceiling Tiles", result="Negative"
        )
        row_a = CandidateRow(provider_id="docling", record=record_a, row_index=0)
        row_b = CandidateRow(provider_id="mineru", record=record_b, row_index=0)
        group = make_group([row_a, row_b], method="key_field_anchor", score=1.0)

        engine = ConsensusEngine()
        result = run_async(engine.merge([group]))

        assert len(result) == 1
        merged = result[0]
        # After L2 resolution, conflict_level reflects the escalation that occurred
        assert merged.consensus_metadata["conflict_level"] == "L2"
        # The resolver_used reflects L2 priority hierarchy
        assert merged.consensus_metadata["resolver_used"] == "priority_hierarchy"
        # extraction_confidence is updated from the resolved tier
        assert merged.extraction_confidence in ("high", "medium", "low")

    def test_merge_sets_extraction_confidence(self):
        """extraction_confidence is updated from tier (HIGH→'high', etc.)."""
        # HIGH case
        record_a = make_record(
            building_id="B1", product="Ceiling Tiles", result="Positive"
        )
        record_b = make_record(
            building_id="B1", product="Ceiling Tiles", result="Positive"
        )
        row_a = CandidateRow(provider_id="docling", record=record_a, row_index=0)
        row_b = CandidateRow(provider_id="mineru", record=record_b, row_index=0)
        group = make_group([row_a, row_b])

        engine = ConsensusEngine()
        result = run_async(engine.merge([group]))
        assert result[0].extraction_confidence == "high"

    def test_merge_consensus_metadata_schema(self):
        """consensus_metadata has all required keys."""
        row = make_candidate(provider_id="docling")
        group = make_group([row], method="single_provider", score=1.0)

        engine = ConsensusEngine()
        result = run_async(engine.merge([group]))

        meta = result[0].consensus_metadata
        required_keys = {
            "tier",
            "providers",
            "match_method",
            "match_score",
            "field_votes",
            "conflict_level",
            "resolver_used",
        }
        assert required_keys.issubset(set(meta.keys())), (
            f"Missing keys: {required_keys - set(meta.keys())}"
        )

    def test_merge_providers_list_sorted(self):
        """consensus_metadata['providers'] is always sorted."""
        record_a = make_record()
        record_b = make_record()
        row_a = CandidateRow(provider_id="mineru", record=record_a, row_index=0)
        row_b = CandidateRow(provider_id="docling", record=record_b, row_index=0)
        group = make_group([row_a, row_b])

        engine = ConsensusEngine()
        result = run_async(engine.merge([group]))

        providers = result[0].consensus_metadata["providers"]
        assert providers == sorted(providers)

    def test_merge_match_method_and_score_preserved(self):
        """match_method and match_score from the MatchGroup are in consensus_metadata."""
        row = make_candidate()
        group = make_group([row], method="jaro_winkler", score=0.87)

        engine = ConsensusEngine()
        result = run_async(engine.merge([group]))

        meta = result[0].consensus_metadata
        assert meta["match_method"] == "jaro_winkler"
        assert meta["match_score"] == pytest.approx(0.87, abs=0.0001)

    def test_merge_multiple_groups_returns_multiple_records(self):
        """Three groups → three merged records."""
        groups = [
            make_group([make_candidate(provider_id="docling")]),
            make_group([make_candidate(provider_id="docling", row_index=1)]),
            make_group([make_candidate(provider_id="docling", row_index=2)]),
        ]
        engine = ConsensusEngine()
        result = run_async(engine.merge(groups))
        assert len(result) == 3

    def test_merge_winner_value_applied_to_base_record(self):
        """When two providers agree on a non-default field, the winner is applied."""
        record_a = make_record(location="Ceiling")
        record_b = make_record(location="Ceiling")
        row_a = CandidateRow(provider_id="docling", record=record_a, row_index=0)
        row_b = CandidateRow(provider_id="mineru", record=record_b, row_index=0)
        group = make_group([row_a, row_b])

        engine = ConsensusEngine()
        result = run_async(engine.merge([group]))

        assert result[0].location == "Ceiling"


# ---------------------------------------------------------------------------
# ConflictResolver tests
# ---------------------------------------------------------------------------


class TestConflictResolver:
    """Tests for ConflictResolver L1-L4 escalation chain."""

    def _make_resolver(self) -> ConflictResolver:
        return ConflictResolver()

    def test_no_contested_fields_returns_unchanged(self):
        """No contested fields → resolve() returns field_votes unchanged, conflict_level='none'."""
        resolver = self._make_resolver()
        field_votes = {
            "result": FieldVoteResult(
                winner="Positive",
                score=1.0,
                contested=False,
                votes={"docling": "Positive"},
            ),
        }
        # Make a minimal group
        group = make_group([make_candidate()])
        resolved = run_async(resolver.resolve(field_votes, group, {}))

        assert resolved["result"].winner == "Positive"
        # Non-contested fields are not processed — conflict_level remains 'none'
        assert resolved["result"].conflict_level == "none"
        assert resolved["result"].resolver_used == "none"

    def test_l1_accepts_winner_score_in_range_0_5_to_0_6(self):
        """Field with score=0.55 (contested=True, score in (0.5, 0.6)) → L1 accepts.

        This is the actual production case: _vote_field marks contested=True when
        score < 0.6, so the range (0.5, 0.6) is the only range that is both contested
        AND resolvable by L1 (score > 0.5). Using score=0.55 exercises this path.
        """
        resolver = self._make_resolver()
        fvr = FieldVoteResult(
            winner="Positive",
            score=0.55,  # contested=True from _vote_field (< 0.6), L1 accepts (> 0.5)
            contested=True,
            votes={"docling": "Positive", "mineru": "Negative"},
        )
        field_votes = {"result": fvr}
        group = make_group(
            [
                make_candidate(provider_id="docling"),
                make_candidate(provider_id="mineru"),
            ]
        )
        resolved = run_async(resolver.resolve(field_votes, group, {}))

        assert resolved["result"].winner == "Positive"
        assert resolved["result"].contested is False
        assert resolved["result"].conflict_level == "L1"
        assert resolved["result"].resolver_used == "weighted_majority"

    def test_l2_priority_docling_over_mineru(self):
        """Docling and MinerU disagree, score < 0.6 → L2 picks docling value."""
        resolver = self._make_resolver()
        fvr = FieldVoteResult(
            winner="Positive",
            score=0.5,  # < 0.6 → goes to L2
            contested=True,
            votes={"docling": "Positive", "mineru": "Negative"},
        )
        field_votes = {"result": fvr}
        group = make_group(
            [
                make_candidate(provider_id="docling"),
                make_candidate(provider_id="mineru"),
            ]
        )
        resolved = run_async(resolver.resolve(field_votes, group, {}))

        # L2 should pick docling (higher priority)
        assert resolved["result"].winner == "Positive"
        assert resolved["result"].conflict_level == "L2"

    def test_l2_priority_unknown_provider_last(self):
        """Unknown provider loses to docling/mineru in priority."""
        resolver = self._make_resolver()
        fvr = FieldVoteResult(
            winner="Negative",  # winner from voting, but contested
            score=0.5,
            contested=True,
            votes={"docling": "Positive", "unknown_provider": "Negative"},
        )
        field_votes = {"result": fvr}
        group = make_group(
            [
                make_candidate(provider_id="docling"),
                make_candidate(provider_id="unknown_provider"),
            ]
        )
        resolved = run_async(resolver.resolve(field_votes, group, {}))

        # L2: docling wins over unknown_provider
        assert resolved["result"].winner == "Positive"

    def test_l3_stub_returns_l2_result_with_0_5_confidence(self):
        """L3 stub is called when L2 gives score=0.6 but we force a stub path."""
        # To reach L3, L2 result must have score < 0.4
        # We simulate by patching L2 behavior — but since L2 always returns 0.6,
        # we test the stub directly
        resolver = self._make_resolver()

        original = FieldVoteResult(
            winner="Positive",
            score=0.3,
            contested=True,
            votes={"docling": "Positive", "mineru": "Negative"},
        )
        l2_result = FieldVoteResult(
            winner="Positive",
            score=0.3,  # < 0.4 to force L3
            contested=False,
            votes={"docling": "Positive", "mineru": "Negative"},
        )

        l3_result = run_async(resolver._l3_llm_stub("result", original, l2_result))
        assert l3_result.winner == "Positive"
        assert l3_result.score == 0.5
        assert l3_result.contested is False
        assert l3_result.conflict_level == "L3"
        assert l3_result.resolver_used == "llm_arbitration"

    def test_l4_human_queue_sets_contested_true(self):
        """L4 leaves contested=True. Reached by mocking both L2 fallback and L3 to return low scores.

        In E31-S3, the L3 stub always returns 0.5 and L2 always returns 0.6 when any provider
        has a value — so reaching L4 requires all providers to have None values (L2 falls back
        to the original fvr) AND L3 to be mocked. We mock both to force L4.
        """
        from unittest.mock import patch

        resolver = self._make_resolver()

        # A contested field where ALL provider votes are None → L2 returns the original fvr
        # The original fvr has score=0.0 < 0.4 → L2 gate fails → goes to L3
        fvr = FieldVoteResult(
            winner=None,
            score=0.0,  # < 0.6 → escalates; L2 will fall back to this since votes are None
            contested=True,
            votes={"unknown_a": None, "unknown_b": None},
        )

        async def mock_l3_stub(field_name, original, l2_result):
            # Return low confidence to force L4
            return FieldVoteResult(
                winner=l2_result.winner,
                score=0.3,  # < 0.4 → forces L4
                contested=False,
                votes=original.votes,
                conflict_level="L3",
                resolver_used="llm_arbitration",
            )

        with patch.object(resolver, "_l3_llm_stub", mock_l3_stub):
            field_votes = {"some_field": fvr}
            group = make_group(
                [
                    make_candidate(provider_id="unknown_a"),
                    make_candidate(provider_id="unknown_b"),
                ]
            )
            resolved = run_async(resolver.resolve(field_votes, group, {}))

        # L4 was reached — result should remain contested (flagged for human review)
        assert resolved["some_field"].conflict_level == "L4"
        assert resolved["some_field"].resolver_used == "human_queue"
        assert resolved["some_field"].contested is True

    def test_resolver_tracks_highest_escalation_level(self):
        """If L1 resolves field A and L2 resolves field B, highest conflict_level across fields is 'L2'."""
        resolver = self._make_resolver()

        field_votes = {
            # score=0.55 → L1 accepts (score > 0.5, contested=True from _vote_field)
            "result": FieldVoteResult(
                winner="Positive",
                score=0.55,
                contested=True,
                votes={"docling": "Positive", "mineru": "Negative"},
            ),
            # score=0.5 → L2 (score == 0.5 is a tie, not > 0.5, so L1 does not accept)
            "building_id": FieldVoteResult(
                winner="B1",
                score=0.5,
                contested=True,
                votes={"docling": "B1", "mineru": "B2"},
            ),
        }
        group = make_group(
            [
                make_candidate(provider_id="docling"),
                make_candidate(provider_id="mineru"),
            ]
        )
        resolved = run_async(resolver.resolve(field_votes, group, {}))

        # L2 is the highest level reached across all fields
        _level_order = {"none": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
        highest = max(
            resolved.values(),
            key=lambda fv: _level_order.get(fv.conflict_level, 0),
        )
        assert highest.conflict_level == "L2"

    def test_resolver_l2_priority_hierarchy_result(self):
        """L2 resolver_used is 'priority_hierarchy'."""
        resolver = self._make_resolver()
        fvr = FieldVoteResult(
            winner="Positive",
            score=0.5,  # tie — L1 gate (score > 0.5) not satisfied, escalates to L2
            contested=True,
            votes={"docling": "Positive", "mineru": "Negative"},
        )
        field_votes = {"result": fvr}
        group = make_group(
            [
                make_candidate(provider_id="docling"),
                make_candidate(provider_id="mineru"),
            ]
        )
        resolved = run_async(resolver.resolve(field_votes, group, {}))

        assert resolved["result"].resolver_used == "priority_hierarchy"

    def test_resolver_conflict_level_stored_on_field_vote_result(self):
        """conflict_level and resolver_used are stored on individual FieldVoteResult objects."""
        resolver = self._make_resolver()
        fvr = FieldVoteResult(
            winner="Positive",
            score=0.65,
            contested=True,
            votes={"docling": "Positive", "mineru": "Negative"},
        )
        field_votes = {"result": fvr}
        group = make_group(
            [
                make_candidate(provider_id="docling"),
                make_candidate(provider_id="mineru"),
            ]
        )
        resolved = run_async(resolver.resolve(field_votes, group, {}))

        assert resolved["result"].conflict_level == "L1"
        assert resolved["result"].resolver_used == "weighted_majority"

    def test_resolver_non_contested_field_has_none_conflict_level(self):
        """Non-contested fields are not processed and retain conflict_level='none'."""
        resolver = self._make_resolver()
        fvr = FieldVoteResult(
            winner="Positive",
            score=1.0,
            contested=False,
            votes={"docling": "Positive"},
        )
        field_votes = {"result": fvr}
        group = make_group([make_candidate()])
        resolved = run_async(resolver.resolve(field_votes, group, {}))

        # Non-contested — should not have been touched
        assert resolved["result"].conflict_level == "none"
        assert resolved["result"].resolver_used == "none"


# ---------------------------------------------------------------------------
# FieldVoteResult dataclass tests
# ---------------------------------------------------------------------------


class TestFieldVoteResult:
    """Tests for FieldVoteResult dataclass."""

    def test_field_vote_result_defaults(self):
        """FieldVoteResult has expected default values for conflict_level and resolver_used."""
        fvr = FieldVoteResult(
            winner="Positive",
            score=1.0,
            contested=False,
            votes={"docling": "Positive"},
        )
        assert fvr.conflict_level == "none"
        assert fvr.resolver_used == "none"

    def test_field_vote_result_custom_levels(self):
        """FieldVoteResult can be created with custom conflict_level and resolver_used."""
        fvr = FieldVoteResult(
            winner="Positive",
            score=0.5,
            contested=True,
            votes={},
            conflict_level="L2",
            resolver_used="priority_hierarchy",
        )
        assert fvr.conflict_level == "L2"
        assert fvr.resolver_used == "priority_hierarchy"


# ---------------------------------------------------------------------------
# ConsensusEngine field_votes schema in consensus_metadata
# ---------------------------------------------------------------------------


class TestConsensusMetadataFieldVotes:
    """Tests that field_votes in consensus_metadata includes conflict_level and resolver_used."""

    def test_field_votes_contain_conflict_level_and_resolver_used(self):
        """Each entry in consensus_metadata['field_votes'] has conflict_level and resolver_used."""
        record = make_record(
            building_id="B1", product="Ceiling Tiles", result="Positive"
        )
        row = CandidateRow(provider_id="docling", record=record, row_index=0)
        group = make_group([row])

        engine = ConsensusEngine()
        result = run_async(engine.merge([group]))

        meta = result[0].consensus_metadata
        for field_name, field_data in meta["field_votes"].items():
            assert "conflict_level" in field_data, (
                f"Missing conflict_level for field '{field_name}'"
            )
            assert "resolver_used" in field_data, (
                f"Missing resolver_used for field '{field_name}'"
            )
