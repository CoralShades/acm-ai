"""Tests for the LLM intent router (rule-based path only — no LLM calls)."""

from open_notebook.graphs.llm_router import (
    RouterResult,
    build_entity_hint,
    classify_with_entities,
)


class TestClassifyWithEntities:
    """Test rule-based classification + entity extraction."""

    def test_write_intent_update(self):
        result = classify_with_entities("Update the risk_status to High for record acm_record:abc123")
        assert result.intent == "write"
        assert result.confidence >= 0.9
        assert "High" in result.entities.get("risk_levels", [])
        assert "acm_record:abc123" in result.entities.get("record_ids", [])

    def test_write_intent_delete(self):
        result = classify_with_entities("Delete the first record in Building A")
        assert result.intent == "write"

    def test_read_intent(self):
        result = classify_with_entities("Show me all records in Building A")
        assert result.intent in ("read", "search")

    def test_analytics_intent(self):
        result = classify_with_entities("How many records are there?")
        assert result.intent == "analytics"
        assert result.confidence >= 0.9

    def test_search_intent(self):
        result = classify_with_entities("Search for vinyl tiles in the document")
        assert result.intent == "search"
        assert "vinyl" in result.entities.get("materials", [])

    def test_meta_intent_schema(self):
        result = classify_with_entities("What fields can I edit?")
        assert result.intent == "meta"
        assert result.confidence >= 0.95

    def test_meta_intent_valid_values(self):
        result = classify_with_entities("What are the valid values for risk_status?")
        assert result.intent == "meta"

    def test_undo_intent(self):
        result = classify_with_entities("Undo my last change")
        assert result.intent == "write"
        assert result.confidence >= 0.95

    def test_general_intent(self):
        result = classify_with_entities("Hello, how are you?")
        assert result.intent == "general"
        assert result.confidence < 0.8

    def test_risk_level_extraction(self):
        result = classify_with_entities("Show me high risk items in Building B")
        assert "High" in result.entities.get("risk_levels", [])

    def test_material_extraction(self):
        result = classify_with_entities("Find all asbestos cement records")
        assert "asbestos" in result.entities.get("materials", [])
        assert "cement" in result.entities.get("materials", [])

    def test_record_id_extraction(self):
        result = classify_with_entities("Show details for building_record:xyz789")
        assert "building_record:xyz789" in result.entities.get("record_ids", [])

    def test_document_search_intent(self):
        result = classify_with_entities("What does the report say about removal procedures?")
        assert result.intent == "search"


class TestBuildEntityHint:
    """Test entity hint generation for system prompt injection."""

    def test_empty_entities(self):
        result = RouterResult(intent="general", entities={})
        assert build_entity_hint(result) == ""

    def test_building_hint(self):
        result = RouterResult(
            intent="read",
            entities={"buildings": ["Building A", "Main Block"]},
        )
        hint = build_entity_hint(result)
        assert "Building A" in hint
        assert "Main Block" in hint
        assert "Buildings mentioned" in hint

    def test_risk_hint(self):
        result = RouterResult(
            intent="read",
            entities={"risk_levels": ["High"]},
        )
        hint = build_entity_hint(result)
        assert "Risk levels: High" in hint

    def test_multiple_entities(self):
        result = RouterResult(
            intent="write",
            entities={
                "buildings": ["Building A"],
                "risk_levels": ["High"],
                "materials": ["vinyl"],
            },
        )
        hint = build_entity_hint(result)
        assert "Buildings mentioned" in hint
        assert "Risk levels" in hint
        assert "Materials" in hint
