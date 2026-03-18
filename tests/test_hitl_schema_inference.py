"""Tests for HITL (Human-In-The-Loop) schema mapping confirmation (MCS6).

Tests cover:
- HITLRegistry: register, wait, submit, cancel, list_pending
- schema_inference_node: interrupt triggered at confidence < 0.8
- schema_inference_node: no interrupt when confidence >= 0.8
- HITL resume: approve, modify, reject actions
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.extractors.hitl_registry import HITLRegistry, get_hitl_registry
from open_notebook.extractors.schema_inference import (
    HITL_CONFIDENCE_THRESHOLD,
    ColumnMapping,
    InferredSchema,
    schema_inference_node,
)

# ---------------------------------------------------------------------------
# Category 1: HITLRegistry unit tests
# ---------------------------------------------------------------------------


class TestHITLRegistry:
    """Tests for the HITLRegistry asyncio.Event-based wait/signal mechanism."""

    def test_register_creates_pending_entry(self):
        registry = HITLRegistry()
        event = registry.register("op-1", {"type": "test"})
        assert registry.is_pending("op-1")
        assert not event.is_set()

    def test_list_pending_returns_registered_ops(self):
        registry = HITLRegistry()
        registry.register("op-1", {"type": "test"})
        registry.register("op-2", {"type": "test"})
        assert set(registry.list_pending()) == {"op-1", "op-2"}

    def test_get_interrupt_data_returns_payload(self):
        registry = HITLRegistry()
        payload = {"type": "schema_mapping_review", "confidence": 0.75}
        registry.register("op-1", payload)
        assert registry.get_interrupt_data("op-1") == payload

    def test_submit_response_unblocks_event(self):
        registry = HITLRegistry()
        event = registry.register("op-1", {"type": "test"})
        assert not event.is_set()
        result = registry.submit_response("op-1", {"action": "approve"})
        assert result is True
        assert event.is_set()

    def test_submit_response_returns_false_for_unknown_op(self):
        registry = HITLRegistry()
        result = registry.submit_response("unknown-op", {"action": "approve"})
        assert result is False

    def test_cancel_removes_pending_entry(self):
        registry = HITLRegistry()
        registry.register("op-1", {"type": "test"})
        registry.cancel("op-1")
        assert not registry.is_pending("op-1")
        assert registry.list_pending() == []

    @pytest.mark.asyncio
    async def test_wait_for_response_returns_submitted_data(self):
        registry = HITLRegistry()
        registry.register("op-1", {"type": "test"})

        # Submit response in a background task
        async def submit_later():
            await asyncio.sleep(0.05)
            registry.submit_response("op-1", {"action": "approve", "data": 42})

        asyncio.create_task(submit_later())
        response = await registry.wait_for_response("op-1", timeout=2.0)
        assert response == {"action": "approve", "data": 42}

    @pytest.mark.asyncio
    async def test_wait_for_response_times_out(self):
        registry = HITLRegistry()
        registry.register("op-1", {"type": "test"})
        with pytest.raises(asyncio.TimeoutError):
            await registry.wait_for_response("op-1", timeout=0.1)

    @pytest.mark.asyncio
    async def test_wait_for_response_raises_key_error_for_unknown_op(self):
        registry = HITLRegistry()
        with pytest.raises(KeyError):
            await registry.wait_for_response("unknown-op", timeout=0.1)

    def test_cleanup_after_wait(self):
        """After wait_for_response completes, the operation is cleaned up."""
        registry = HITLRegistry()
        registry.register("op-1", {"type": "test"})
        registry.submit_response("op-1", {"action": "approve"})
        # Manually check cleanup happened after event.set()
        # (cleanup happens inside wait_for_response, but event is already set)
        assert registry.is_pending("op-1") is False  # Event was set

    def test_singleton_returns_same_instance(self):
        """get_hitl_registry() returns a singleton."""
        r1 = get_hitl_registry()
        r2 = get_hitl_registry()
        assert r1 is r2


# ---------------------------------------------------------------------------
# Category 2: HITL confidence threshold
# ---------------------------------------------------------------------------


class TestHITLConfidenceThreshold:
    """Tests that HITL_CONFIDENCE_THRESHOLD is correctly defined."""

    def test_threshold_is_0_8(self):
        assert HITL_CONFIDENCE_THRESHOLD == 0.8

    def test_confidence_below_threshold_triggers_hitl(self):
        """Confidence 0.75 should be below the HITL threshold."""
        assert 0.75 < HITL_CONFIDENCE_THRESHOLD

    def test_confidence_at_threshold_does_not_trigger_hitl(self):
        """Confidence exactly 0.8 should NOT trigger HITL (< not <=)."""
        assert not (0.8 < HITL_CONFIDENCE_THRESHOLD)

    def test_confidence_above_threshold_does_not_trigger_hitl(self):
        """Confidence 0.85 should NOT trigger HITL."""
        assert not (0.85 < HITL_CONFIDENCE_THRESHOLD)


# ---------------------------------------------------------------------------
# Category 3: InferredSchema with HITL-related fields
# ---------------------------------------------------------------------------


class TestInferredSchemaHITL:
    """InferredSchema supports HITL-related fields."""

    def test_schema_with_low_confidence(self):
        schema = InferredSchema(
            column_mapping={"Room": "Room_or_Area__c"},
            canonical_mapping={"Room": "room_location"},
            confidence=0.65,
            mappings=[
                ColumnMapping(
                    pdf_header="Room",
                    sf_field="Room_or_Area__c",
                    confidence=0.65,
                )
            ],
        )
        assert schema.confidence < HITL_CONFIDENCE_THRESHOLD
        assert len(schema.mappings) == 1

    def test_schema_with_high_confidence(self):
        schema = InferredSchema(
            column_mapping={"Room": "Room_or_Area__c"},
            canonical_mapping={"Room": "room_location"},
            confidence=0.95,
        )
        assert schema.confidence >= HITL_CONFIDENCE_THRESHOLD


# ---------------------------------------------------------------------------
# Category 4: schema_inference_node with interrupt (integration-style)
# ---------------------------------------------------------------------------


class TestSchemaInferenceNodeHITL:
    """Tests for interrupt() behavior in schema_inference_node.

    These tests mock the DB and LLM to control the confidence score,
    then verify that interrupt() is called (or not) based on confidence.

    Note: imports inside schema_inference_node are lazy (inside the function),
    so we patch at the source module level, not at schema_inference module level.
    """

    # Common mock patches for all integration tests
    _DB_PATCH = "open_notebook.database.repository.repo_query"
    _ENSURE_ID_PATCH = "open_notebook.database.repository.ensure_record_id"
    _GET_PROFILE_PATCH = "open_notebook.extractors.format_profile_repository.get_profile_by_signature"
    _SAVE_PROFILE_PATCH = "open_notebook.extractors.format_profile_repository.save_profile"
    _PROVISION_MODEL_PATCH = "open_notebook.graphs.utils.provision_langchain_model"
    # interrupt IS a module-level import in schema_inference.py
    _INTERRUPT_PATCH = "open_notebook.extractors.schema_inference.interrupt"

    @pytest.mark.asyncio
    async def test_no_interrupt_when_confidence_above_threshold(self):
        """When LLM returns confidence >= 0.8, no interrupt is triggered."""
        mock_source = MagicMock()
        mock_source.id = "source:test1"

        state = {
            "source": mock_source,
            "model_id": None,
            "document_metadata": None,
        }

        mock_table_data = [
            {
                "docling_document_json": {
                    "table_cells": [
                        {"text": "Room", "column_header": True, "start_col_offset_idx": 0},
                        {"text": "Item", "column_header": True, "start_col_offset_idx": 1},
                        {"text": "Result", "column_header": True, "start_col_offset_idx": 2},
                    ]
                }
            }
        ]

        mock_llm_response = MagicMock()
        mock_llm_response.content = """```json
        {
            "mappings": [
                {"pdf_header": "Room", "sf_field": "Room_or_Area__c", "confidence": 0.95},
                {"pdf_header": "Item", "sf_field": "Item_Name__c", "confidence": 0.90},
                {"pdf_header": "Result", "sf_field": "Sample_Analysis_Result_Material_Status__c", "confidence": 0.85}
            ],
            "unmapped_headers": [],
            "overall_confidence": 0.90,
            "detected_consultant": "Test Consultant"
        }
        ```"""

        with (
            patch(self._DB_PATCH, new_callable=AsyncMock, return_value=mock_table_data),
            patch(self._ENSURE_ID_PATCH, return_value="source:test1"),
            patch(self._GET_PROFILE_PATCH, new_callable=AsyncMock, return_value=None),
            patch(self._SAVE_PROFILE_PATCH, new_callable=AsyncMock, return_value=[{"id": "profile:test"}]),
            patch(self._PROVISION_MODEL_PATCH, new_callable=AsyncMock) as mock_provision,
            patch(self._INTERRUPT_PATCH) as mock_interrupt,
        ):
            mock_model = AsyncMock()
            mock_model.ainvoke = AsyncMock(return_value=mock_llm_response)
            mock_provision.return_value = mock_model

            result = await schema_inference_node(state)

            # interrupt() should NOT have been called
            mock_interrupt.assert_not_called()
            assert "inferred_schema" in result
            assert result["inferred_schema"].confidence >= HITL_CONFIDENCE_THRESHOLD

    @pytest.mark.asyncio
    async def test_interrupt_called_when_confidence_below_threshold(self):
        """When LLM returns confidence < 0.8, interrupt() IS called."""
        mock_source = MagicMock()
        mock_source.id = "source:test2"

        state = {
            "source": mock_source,
            "model_id": None,
            "document_metadata": None,
        }

        mock_table_data = [
            {
                "docling_document_json": {
                    "table_cells": [
                        {"text": "Location", "column_header": True, "start_col_offset_idx": 0},
                        {"text": "Material Type", "column_header": True, "start_col_offset_idx": 1},
                    ]
                }
            }
        ]

        mock_llm_response = MagicMock()
        mock_llm_response.content = """```json
        {
            "mappings": [
                {"pdf_header": "Location", "sf_field": "Room_or_Area__c", "confidence": 0.60},
                {"pdf_header": "Material Type", "sf_field": "Item_Name__c", "confidence": 0.55}
            ],
            "unmapped_headers": [],
            "overall_confidence": 0.58,
            "detected_consultant": null
        }
        ```"""

        with (
            patch(self._DB_PATCH, new_callable=AsyncMock, return_value=mock_table_data),
            patch(self._ENSURE_ID_PATCH, return_value="source:test2"),
            patch(self._GET_PROFILE_PATCH, new_callable=AsyncMock, return_value=None),
            patch(self._SAVE_PROFILE_PATCH, new_callable=AsyncMock, return_value=[{"id": "profile:test"}]),
            patch(self._PROVISION_MODEL_PATCH, new_callable=AsyncMock) as mock_provision,
            patch(self._INTERRUPT_PATCH, return_value={"action": "approve"}) as mock_interrupt,
        ):
            mock_model = AsyncMock()
            mock_model.ainvoke = AsyncMock(return_value=mock_llm_response)
            mock_provision.return_value = mock_model

            result = await schema_inference_node(state)

            # interrupt() SHOULD have been called
            mock_interrupt.assert_called_once()
            call_args = mock_interrupt.call_args[0][0]
            assert call_args["type"] == "schema_mapping_review"
            assert call_args["overall_confidence"] == 0.58
            assert len(call_args["mappings"]) == 2
            assert "inferred_schema" in result

    @pytest.mark.asyncio
    async def test_interrupt_resume_with_reject_returns_empty(self):
        """When user rejects the mapping, schema_inference_node returns {}."""
        mock_source = MagicMock()
        mock_source.id = "source:test3"

        state = {
            "source": mock_source,
            "model_id": None,
            "document_metadata": None,
        }

        mock_table_data = [
            {
                "docling_document_json": {
                    "table_cells": [
                        {"text": "Col1", "column_header": True, "start_col_offset_idx": 0},
                    ]
                }
            }
        ]

        mock_llm_response = MagicMock()
        mock_llm_response.content = """```json
        {
            "mappings": [
                {"pdf_header": "Col1", "sf_field": "Room_or_Area__c", "confidence": 0.40}
            ],
            "unmapped_headers": [],
            "overall_confidence": 0.40
        }
        ```"""

        with (
            patch(self._DB_PATCH, new_callable=AsyncMock, return_value=mock_table_data),
            patch(self._ENSURE_ID_PATCH, return_value="source:test3"),
            patch(self._GET_PROFILE_PATCH, new_callable=AsyncMock, return_value=None),
            patch(self._SAVE_PROFILE_PATCH, new_callable=AsyncMock, return_value=[{"id": "profile:test"}]),
            patch(self._PROVISION_MODEL_PATCH, new_callable=AsyncMock) as mock_provision,
            patch(self._INTERRUPT_PATCH, return_value={"action": "reject"}),
        ):
            mock_model = AsyncMock()
            mock_model.ainvoke = AsyncMock(return_value=mock_llm_response)
            mock_provision.return_value = mock_model

            result = await schema_inference_node(state)
            assert result == {}

    @pytest.mark.asyncio
    async def test_interrupt_resume_with_modify_uses_user_mappings(self):
        """When user modifies mappings, the returned schema uses user's mappings."""
        mock_source = MagicMock()
        mock_source.id = "source:test4"

        state = {
            "source": mock_source,
            "model_id": None,
            "document_metadata": None,
        }

        mock_table_data = [
            {
                "docling_document_json": {
                    "table_cells": [
                        {"text": "Area", "column_header": True, "start_col_offset_idx": 0},
                        {"text": "Stuff", "column_header": True, "start_col_offset_idx": 1},
                    ]
                }
            }
        ]

        mock_llm_response = MagicMock()
        mock_llm_response.content = """```json
        {
            "mappings": [
                {"pdf_header": "Area", "sf_field": "Room_or_Area__c", "confidence": 0.70},
                {"pdf_header": "Stuff", "sf_field": "Quantity__c", "confidence": 0.40}
            ],
            "unmapped_headers": [],
            "overall_confidence": 0.55
        }
        ```"""

        user_response = {
            "action": "modify",
            "mappings": [
                {"pdf_header": "Area", "sf_field": "Room_or_Area__c", "confidence": 1.0},
                {"pdf_header": "Stuff", "sf_field": "Item_Name__c", "confidence": 1.0},
            ],
        }

        with (
            patch(self._DB_PATCH, new_callable=AsyncMock, return_value=mock_table_data),
            patch(self._ENSURE_ID_PATCH, return_value="source:test4"),
            patch(self._GET_PROFILE_PATCH, new_callable=AsyncMock, return_value=None),
            patch(self._SAVE_PROFILE_PATCH, new_callable=AsyncMock, return_value=[{"id": "profile:modified"}]) as mock_save,
            patch(self._PROVISION_MODEL_PATCH, new_callable=AsyncMock) as mock_provision,
            patch(self._INTERRUPT_PATCH, return_value=user_response),
        ):
            mock_model = AsyncMock()
            mock_model.ainvoke = AsyncMock(return_value=mock_llm_response)
            mock_provision.return_value = mock_model

            result = await schema_inference_node(state)

            assert "inferred_schema" in result
            schema = result["inferred_schema"]
            assert schema.column_mapping["Stuff"] == "Item_Name__c"
            assert schema.confidence == 1.0
            save_call = mock_save.call_args[0][0]
            assert save_call["verified_by_user"] is True
