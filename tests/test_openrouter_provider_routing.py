"""Tests for OpenRouter provider hard-lock routing + production features (E27-S3).

Verifies that _apply_openrouter_preferences() configures:
- provider.only (hard allowlist, not soft provider.order)
- allow_fallbacks=false (no silent provider substitution)
- zdr=true (Zero Data Retention for government data)
- data_collection="deny" (don't train on government data)
- Response Healing plugin (auto-fix malformed JSON)
- Request metadata (production observability tagging)

Ref: https://openrouter.ai/docs/guides/routing/provider-selection
Ref: https://openrouter.ai/docs/guides/features/plugins/response-healing
"""

from unittest.mock import MagicMock

import pytest


def _make_openrouter_model(model_kwargs=None):
    """Create a mock LangChain model that looks like an OpenRouter model."""
    mock = MagicMock()
    mock.openai_api_base = "https://openrouter.ai/api/v1"
    mock.base_url = "https://openrouter.ai/api/v1"
    mock.model_name = "anthropic/claude-sonnet-4"
    mock.model_kwargs = model_kwargs or {}

    # Track what object.__setattr__ does
    original_kwargs = dict(mock.model_kwargs)

    def capture_setattr(obj, name, value):
        if name == "model_kwargs":
            obj.__dict__[name] = value

    # We need to actually capture the setattr call
    mock.__dict__["model_kwargs"] = model_kwargs or {}
    return mock


def _apply_and_get_extra_body(model_kwargs=None, **apply_kwargs):
    """Helper: apply preferences to a mock OpenRouter model and return extra_body."""
    from open_notebook.graphs.utils import _apply_openrouter_preferences

    mock = MagicMock()
    mock.openai_api_base = "https://openrouter.ai/api/v1"
    mock.model_name = "anthropic/claude-sonnet-4"
    initial_kwargs = model_kwargs or {}
    mock.model_kwargs = initial_kwargs

    _apply_openrouter_preferences(mock, **apply_kwargs)

    # object.__setattr__ bypasses MagicMock, so check __dict__ directly
    result_kwargs = mock.__dict__.get("model_kwargs", mock.model_kwargs)
    return result_kwargs.get("extra_body", {})


class TestProviderHardLock:
    """Verify provider routing uses hard lock, not soft preference."""

    def test_uses_provider_only_not_order(self):
        """extra_body must use 'only' key, not 'order' key."""
        extra_body = _apply_and_get_extra_body()
        provider = extra_body.get("provider", {})

        assert "only" in provider, "Must use provider.only for hard lock"
        assert "order" not in provider, "Must NOT use provider.order (soft preference)"
        assert "ignore" not in provider, "Must NOT use provider.ignore (partial blocklist)"

    def test_allow_fallbacks_disabled(self):
        """allow_fallbacks must be False."""
        extra_body = _apply_and_get_extra_body()
        provider = extra_body.get("provider", {})
        assert provider.get("allow_fallbacks") is False

    def test_anthropic_is_only_allowed_provider(self):
        """Only Anthropic should be in the provider.only list."""
        from open_notebook.graphs.utils import OPENROUTER_ALLOWED_PROVIDERS

        assert OPENROUTER_ALLOWED_PROVIDERS == ["Anthropic"]

    def test_provider_only_matches_constant(self):
        """provider.only in extra_body matches OPENROUTER_ALLOWED_PROVIDERS."""
        from open_notebook.graphs.utils import OPENROUTER_ALLOWED_PROVIDERS

        extra_body = _apply_and_get_extra_body()
        provider = extra_body.get("provider", {})
        assert provider.get("only") == OPENROUTER_ALLOWED_PROVIDERS

    def test_zdr_disabled_by_default(self):
        """ZDR is off by default (requires OPENROUTER_ZDR=true env var)."""
        from unittest.mock import patch

        with patch.dict("os.environ", {}, clear=False):
            # Ensure OPENROUTER_ZDR is not set
            import os

            os.environ.pop("OPENROUTER_ZDR", None)
            extra_body = _apply_and_get_extra_body()
        provider = extra_body.get("provider", {})
        assert "zdr" not in provider

    def test_zdr_enabled_when_env_set(self):
        """ZDR is enabled when OPENROUTER_ZDR=true."""
        from unittest.mock import patch

        with patch.dict("os.environ", {"OPENROUTER_ZDR": "true"}):
            extra_body = _apply_and_get_extra_body()
        provider = extra_body.get("provider", {})
        assert provider.get("zdr") is True

    def test_data_collection_denied(self):
        """Government data must not be used for training."""
        extra_body = _apply_and_get_extra_body()
        provider = extra_body.get("provider", {})
        assert provider.get("data_collection") == "deny"

    def test_require_parameters_enabled(self):
        """Provider must support all request parameters."""
        extra_body = _apply_and_get_extra_body()
        provider = extra_body.get("provider", {})
        assert provider.get("require_parameters") is True

    def test_skips_non_openrouter_models(self):
        """Must not apply preferences to non-OpenRouter models."""
        from open_notebook.graphs.utils import _apply_openrouter_preferences

        mock = MagicMock()
        mock.openai_api_base = "https://api.anthropic.com/v1"
        mock.base_url = "https://api.anthropic.com/v1"
        mock.model_kwargs = {}

        result = _apply_openrouter_preferences(mock)
        # model_kwargs should be unchanged (no object.__setattr__ call)
        assert result.model_kwargs == {}


