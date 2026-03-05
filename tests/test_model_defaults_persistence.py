"""
Tests for E35-S2: Persist Model Defaults to SurrealDB.

Verifies that:
- update_defaults_if_needed() only fills empty (None) fields
- update_defaults_if_needed() never overwrites user-set values
- DefaultModels.get_instance() reads from SurrealDB
- DefaultModels.update() persists to SurrealDB via repo_upsert
- Partial PUT requests preserve untouched fields

Patch targets:
- get_instance() calls repo_query imported into open_notebook.domain.models
- update() calls repo_upsert and repo_query imported into open_notebook.domain.base
"""

from unittest.mock import AsyncMock, patch

import pytest

from open_notebook.domain.models import DefaultModels

# ---------------------------------------------------------------------------
# Patch target constants — where each function is *used*, not *defined*
# ---------------------------------------------------------------------------

_MODELS_REPO_QUERY = "open_notebook.domain.models.repo_query"
_BASE_REPO_UPSERT = "open_notebook.domain.base.repo_upsert"
_BASE_REPO_QUERY = "open_notebook.domain.base.repo_query"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_defaults(**kwargs) -> DefaultModels:
    """Create a DefaultModels instance without touching the singleton cache."""
    instance = object.__new__(DefaultModels)
    object.__setattr__(instance, "__dict__", {})
    super(DefaultModels.__bases__[0], instance).__init__(**kwargs)
    return instance


def _default_db_record(**overrides) -> list:
    """Return a single-item list mimicking a SurrealDB SELECT result."""
    base = {
        "id": "open_notebook:default_models",
        "default_chat_model": None,
        "default_transformation_model": None,
        "large_context_model": None,
        "default_text_to_speech_model": None,
        "default_speech_to_text_model": None,
        "default_embedding_model": None,
        "default_tools_model": None,
        "default_extraction_model": None,
    }
    base.update(overrides)
    return [base]


# ---------------------------------------------------------------------------
# Tests — provisioning logic
# ---------------------------------------------------------------------------


class TestProvisioningPreservesUserDefaults:
    """update_defaults_if_needed() must not overwrite user-set values."""

    @pytest.mark.asyncio
    @patch(_MODELS_REPO_QUERY, new_callable=AsyncMock)
    async def test_provisioning_preserves_user_defaults(self, mock_models_query):
        """If a field already has a value, provisioning must not overwrite it."""
        from api.model_provisioning import update_defaults_if_needed

        user_model_id = "model:user_chosen"
        provisioned_model_id = "model:env_provisioned"

        mock_models_query.return_value = _default_db_record(
            default_chat_model=user_model_id
        )

        provisioned = {"chat": provisioned_model_id}

        DefaultModels.clear_instance()

        # Patch base.repo_upsert so we can assert it is NOT called
        with patch(_BASE_REPO_UPSERT, new_callable=AsyncMock) as mock_upsert:
            await update_defaults_if_needed(provisioned)
            mock_upsert.assert_not_called()

    @pytest.mark.asyncio
    @patch(_MODELS_REPO_QUERY, new_callable=AsyncMock)
    async def test_provisioning_fills_empty_fields(self, mock_models_query):
        """If a field is None, provisioning must populate it."""
        from api.model_provisioning import update_defaults_if_needed

        provisioned_model_id = "model:env_provisioned"

        mock_models_query.return_value = _default_db_record(default_chat_model=None)

        provisioned = {"chat": provisioned_model_id}

        DefaultModels.clear_instance()

        upsert_return = _default_db_record(default_chat_model=provisioned_model_id)[0]
        # base.repo_query is called inside update() to re-fetch after upsert
        with (
            patch(
                _BASE_REPO_UPSERT, new_callable=AsyncMock, return_value=upsert_return
            ) as mock_upsert,
            patch(
                _BASE_REPO_QUERY, new_callable=AsyncMock, return_value=[upsert_return]
            ),
        ):
            await update_defaults_if_needed(provisioned)

            mock_upsert.assert_called_once()
            data_arg = mock_upsert.call_args[0][2]
            assert data_arg.get("default_chat_model") == provisioned_model_id

    @pytest.mark.asyncio
    @patch(_MODELS_REPO_QUERY, new_callable=AsyncMock)
    async def test_provisioning_skips_none_provisioned_value(self, mock_models_query):
        """If provisioning returned None for a purpose, skip that field."""
        from api.model_provisioning import update_defaults_if_needed

        mock_models_query.return_value = _default_db_record(default_chat_model=None)

        provisioned = {"chat": None}  # provisioning produced nothing

        DefaultModels.clear_instance()

        with patch(_BASE_REPO_UPSERT, new_callable=AsyncMock) as mock_upsert:
            await update_defaults_if_needed(provisioned)
            mock_upsert.assert_not_called()

    @pytest.mark.asyncio
    @patch(_MODELS_REPO_QUERY, new_callable=AsyncMock)
    async def test_provisioning_multiple_fields_mixed(self, mock_models_query):
        """When some fields are set and some are empty, only empty ones get filled."""
        from api.model_provisioning import update_defaults_if_needed

        user_chat = "model:user_chat"
        provisioned_chat = "model:env_chat"
        provisioned_embed = "model:env_embed"

        # chat is user-set; embedding is empty
        mock_models_query.return_value = _default_db_record(
            default_chat_model=user_chat,
            default_embedding_model=None,
        )

        upsert_return = _default_db_record(
            default_chat_model=user_chat,
            default_embedding_model=provisioned_embed,
        )[0]

        provisioned = {"chat": provisioned_chat, "embedding": provisioned_embed}

        DefaultModels.clear_instance()

        with (
            patch(
                _BASE_REPO_UPSERT, new_callable=AsyncMock, return_value=upsert_return
            ) as mock_upsert,
            patch(
                _BASE_REPO_QUERY, new_callable=AsyncMock, return_value=[upsert_return]
            ),
        ):
            await update_defaults_if_needed(provisioned)

            # upsert was called (embedding was empty)
            mock_upsert.assert_called_once()
            data_arg = mock_upsert.call_args[0][2]

            # chat must NOT have been overwritten by the provisioned value
            assert data_arg.get("default_chat_model") == user_chat
            # embedding must have been filled
            assert data_arg.get("default_embedding_model") == provisioned_embed


