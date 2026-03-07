"""
Unit tests for the Provider Adapter Framework (E31-S2).

Tests cover:
- base.py: NormalizedTable, NormalizedExtractionResult, ProviderError, ExtractionProvider
- DoclingAdapter: provider_id, capabilities, import error handling
- MinerUAdapter: provider_id, MINERU_ENABLED gate, import error handling
- ProviderRegistry: register, get_provider, list_providers, set_default, get_default
- normalizer.py: normalize_html_table, normalize_markdown_table
- Adapter isolation: ProviderError does NOT propagate as RuntimeError

Story: E31-S2 Provider Adapter Framework
"""

import os
import sys
from typing import Dict, List
from unittest.mock import MagicMock, patch

import pytest

from open_notebook.extractors.providers import ProviderRegistry
from open_notebook.extractors.providers.base import (
    ExtractionProvider,
    NormalizedExtractionResult,
    NormalizedTable,
    ProviderError,
    TableBBox,
)
from open_notebook.extractors.providers.docling_adapter import DoclingAdapter
from open_notebook.extractors.providers.mineru_adapter import MinerUAdapter
from open_notebook.extractors.providers.normalizer import (
    normalize_html_table,
    normalize_markdown_table,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SIMPLE_HTML = (
    "<table>"
    "<thead><tr><th>Name</th><th>Value</th></tr></thead>"
    "<tbody><tr><td>alpha</td><td>1</td></tr>"
    "<tr><td>beta</td><td>2</td></tr></tbody>"
    "</table>"
)

SIMPLE_MARKDOWN = "| Name | Value |\n| --- | --- |\n| alpha | 1 |\n| beta | 2 |"


# ---------------------------------------------------------------------------
# base.py tests
# ---------------------------------------------------------------------------


class TestNormalizedTable:
    """NormalizedTable dataclass field tests."""

    def test_normalized_table_fields(self):
        """NormalizedTable has all required fields."""
        tbl = NormalizedTable(
            table_index=0,
            page=1,
            row_count=3,
            col_count=2,
            columns=["A", "B"],
            html="<table></table>",
            markdown="| A | B |",
        )
        assert tbl.table_index == 0
        assert tbl.page == 1
        assert tbl.row_count == 3
        assert tbl.col_count == 2
        assert tbl.columns == ["A", "B"]
        assert tbl.html == "<table></table>"
        assert tbl.markdown == "| A | B |"
        assert tbl.csv is None
        assert tbl.bbox is None

    def test_normalized_table_with_bbox(self):
        """NormalizedTable accepts a TableBBox."""
        bbox = TableBBox(x=10.0, y=20.0, width=100.0, height=50.0, page=1)
        tbl = NormalizedTable(
            table_index=0,
            page=1,
            row_count=1,
            col_count=1,
            columns=["X"],
            html="<table></table>",
            markdown="| X |",
            bbox=bbox,
        )
        assert tbl.bbox is not None
        assert tbl.bbox.x == 10.0
        assert tbl.bbox.page == 1

    def test_normalized_table_with_csv(self):
        """NormalizedTable accepts csv string."""
        tbl = NormalizedTable(
            table_index=0,
            page=2,
            row_count=1,
            col_count=2,
            columns=["A", "B"],
            html="<table></table>",
            markdown="| A | B |",
            csv="A,B\n1,2\n",
        )
        assert tbl.csv == "A,B\n1,2\n"


class TestNormalizedExtractionResult:
    """NormalizedExtractionResult dataclass field tests."""

    def test_normalized_extraction_result_fields(self):
        """NormalizedExtractionResult has all required fields."""
        result = NormalizedExtractionResult(provider_id="docling")
        assert result.provider_id == "docling"
        assert result.tables == []
        assert result.extraction_time_ms == 0
        assert result.warnings == []

    def test_normalized_extraction_result_with_tables(self):
        """NormalizedExtractionResult stores tables list."""
        tbl = NormalizedTable(
            table_index=0,
            page=1,
            row_count=2,
            col_count=2,
            columns=["C1", "C2"],
            html="<table></table>",
            markdown="| C1 | C2 |",
        )
        result = NormalizedExtractionResult(
            provider_id="test",
            tables=[tbl],
            extraction_time_ms=500,
            warnings=["minor issue"],
        )
        assert len(result.tables) == 1
        assert result.extraction_time_ms == 500
        assert result.warnings == ["minor issue"]


class TestProviderError:
    """ProviderError exception tests."""

    def test_provider_error_message(self):
        """ProviderError formats message with provider_id prefix."""
        err = ProviderError("docling", "something went wrong")
        assert "[docling] something went wrong" in str(err)
        assert err.provider_id == "docling"
        assert err.message == "something went wrong"
        assert err.original is None

    def test_provider_error_with_original(self):
        """ProviderError stores original exception."""
        original = RuntimeError("underlying error")
        err = ProviderError("mineru", "wrapped", original=original)
        assert err.original is original
        assert isinstance(err, Exception)

    def test_provider_error_is_exception(self):
        """ProviderError is catchable as Exception."""
        with pytest.raises(Exception):
            raise ProviderError("test", "boom")


class TestExtractionProviderProtocol:
    """ExtractionProvider Protocol runtime_checkable tests."""

    def test_protocol_isinstance_check(self):
        """Concrete class satisfying the protocol passes isinstance."""

        class FakeProvider:
            @property
            def provider_id(self) -> str:
                return "fake"

            def extract(self, pdf_path: str, *, pipeline_logger=None):
                return NormalizedExtractionResult(provider_id="fake")

            def supports_table_extraction(self) -> bool:
                return True

            def get_field_confidence(self) -> Dict[str, float]:
                return {}

            def cleanup(self) -> None:
                pass

        provider = FakeProvider()
        assert isinstance(provider, ExtractionProvider)

    def test_docling_adapter_isinstance(self):
        """DoclingAdapter satisfies ExtractionProvider protocol."""
        adapter = DoclingAdapter()
        assert isinstance(adapter, ExtractionProvider)

    def test_mineru_adapter_isinstance(self):
        """MinerUAdapter satisfies ExtractionProvider protocol."""
        adapter = MinerUAdapter()
        assert isinstance(adapter, ExtractionProvider)


# ---------------------------------------------------------------------------
# DoclingAdapter tests
# ---------------------------------------------------------------------------


class TestDoclingAdapter:
    """DoclingAdapter unit tests."""

    def test_docling_adapter_provider_id(self):
        """DoclingAdapter.provider_id == 'docling'."""
        adapter = DoclingAdapter()
        assert adapter.provider_id == "docling"

    def test_docling_adapter_supports_table_extraction(self):
        """DoclingAdapter.supports_table_extraction() returns True."""
        adapter = DoclingAdapter()
        assert adapter.supports_table_extraction() is True

    def test_docling_adapter_get_field_confidence(self):
        """DoclingAdapter.get_field_confidence() returns empty dict."""
        adapter = DoclingAdapter()
        assert adapter.get_field_confidence() == {}

    def test_docling_adapter_import_error(self):
        """When docling not importable, extract() raises ProviderError."""
        adapter = DoclingAdapter()

        with patch.dict(
            sys.modules, {"docling": None, "docling.document_converter": None}
        ):
            with pytest.raises(ProviderError) as exc_info:
                adapter.extract("/fake/path.pdf")

        assert exc_info.value.provider_id == "docling"

    def test_docling_adapter_returns_normalized_result(self):
        """DoclingAdapter.extract() returns NormalizedExtractionResult on success."""
        adapter = DoclingAdapter()

        # Build mock DataFrame
        import pandas as pd

        mock_df = pd.DataFrame(
            {"Col A": ["val1", "val2"], "Hazard Status": ["ACM", "NAD"]}
        )

        mock_table = MagicMock()
        mock_table.export_to_dataframe.return_value = mock_df
        mock_table.export_to_html.return_value = "<table><tr><td>x</td></tr></table>"
        mock_table.prov = [MagicMock(page_no=3)]

        mock_doc = MagicMock()
        mock_doc.tables = [mock_table]

        mock_result = MagicMock()
        mock_result.document = mock_doc

        mock_converter_instance = MagicMock()
        mock_converter_instance.convert.return_value = mock_result

        mock_docling_module = MagicMock()
        mock_docling_module.DocumentConverter = MagicMock(
            return_value=mock_converter_instance
        )

        mock_pipeline_options = MagicMock()

        with patch.dict(
            sys.modules,
            {
                "docling": MagicMock(),
                "docling.document_converter": mock_docling_module,
                "docling.datamodel": MagicMock(),
                "docling.datamodel.base_models": MagicMock(),
                "docling.datamodel.pipeline_options": MagicMock(),
            },
        ):
            with patch(
                "open_notebook.extractors.providers.docling_adapter.DoclingAdapter._run_extraction"
            ) as mock_run:
                mock_run.return_value = NormalizedExtractionResult(
                    provider_id="docling",
                    tables=[
                        NormalizedTable(
                            table_index=0,
                            page=3,
                            row_count=2,
                            col_count=2,
                            columns=["Col A", "Hazard Status"],
                            html="<table></table>",
                            markdown="| Col A | Hazard Status |",
                            csv="Col A,Hazard Status\nval1,ACM\nval2,NAD\n",
                        )
                    ],
                    extraction_time_ms=200,
                )
                result = adapter.extract("/fake/path.pdf")

        assert isinstance(result, NormalizedExtractionResult)
        assert result.provider_id == "docling"
        assert len(result.tables) == 1
        assert result.tables[0].page == 3

    def test_docling_adapter_wraps_runtime_error_as_provider_error(self):
        """DoclingAdapter wraps non-ImportError exceptions as ProviderError."""
        adapter = DoclingAdapter()

        with patch.object(
            adapter,
            "_run_extraction",
            side_effect=RuntimeError("unexpected crash"),
        ):
            with pytest.raises(ProviderError) as exc_info:
                adapter.extract("/fake/path.pdf")

        assert exc_info.value.provider_id == "docling"
        assert isinstance(exc_info.value.original, RuntimeError)


# ---------------------------------------------------------------------------
# MinerUAdapter tests
# ---------------------------------------------------------------------------


class TestMinerUAdapter:
    """MinerUAdapter unit tests."""

    def test_mineru_adapter_provider_id(self):
        """MinerUAdapter.provider_id == 'mineru'."""
        adapter = MinerUAdapter()
        assert adapter.provider_id == "mineru"

    def test_mineru_adapter_supports_table_extraction(self):
        """MinerUAdapter.supports_table_extraction() returns True."""
        adapter = MinerUAdapter()
        assert adapter.supports_table_extraction() is True

    def test_mineru_adapter_get_field_confidence(self):
        """MinerUAdapter.get_field_confidence() returns empty dict."""
        adapter = MinerUAdapter()
        assert adapter.get_field_confidence() == {}

    def test_mineru_adapter_disabled_env_var(self):
        """When MINERU_ENABLED != 'true', extract() raises ProviderError."""
        adapter = MinerUAdapter()

        for disabled_val in ("false", "0", "", "FALSE", "no"):
            with patch.dict(os.environ, {"MINERU_ENABLED": disabled_val}, clear=False):
                with pytest.raises(ProviderError) as exc_info:
                    adapter.extract("/fake/path.pdf")
            assert exc_info.value.provider_id == "mineru"
            assert "MINERU_ENABLED" in exc_info.value.message

    def test_mineru_adapter_disabled_by_default(self):
        """When MINERU_ENABLED is absent, extract() raises ProviderError."""
        adapter = MinerUAdapter()
        env_without_mineru = {
            k: v for k, v in os.environ.items() if k != "MINERU_ENABLED"
        }
        with patch.dict(os.environ, env_without_mineru, clear=True):
            with pytest.raises(ProviderError) as exc_info:
                adapter.extract("/fake/path.pdf")
        assert exc_info.value.provider_id == "mineru"

    def test_mineru_adapter_import_error(self):
        """When mineru not importable, extract() raises ProviderError."""
        adapter = MinerUAdapter()

        with patch.dict(os.environ, {"MINERU_ENABLED": "true"}):
            with patch.dict(sys.modules, {"mineru": None}):
                with pytest.raises(ProviderError) as exc_info:
                    adapter.extract("/fake/path.pdf")

        assert exc_info.value.provider_id == "mineru"

    def test_mineru_adapter_enabled_returns_result(self):
        """When MINERU_ENABLED=true and mineru is mocked, extract() returns result."""
        adapter = MinerUAdapter()

        mock_result = MagicMock()
        mock_result.tables = []

        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result

        mock_mineru_module = MagicMock()
        mock_mineru_module.MinerUDocumentConverter.return_value = mock_converter

        with patch.dict(os.environ, {"MINERU_ENABLED": "true"}):
            with patch.dict(sys.modules, {"mineru": mock_mineru_module}):
                result = adapter.extract("/fake/path.pdf")

        assert isinstance(result, NormalizedExtractionResult)
        assert result.provider_id == "mineru"

    def test_mineru_adapter_empty_result_with_warning(self):
        """MinerU result with no table attributes produces warning."""
        adapter = MinerUAdapter()

        # result object with no tables/pages attribute
        mock_result = MagicMock(spec=[])  # empty spec — no attributes

        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result

        mock_mineru_module = MagicMock()
        mock_mineru_module.MinerUDocumentConverter.return_value = mock_converter

        with patch.dict(os.environ, {"MINERU_ENABLED": "true"}):
            with patch.dict(sys.modules, {"mineru": mock_mineru_module}):
                result = adapter.extract("/fake/path.pdf")

        assert result.tables == []
        assert len(result.warnings) > 0


# ---------------------------------------------------------------------------
# ProviderRegistry tests
# ---------------------------------------------------------------------------


class TestProviderRegistry:
    """ProviderRegistry unit tests using a fresh instance."""

    def _make_registry(self) -> ProviderRegistry:
        """Return a fresh registry for isolated testing."""
        return ProviderRegistry()

    def _make_provider(self, pid: str) -> ExtractionProvider:
        """Create a minimal fake provider with the given ID."""

        class _Provider:
            def __init__(self, pid: str):
                self._pid = pid

            @property
            def provider_id(self) -> str:
                return self._pid

            def extract(self, pdf_path, *, pipeline_logger=None):
                return NormalizedExtractionResult(provider_id=self._pid)

            def supports_table_extraction(self) -> bool:
                return True

            def get_field_confidence(self) -> Dict[str, float]:
                return {}

            def cleanup(self) -> None:
                pass

        return _Provider(pid)

    def test_registry_register_and_get(self):
        """register() + get_provider() round-trip."""
        registry = self._make_registry()
        provider = self._make_provider("alpha")
        registry.register(provider)
        retrieved = registry.get_provider("alpha")
        assert retrieved.provider_id == "alpha"

    def test_registry_list_providers(self):
        """list_providers() returns sorted list of IDs."""
        registry = self._make_registry()
        registry.register(self._make_provider("zebra"))
        registry.register(self._make_provider("apple"))
        registry.register(self._make_provider("mango"))
        ids = registry.list_providers()
        assert ids == ["apple", "mango", "zebra"]

    def test_registry_unknown_provider_raises_keyerror(self):
        """get_provider('unknown') raises KeyError."""
        registry = self._make_registry()
        with pytest.raises(KeyError):
            registry.get_provider("unknown")

    def test_registry_set_default(self):
        """set_default() + get_default() round-trip."""
        registry = self._make_registry()
        registry.register(self._make_provider("docling"))
        registry.register(self._make_provider("mineru"))
        registry.set_default("mineru")

        with patch.dict(os.environ, {}, clear=False):
            # Remove ACM_EXTRACTION_PROVIDER if set
            env = {
                k: v for k, v in os.environ.items() if k != "ACM_EXTRACTION_PROVIDER"
            }
            with patch.dict(os.environ, env, clear=True):
                default = registry.get_default()
        assert default.provider_id == "mineru"

    def test_registry_set_default_unknown_raises_keyerror(self):
        """set_default() with unregistered ID raises KeyError."""
        registry = self._make_registry()
        with pytest.raises(KeyError):
            registry.set_default("nonexistent")

    def test_registry_default_env_var(self):
        """get_default() respects ACM_EXTRACTION_PROVIDER env var."""
        registry = self._make_registry()
        registry.register(self._make_provider("docling"))
        registry.register(self._make_provider("mineru"))

        with patch.dict(os.environ, {"ACM_EXTRACTION_PROVIDER": "mineru"}):
            default = registry.get_default()

        assert default.provider_id == "mineru"

    def test_registry_default_env_var_missing_falls_back_to_internal(self):
        """get_default() falls back to internal _default_id when env var absent."""
        registry = self._make_registry()
        registry.register(self._make_provider("docling"))
        registry.set_default("docling")

        env_without = {
            k: v for k, v in os.environ.items() if k != "ACM_EXTRACTION_PROVIDER"
        }
        with patch.dict(os.environ, env_without, clear=True):
            default = registry.get_default()

        assert default.provider_id == "docling"

    def test_registry_list_providers_empty(self):
        """list_providers() returns empty list when no providers registered."""
        registry = self._make_registry()
        assert registry.list_providers() == []


# ---------------------------------------------------------------------------
# normalizer.py tests
# ---------------------------------------------------------------------------


class TestNormalizeHtmlTable:
    """normalize_html_table() unit tests."""

    def test_normalize_html_table_basic(self):
        """normalize_html_table() parses simple HTML table."""
        result = normalize_html_table(SIMPLE_HTML, table_index=0, page=2)
        assert isinstance(result, NormalizedTable)
        assert result.table_index == 0
        assert result.page == 2
        assert result.col_count == 2
        assert result.columns == ["Name", "Value"]
        assert result.row_count == 2
        assert result.html == SIMPLE_HTML
        assert "Name" in result.markdown

    def test_normalize_html_table_invalid_raises_valueerror(self):
        """normalize_html_table() raises ValueError for non-table HTML."""
        with pytest.raises(ValueError):
            normalize_html_table("<p>Not a table</p>")

    def test_normalize_html_table_default_params(self):
        """normalize_html_table() uses default table_index=0 and page=-1."""
        result = normalize_html_table(SIMPLE_HTML)
        assert result.table_index == 0
        assert result.page == -1

    def test_normalize_html_table_csv_is_none(self):
        """normalize_html_table() leaves csv as None (not implemented)."""
        result = normalize_html_table(SIMPLE_HTML)
        assert result.csv is None


class TestNormalizeMarkdownTable:
    """normalize_markdown_table() unit tests."""

    def test_normalize_markdown_table_basic(self):
        """normalize_markdown_table() parses pipe-delimited markdown."""
        result = normalize_markdown_table(SIMPLE_MARKDOWN, table_index=1, page=5)
        assert isinstance(result, NormalizedTable)
        assert result.table_index == 1
        assert result.page == 5
        assert result.col_count == 2
        assert result.columns == ["Name", "Value"]
        assert result.row_count == 2
        assert result.markdown == SIMPLE_MARKDOWN
        assert "<table>" in result.html

    def test_normalize_markdown_table_invalid_raises_valueerror(self):
        """normalize_markdown_table() raises ValueError for empty/invalid input."""
        with pytest.raises(ValueError):
            normalize_markdown_table("")

    def test_normalize_markdown_table_separator_only_raises_valueerror(self):
        """normalize_markdown_table() raises ValueError when only separators present."""
        with pytest.raises(ValueError):
            normalize_markdown_table("| --- | --- |\n| --- | --- |")

    def test_normalize_markdown_table_default_params(self):
        """normalize_markdown_table() uses default table_index=0 and page=-1."""
        result = normalize_markdown_table(SIMPLE_MARKDOWN)
        assert result.table_index == 0
        assert result.page == -1

    def test_normalize_markdown_table_csv_is_none(self):
        """normalize_markdown_table() leaves csv as None."""
        result = normalize_markdown_table(SIMPLE_MARKDOWN)
        assert result.csv is None


# ---------------------------------------------------------------------------
# Adapter isolation tests
# ---------------------------------------------------------------------------


class TestAdapterIsolation:
    """Verify ProviderError boundary — no RuntimeError escapes adapters."""

    def test_docling_provider_error_does_not_propagate_as_runtime_error(self):
        """DoclingAdapter exception → ProviderError, NOT RuntimeError."""
        adapter = DoclingAdapter()

        with patch.object(
            adapter,
            "_run_extraction",
            side_effect=RuntimeError("crash"),
        ):
            with pytest.raises(ProviderError):
                adapter.extract("/path.pdf")

        # If we reach here, RuntimeError was correctly caught and wrapped

    def test_mineru_provider_error_does_not_propagate_as_runtime_error(self):
        """MinerUAdapter exception → ProviderError, NOT RuntimeError."""
        adapter = MinerUAdapter()

        with patch.dict(os.environ, {"MINERU_ENABLED": "true"}):
            with patch.object(
                adapter,
                "_run_extraction",
                side_effect=RuntimeError("crash"),
            ):
                with pytest.raises(ProviderError):
                    adapter.extract("/path.pdf")

    def test_provider_error_is_not_runtime_error(self):
        """ProviderError is not a subclass of RuntimeError."""
        assert not issubclass(ProviderError, RuntimeError)

    def test_docling_import_error_is_provider_error(self):
        """ImportError inside DoclingAdapter surfaces as ProviderError."""
        adapter = DoclingAdapter()

        # Simulate ImportError by patching builtins.__import__
        original_import = (
            __builtins__.__import__
            if hasattr(__builtins__, "__import__")
            else __import__
        )

        with patch.dict(
            sys.modules, {"docling": None, "docling.document_converter": None}
        ):
            with pytest.raises(ProviderError) as exc_info:
                adapter.extract("/fake/path.pdf")

        assert exc_info.value.provider_id == "docling"
        # Must be ProviderError, not ImportError
        assert not isinstance(exc_info.value, ImportError)