class TestResponseHealing:
    """Verify Response Healing plugin is configured."""

    def test_response_healing_plugin_present(self):
        """Response Healing plugin must be in the plugins array."""
        extra_body = _apply_and_get_extra_body()
        plugins = extra_body.get("plugins", [])
        plugin_ids = [p.get("id") for p in plugins]
        assert "response-healing" in plugin_ids

    def test_plugins_not_duplicated_on_merge(self):
        """If response-healing already exists, don't add it again."""
        extra_body = _apply_and_get_extra_body(
            model_kwargs={
                "extra_body": {"plugins": [{"id": "response-healing"}]}
            }
        )
        plugins = extra_body.get("plugins", [])
        healing_count = sum(1 for p in plugins if p.get("id") == "response-healing")
        assert healing_count == 1, "response-healing plugin should not be duplicated"

    def test_preserves_existing_plugins(self):
        """Existing plugins must be preserved when adding response-healing."""
        extra_body = _apply_and_get_extra_body(
            model_kwargs={
                "extra_body": {"plugins": [{"id": "custom-plugin"}]}
            }
        )
        plugins = extra_body.get("plugins", [])
        plugin_ids = [p.get("id") for p in plugins]
        assert "custom-plugin" in plugin_ids
        assert "response-healing" in plugin_ids


class TestRequestMetadata:
    """Verify request metadata tagging for production observability."""

    def test_default_metadata_present(self):
        """App and pipeline metadata always present."""
        extra_body = _apply_and_get_extra_body()
        metadata = extra_body.get("metadata", {})
        assert metadata.get("app") == "acm-ai"
        assert metadata.get("pipeline") == "extraction"

    def test_source_id_tagged(self):
        """source_id passed through to metadata."""
        extra_body = _apply_and_get_extra_body(source_id="source:abc123")
        metadata = extra_body.get("metadata", {})
        assert metadata.get("source_id") == "source:abc123"

    def test_building_name_tagged(self):
        """building_name passed through to metadata."""
        extra_body = _apply_and_get_extra_body(building_name="Main Building")
        metadata = extra_body.get("metadata", {})
        assert metadata.get("building") == "Main Building"

    def test_stage_name_tagged(self):
        """stage_name passed through to metadata."""
        extra_body = _apply_and_get_extra_body(stage_name="orchestrator")
        metadata = extra_body.get("metadata", {})
        assert metadata.get("stage") == "orchestrator"

    def test_metadata_values_truncated(self):
        """Metadata values must be <=512 chars (OpenRouter limit)."""
        long_value = "x" * 1000
        extra_body = _apply_and_get_extra_body(source_id=long_value)
        metadata = extra_body.get("metadata", {})
        assert len(metadata.get("source_id", "")) <= 512

    def test_none_values_excluded(self):
        """None optional params should not appear in metadata."""
        extra_body = _apply_and_get_extra_body()
        metadata = extra_body.get("metadata", {})
        assert "source_id" not in metadata
        assert "building" not in metadata
        assert "stage" not in metadata