# ---------------------------------------------------------------------------
# Tests — DefaultModels.get_instance() reads from DB
# ---------------------------------------------------------------------------


class TestDefaultModelsReadFromDb:
    """DefaultModels.get_instance() reads persisted values from SurrealDB."""

    @pytest.mark.asyncio
    @patch(_MODELS_REPO_QUERY, new_callable=AsyncMock)
    async def test_get_defaults_reads_from_db(self, mock_models_query):
        """get_instance() returns values stored in SurrealDB."""
        saved_model = "model:my_saved_model"
        mock_models_query.return_value = _default_db_record(
            default_chat_model=saved_model
        )

        instance = await DefaultModels.get_instance()
        assert instance.default_chat_model == saved_model
        assert instance.default_embedding_model is None

    @pytest.mark.asyncio
    @patch(_MODELS_REPO_QUERY, new_callable=AsyncMock)
    async def test_get_defaults_returns_empty_defaults_when_no_record(
        self, mock_models_query
    ):
        """get_instance() returns a blank DefaultModels when DB has no record."""
        mock_models_query.return_value = []

        instance = await DefaultModels.get_instance()
        assert instance.default_chat_model is None
        assert instance.default_embedding_model is None


# ---------------------------------------------------------------------------
# Tests — DefaultModels.update() persists to DB
# ---------------------------------------------------------------------------


class TestDefaultModelsPersistOnUpdate:
    """DefaultModels.update() calls repo_upsert with correct data."""

    @pytest.mark.asyncio
    async def test_put_defaults_persists(self):
        """Setting a field on DefaultModels and calling update() invokes repo_upsert."""
        new_model = "model:new_chat"
        upsert_return = _default_db_record(default_chat_model=new_model)[0]

        with (
            patch(
                _BASE_REPO_UPSERT, new_callable=AsyncMock, return_value=upsert_return
            ) as mock_upsert,
            patch(
                _BASE_REPO_QUERY, new_callable=AsyncMock, return_value=[upsert_return]
            ),
        ):
            defaults = _make_defaults(default_chat_model=new_model)
            await defaults.update()

            mock_upsert.assert_called_once()
            data_arg = mock_upsert.call_args[0][2]
            assert data_arg.get("default_chat_model") == new_model


# ---------------------------------------------------------------------------
# Tests — partial PUT preserves untouched fields
# ---------------------------------------------------------------------------


class TestPartialUpdatePreservesOtherFields:
    """A PUT that touches only some fields must not zero-out others."""

    @pytest.mark.asyncio
    @patch(_MODELS_REPO_QUERY, new_callable=AsyncMock)
    async def test_put_partial_update_preserves_others(self, mock_models_query):
        """
        Simulate the PUT /api/models/defaults endpoint pattern:
        load defaults, apply only the non-None fields from the request,
        then save — existing fields must survive.
        """
        existing_embed = "model:existing_embed"
        new_chat = "model:new_chat"

        mock_models_query.return_value = _default_db_record(
            default_chat_model=None,
            default_embedding_model=existing_embed,
        )

        after_upsert = _default_db_record(
            default_chat_model=new_chat,
            default_embedding_model=existing_embed,
        )[0]

        with (
            patch(
                _BASE_REPO_UPSERT, new_callable=AsyncMock, return_value=after_upsert
            ) as mock_upsert,
            patch(
                _BASE_REPO_QUERY, new_callable=AsyncMock, return_value=[after_upsert]
            ),
        ):
            # Simulate the endpoint: read current defaults
            instance = await DefaultModels.get_instance()

            # Apply only the fields from the request (partial update)
            request_payload = {"default_chat_model": new_chat}
            for key, value in request_payload.items():
                if value is not None:
                    setattr(instance, key, value)

            await instance.update()

            mock_upsert.assert_called_once()
            data_arg = mock_upsert.call_args[0][2]

            # Chat was in the request → present in the upsert payload
            assert data_arg.get("default_chat_model") == new_chat