class TestDeepMerge:
    """Verify extra_body merging preserves existing fields."""

    def test_preserves_existing_extra_body_fields(self):
        """Must not overwrite existing extra_body fields."""
        extra_body = _apply_and_get_extra_body(
            model_kwargs={"extra_body": {"custom_field": "preserved"}}
        )
        assert extra_body.get("custom_field") == "preserved"

    def test_preserves_existing_provider_fields(self):
        """Must deep-merge provider dict, not overwrite it."""
        extra_body = _apply_and_get_extra_body(
            model_kwargs={
                "extra_body": {"provider": {"custom_provider_field": True}}
            }
        )
        provider = extra_body.get("provider", {})
        assert provider.get("custom_provider_field") is True
        assert provider.get("only") == ["Anthropic"]

    def test_preserves_existing_model_kwargs(self):
        """Must not lose non-extra_body model_kwargs."""
        from open_notebook.graphs.utils import _apply_openrouter_preferences

        mock = MagicMock()
        mock.openai_api_base = "https://openrouter.ai/api/v1"
        mock.model_name = "anthropic/claude-sonnet-4"
        mock.model_kwargs = {"temperature": 0.1, "extra_body": {}}

        _apply_openrouter_preferences(mock)

        result_kwargs = mock.__dict__.get("model_kwargs", {})
        assert result_kwargs.get("temperature") == 0.1


class TestOldConstantsRemoved:
    """Verify old soft-preference constants no longer exist."""

    def test_no_ignored_providers(self):
        import open_notebook.graphs.utils as utils

        assert not hasattr(
            utils, "OPENROUTER_IGNORED_PROVIDERS"
        ), "OPENROUTER_IGNORED_PROVIDERS should be removed"

    def test_no_provider_order(self):
        import open_notebook.graphs.utils as utils

        assert not hasattr(
            utils, "OPENROUTER_PROVIDER_ORDER"
        ), "OPENROUTER_PROVIDER_ORDER should be removed"

    def test_allowed_providers_exists(self):
        import open_notebook.graphs.utils as utils

        assert hasattr(
            utils, "OPENROUTER_ALLOWED_PROVIDERS"
        ), "OPENROUTER_ALLOWED_PROVIDERS must exist"


class TestProviderVerification:
    """Verify provider verification logging helper."""

    def test_verify_function_exists(self):
        """_verify_provider_routing function must exist and be callable."""
        from open_notebook.graphs.utils import _verify_provider_routing

        assert callable(_verify_provider_routing)

    @pytest.mark.asyncio
    async def test_handles_missing_metadata(self):
        """Must not crash when response has no metadata."""
        from open_notebook.graphs.utils import _verify_provider_routing

        mock_response = MagicMock()
        mock_response.response_metadata = {}
        mock_response.additional_kwargs = {}

        result = await _verify_provider_routing(mock_response, "test_stage")
        assert result is None

    @pytest.mark.asyncio
    async def test_handles_none_metadata(self):
        """Must not crash when response_metadata is None."""
        from open_notebook.graphs.utils import _verify_provider_routing

        mock_response = MagicMock()
        mock_response.response_metadata = None
        mock_response.additional_kwargs = {}

        result = await _verify_provider_routing(mock_response, "test_stage")
        assert result is None

    @pytest.mark.asyncio
    async def test_detects_provider_from_metadata(self):
        """Returns provider info when available in response_metadata."""
        from open_notebook.graphs.utils import _verify_provider_routing

        mock_response = MagicMock()
        mock_response.response_metadata = {
            "provider": "Anthropic",
            "model": "anthropic/claude-sonnet-4",
            "id": "gen-test123",
        }

        result = await _verify_provider_routing(mock_response, "test_stage")
        assert result is not None
        assert result["provider_name"] == "Anthropic"

    @pytest.mark.asyncio
    async def test_detects_provider_mismatch(self):
        """Logs warning when provider doesn't match expected."""
        from open_notebook.graphs.utils import _verify_provider_routing

        mock_response = MagicMock()
        mock_response.response_metadata = {
            "provider": "Google",
            "model": "anthropic/claude-sonnet-4",
            "id": "gen-test456",
        }

        result = await _verify_provider_routing(
            mock_response, "test_stage", expected_provider="Anthropic"
        )
        assert result is not None
        assert result["provider_name"] == "Google"

    @pytest.mark.asyncio
    async def test_no_api_key_returns_none(self):
        """Returns None gracefully when no API key and no inline provider."""
        from unittest.mock import patch

        from open_notebook.graphs.utils import _verify_provider_routing

        mock_response = MagicMock()
        mock_response.response_metadata = {"id": "gen-needs-api-call"}
        mock_response.additional_kwargs = {}

        with patch.dict("os.environ", {}, clear=True):
            result = await _verify_provider_routing(mock_response, "test_stage")
        assert result is None


class TestTransforms:
    """Verify transforms configuration."""

    def test_middle_out_transform_present(self):
        """middle-out transform for context compression must be present."""
        extra_body = _apply_and_get_extra_body()
        transforms = extra_body.get("transforms", [])
        assert "middle-out" in transforms


class TestPydanticToOpenRouterSchema:
    """Verify pydantic_to_openrouter_schema() schema transformation (E27-S4)."""

    def test_no_refs_in_output(self):
        """Output schema must have all $ref entries resolved (inlined)."""
        from pydantic import BaseModel

        from open_notebook.graphs.utils import pydantic_to_openrouter_schema

        class Inner(BaseModel):
            value: int

        class Outer(BaseModel):
            inner: Inner

        schema = pydantic_to_openrouter_schema(Outer)
        schema_str = str(schema)
        assert "$ref" not in schema_str
        assert "$defs" not in schema_str

    def test_additional_properties_false_on_all_objects(self):
        """All object schemas must have additionalProperties: false."""
        from pydantic import BaseModel

        from open_notebook.graphs.utils import pydantic_to_openrouter_schema

        class Nested(BaseModel):
            x: int

        class Root(BaseModel):
            nested: Nested
            name: str

        schema = pydantic_to_openrouter_schema(Root)
        assert schema.get("additionalProperties") is False
        nested_props = schema["properties"]["nested"]
        assert nested_props.get("additionalProperties") is False

    def test_title_removed(self):
        """Pydantic 'title' metadata must be removed from top level."""
        from pydantic import BaseModel

        from open_notebook.graphs.utils import pydantic_to_openrouter_schema

        class MyModel(BaseModel):
            x: int

        schema = pydantic_to_openrouter_schema(MyModel)
        assert "title" not in schema

    def test_acm_extraction_schema_no_refs(self):
        """ACMExtractionResult schema must have no $ref entries."""
        from open_notebook.extractors.acm_schemas import ACMExtractionResult
        from open_notebook.graphs.utils import pydantic_to_openrouter_schema

        schema = pydantic_to_openrouter_schema(ACMExtractionResult)
        schema_str = str(schema)
        assert "$ref" not in schema_str

    def test_acm_extraction_schema_has_records(self):
        """ACMExtractionResult schema must have records array."""
        from open_notebook.extractors.acm_schemas import ACMExtractionResult
        from open_notebook.graphs.utils import pydantic_to_openrouter_schema

        schema = pydantic_to_openrouter_schema(ACMExtractionResult)
        assert "records" in schema.get("properties", {})
        records_prop = schema["properties"]["records"]
        assert records_prop.get("type") == "array"


class TestGetACMExtractionSchema:
    """Verify _get_acm_extraction_schema() caching (E27-S4)."""

    def test_returns_dict(self):
        """Must return a dict schema."""
        from open_notebook.graphs.utils import _get_acm_extraction_schema

        schema = _get_acm_extraction_schema()
        assert isinstance(schema, dict)
        assert "properties" in schema

    def test_cached_identity(self):
        """Repeated calls must return the same object (identity cache)."""
        from open_notebook.graphs.utils import _get_acm_extraction_schema

        schema1 = _get_acm_extraction_schema()
        schema2 = _get_acm_extraction_schema()
        assert schema1 is schema2


class TestInjectResponseFormat:
    """Verify _inject_response_format() injection logic (E27-S4)."""

    def test_injects_on_openrouter_model(self):
        """Must inject response_format into OpenRouter model's extra_body."""
        from open_notebook.graphs.utils import _inject_response_format

        mock = MagicMock()
        mock.openai_api_base = "https://openrouter.ai/api/v1"
        mock.model_kwargs = {}

        schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
        result = _inject_response_format(mock, schema, "TestSchema")

        result_kwargs = result.__dict__.get("model_kwargs", {})
        rf = result_kwargs.get("extra_body", {}).get("response_format", {})
        assert rf.get("type") == "json_schema"
        assert rf["json_schema"]["name"] == "TestSchema"
        assert rf["json_schema"]["strict"] is True
        assert rf["json_schema"]["schema"] == schema

    def test_skips_non_openrouter_model(self):
        """Must not inject on non-OpenRouter models."""
        from open_notebook.graphs.utils import _inject_response_format

        mock = MagicMock()
        mock.openai_api_base = "https://api.anthropic.com/v1"
        mock.base_url = "https://api.anthropic.com/v1"
        mock.model_kwargs = {}

        schema = {"type": "object"}
        _inject_response_format(mock, schema, "TestSchema")

        # model_kwargs should be unchanged
        assert mock.model_kwargs == {}

    def test_preserves_existing_extra_body(self):
        """Must merge into existing extra_body, not overwrite."""
        from open_notebook.graphs.utils import _inject_response_format

        mock = MagicMock()
        mock.openai_api_base = "https://openrouter.ai/api/v1"
        mock.model_kwargs = {
            "extra_body": {"provider": {"only": ["Anthropic"]}}
        }

        schema = {"type": "object"}
        _inject_response_format(mock, schema, "TestSchema")

        result_kwargs = mock.__dict__.get("model_kwargs", {})
        extra_body = result_kwargs.get("extra_body", {})
        # Provider settings preserved
        assert extra_body.get("provider", {}).get("only") == ["Anthropic"]
        # response_format added
        assert "response_format" in extra_body

    def test_returns_same_model(self):
        """Must return the same model object (mutates in place)."""
        from open_notebook.graphs.utils import _inject_response_format

        mock = MagicMock()
        mock.openai_api_base = "https://openrouter.ai/api/v1"
        mock.model_kwargs = {}

        result = _inject_response_format(mock, {"type": "object"}, "Test")
        assert result is mock


class TestUnwrapCompletionStateRemoved:
    """Verify _unwrap_completion_state is fully removed (E27-S4)."""

    def test_function_not_importable(self):
        """_unwrap_completion_state must not exist in utils module."""
        import open_notebook.graphs.utils as utils

        assert not hasattr(utils, "_unwrap_completion_state")
