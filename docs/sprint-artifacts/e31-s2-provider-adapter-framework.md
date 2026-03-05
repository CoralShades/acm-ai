# Tech Spec: E31-S2 — Provider Adapter Framework

**Sprint:** V3-3
**Story Points:** 3
**Risk:** MEDIUM
**Type:** Backend
**Status:** drafted

---

## 1. Problem Statement

The current Docling table extraction is tightly coupled to `commands/source_commands.py` as an
inline async function (`_extract_tables_with_docling`). This creates three problems:

1. **No abstraction boundary.** Adding a second extractor (MinerU 2.x) requires duplicating
   pipeline plumbing, error handling, and storage logic instead of sharing a common interface.

2. **Inconsistent output schemas.** Docling produces a dict with `table_index`, `page`, `rows`,
   `columns`, `csv`, `markdown`, `html` keys. A future MinerU adapter will produce different
   keys unless they are normalised at the boundary.

3. **Provider failures can escalate.** Without explicit error containment at the adapter
   boundary, a crash inside a provider call can surface as an unhandled exception in
   `process_source_command`, which surreal-commands will retry unnecessarily.

This story creates a thin, stable adapter layer so that:
- `source_commands.py` calls `registry.get_provider(provider_id).extract(pdf_path)` and
  receives a `NormalizedExtractionResult` regardless of the underlying provider.
- Each adapter isolates its own import errors and runtime exceptions, raising only
  `ProviderError` to the pipeline.
- Adding a third provider (e.g., pymupdf-tables) requires only a new adapter file.

### Relationship to Existing Code

The existing `ConsultantParser` ABC in `open_notebook/extractors/parsers/base.py` handles
*LLM-side* record extraction from already-extracted text. The new `ExtractionProvider` protocol
is a lower-level, *document-side* interface that handles PDF-to-table conversion. These two
layers are complementary and do not overlap.

The existing `StrategyRegistry` in `open_notebook/extractors/strategy_registry.py` manages
extraction *strategies* (routing decisions). The new `ProviderRegistry` manages concrete
*provider implementations*. They operate at different levels of abstraction.

---

## 2. Acceptance Criteria

### AC1 — ExtractionProvider Protocol

A `typing.Protocol` class in `base.py` defining the three required methods:

| Method | Signature | Description |
|--------|-----------|-------------|
| `provider_id` | `@property str` | Stable string key (e.g., `"docling"`, `"mineru"`) |
| `extract` | `(pdf_path: str, ...) -> NormalizedExtractionResult` | Synchronous extraction |
| `supports_table_extraction` | `() -> bool` | Capability flag — must return `True` at minimum |
| `get_field_confidence` | `() -> Dict[str, float]` | Per-field confidence map; return `{}` if unsupported |

**Implementation notes:**
- Use `typing.Protocol` with `runtime_checkable=True` so `isinstance` works in tests.
- `extract` may accept keyword-only args `pipeline_logger: Optional[PipelineLogger] = None`
  to allow the caller to pass observability hooks without coupling the protocol to PipelineLogger.
- Do NOT use `ABC`/`abstractmethod` — the Protocol approach allows duck-typing and avoids
  forcing subclasses to call `super()`.

### AC2 — NormalizedExtractionResult Schema

A `dataclass` (or Pydantic `BaseModel`) defined in `base.py`:

```
NormalizedExtractionResult
  provider_id: str
  tables: List[NormalizedTable]
  extraction_time_ms: int          # wall-clock ms, for observability
  warnings: List[str]              # non-fatal issues encountered

NormalizedTable
  table_index: int                 # 0-based index within the document
  page: int                        # 1-based page number (-1 if unknown)
  row_count: int
  col_count: int
  columns: List[str]               # column header strings
  html: str                        # full HTML <table> string
  markdown: str                    # pipe-delimited markdown table
  csv: Optional[str]               # CSV text; None if not producible
  bbox: Optional[TableBBox]        # bounding box if provider supports it

TableBBox
  x: float
  y: float
  width: float
  height: float
  page: int
```

**Implementation notes:**
- Use `@dataclass(frozen=False)` for mutability during construction.
- Pydantic is also acceptable if consistency with existing domain models is preferred;
  prefer dataclass for speed (no validation overhead in extraction hot path).
- `NormalizedTable.html` is the authoritative field for downstream storage in
  `acm_table_section.raw_html`. `markdown` is used by the LLM extraction path.
- `TableBBox` mirrors the existing `ACMRecord.table_bbox` dict shape but as a typed object.

### AC3 — DoclingAdapter

A class in `docling_adapter.py` that implements `ExtractionProvider` and wraps the logic
currently in `_extract_tables_with_docling` in `source_commands.py`.

**Key requirements:**

1. The adapter must be importable even if `docling` is not installed. Wrap all `from docling ...`
   imports inside the `extract()` method body (deferred import pattern), guarded by
   `try/except ImportError` that raises `ProviderError`.

2. Replicate the existing normalization pipeline inside `extract()`:
   - Fix split sample numbers: `re.sub(r"(\d+)-\s+(\d+)", r"\1-\2", str(v))`
   - Strip `"Asbestos "` prefix from hazard/status columns

3. Convert Docling output to `NormalizedTable`:
   - `html`: `table.export_to_html(doc=doc)`
   - `markdown`: `df.to_markdown(index=False)` (use empty string if pandas unavailable)
   - `csv`: `df.to_csv(index=False)`
   - `page`: `table.prov[0].page_no if table.prov else -1`
   - `bbox`: `None` (Docling provides bounding boxes via `table.prov[0].bbox` but this is
     out of scope for this story — leave as `None` and add a `TODO` comment)

4. Catch ALL exceptions from Docling, log them with `logger.warning`, and re-raise as
   `ProviderError(provider_id="docling", message=str(e), original=e)`.

5. `supports_table_extraction()` returns `True`.

6. `get_field_confidence()` returns `{}` (Docling does not produce field-level confidence).

### AC4 — MinerUAdapter

A class in `mineru_adapter.py` that implements `ExtractionProvider` and wraps MinerU 2.x.

**Key requirements:**

1. Deferred import: all `from mineru ...` imports inside `extract()`, guarded by
   `try/except ImportError` raising `ProviderError`.

2. The MinerU 2.x API to use:
   ```python
   from mineru import MinerUDocumentConverter
   converter = MinerUDocumentConverter()
   result = converter.convert(pdf_path)
   ```
   The shape of `result` must be validated at runtime — if it doesn't yield table objects,
   return an empty `NormalizedExtractionResult` with a warning entry.

3. Since MinerU 2.x output schema is not fully documented in this codebase yet, the adapter
   must include a `_parse_mineru_result(result) -> List[NormalizedTable]` private method.
   This method should:
   - Attempt to iterate `result.pages` or `result.tables` (whichever exists).
   - For each table-like object, attempt to produce `html`, `markdown`, `csv`.
   - If a table fails to convert, log a warning and skip it (don't fail the whole extraction).

4. `supports_table_extraction()` returns `True`.

5. `get_field_confidence()` returns `{}`.

6. Controlled by environment variable `MINERU_ENABLED` (string `"true"` / `"false"`).
   If `MINERU_ENABLED != "true"`, `extract()` must raise `ProviderError` immediately with
   message `"MinerU disabled via MINERU_ENABLED env var"`.

### AC5 — Result Normalizer

A module-level function (or class method) in `base.py` or a separate
`open_notebook/extractors/providers/normalizer.py` that converts either:

- An HTML `<table>` string to a `NormalizedTable` (for MinerU HTML output)
- A structured markdown table string to a `NormalizedTable` (for any provider that
  produces markdown-first output)

The normalizer exists so adapters that produce HTML-first or markdown-first output both
produce the same `NormalizedTable` shape. It is NOT required to re-implement
`normalize_docling_text()` — that function remains in
`open_notebook/extractors/normalizers/content.py` and is called before LLM extraction.

**Function signatures:**

```python
def normalize_html_table(
    html: str,
    table_index: int = 0,
    page: int = -1,
) -> NormalizedTable: ...

def normalize_markdown_table(
    markdown: str,
    table_index: int = 0,
    page: int = -1,
) -> NormalizedTable: ...
```

Each function parses the input, extracts columns and row counts, and fills all
`NormalizedTable` fields. If parsing fails, raise `ValueError` with a descriptive message.

### AC6 — Provider Registry

A `ProviderRegistry` class in `__init__.py` that supports:

| Method | Signature | Description |
|--------|-----------|-------------|
| `register` | `(provider: ExtractionProvider) -> None` | Register a provider instance |
| `get_provider` | `(provider_id: str) -> ExtractionProvider` | Look up by ID; raises `KeyError` if missing |
| `list_providers` | `() -> List[str]` | Return sorted list of registered provider IDs |
| `get_default` | `() -> ExtractionProvider` | Return the default provider |
| `set_default` | `(provider_id: str) -> None` | Set the default by ID |

**Global singleton pattern:**

```python
# In __init__.py
_registry = ProviderRegistry()

def get_provider_registry() -> ProviderRegistry:
    return _registry
```

This allows `source_commands.py` to import only `get_provider_registry` without
constructing a registry itself.

**Default provider selection:**

The default provider is controlled by environment variable `ACM_EXTRACTION_PROVIDER`
(default: `"docling"`). `get_default()` reads this env var each time it is called so
that tests can swap providers without re-importing the module.

**Auto-registration on import:**

The module `__init__.py` should auto-register both `DoclingAdapter` and `MinerUAdapter`
instances at import time, so callers never need to register manually in production code.
The registration must not fail even if the underlying libraries are not installed
(adapters raise `ProviderError` only at `extract()` time, not at construction time).

### AC7 — Unit Tests

File: `tests/test_provider_adapters.py`

Required test cases:

| Test | Description |
|------|-------------|
| `test_normalized_table_fields` | NormalizedTable has all required fields |
| `test_normalized_extraction_result_fields` | NormalizedExtractionResult has all required fields |
| `test_docling_adapter_provider_id` | DoclingAdapter.provider_id == "docling" |
| `test_docling_adapter_supports_table_extraction` | Returns True |
| `test_docling_adapter_get_field_confidence` | Returns empty dict |
| `test_docling_adapter_import_error` | When docling not importable, extract() raises ProviderError |
| `test_mineru_adapter_provider_id` | MinerUAdapter.provider_id == "mineru" |
| `test_mineru_adapter_disabled_env_var` | When MINERU_ENABLED != "true", extract() raises ProviderError |
| `test_mineru_adapter_import_error` | When mineru not importable, extract() raises ProviderError |
| `test_registry_register_and_get` | register() + get_provider() round-trip |
| `test_registry_list_providers` | list_providers() returns sorted list |
| `test_registry_unknown_provider_raises_keyerror` | get_provider("unknown") raises KeyError |
| `test_registry_set_default` | set_default() + get_default() round-trip |
| `test_registry_default_env_var` | get_default() respects ACM_EXTRACTION_PROVIDER env var |
| `test_normalize_html_table_basic` | normalize_html_table() parses simple HTML table |
| `test_normalize_markdown_table_basic` | normalize_markdown_table() parses pipe-delimited markdown |

All tests use `unittest.mock.patch` or `pytest.MonkeyPatch` to simulate missing imports
without requiring Docling or MinerU to be installed in the test environment.

### AC8 — Adapter Isolation

A provider failure MUST NOT crash the pipeline. The contract is:

1. Each adapter wraps its entire `extract()` body in `try/except Exception as e` and
   re-raises only `ProviderError`.
2. `ProviderError` is a custom exception class (defined in `base.py`) with fields:
   - `provider_id: str`
   - `message: str`
   - `original: Optional[Exception]` (the wrapped exception)
3. `source_commands.py` catches `ProviderError` at the call site and logs it as
   `logger.error(...)` without re-raising — matching the existing non-fatal pattern in
   `_extract_tables_with_docling`.
4. No change to the retry contract in `strategy_registry.py` is required for this story.

---

## 3. File Changes Table

| File | Action | Description |
|------|--------|-------------|
| `open_notebook/extractors/providers/__init__.py` | CREATE | ProviderRegistry class + auto-registration + `get_provider_registry()` |
| `open_notebook/extractors/providers/base.py` | CREATE | ExtractionProvider Protocol, NormalizedTable, NormalizedExtractionResult, TableBBox, ProviderError dataclasses/Protocol |
| `open_notebook/extractors/providers/docling_adapter.py` | CREATE | DoclingAdapter wrapping existing `_extract_tables_with_docling` logic |
| `open_notebook/extractors/providers/mineru_adapter.py` | CREATE | MinerUAdapter wrapping MinerU 2.x DocumentConverter |
| `open_notebook/extractors/providers/normalizer.py` | CREATE | `normalize_html_table()` and `normalize_markdown_table()` utility functions |
| `commands/source_commands.py` | MODIFY | Replace inline `_extract_tables_with_docling` call with `get_provider_registry().get_default().extract(...)` |
| `tests/test_provider_adapters.py` | CREATE | Unit tests per AC7 |

### Files NOT Modified

| File | Reason |
|------|--------|
| `open_notebook/extractors/normalizers/content.py` | Remains unchanged; operates on Docling text, not table objects |
| `open_notebook/extractors/strategy_registry.py` | Operates on extraction strategies, not PDF providers |
| `open_notebook/extractors/parsers/base.py` | ConsultantParser is LLM-side; no overlap |
| `open_notebook/extractors/pipeline_events.py` | StageId.DOCLING_EXTRACTION still used; no rename needed |

---

## 4. Implementation Details

### 4.1 `open_notebook/extractors/providers/base.py`

```python
"""
Provider Adapter Framework — base types.

Story: E31-S2 Provider Adapter Framework
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, runtime_checkable
from typing import Protocol


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

@dataclass
class TableBBox:
    """Bounding box coordinates for a table within a PDF page."""
    x: float
    y: float
    width: float
    height: float
    page: int


@dataclass
class NormalizedTable:
    """Provider-agnostic representation of a single extracted table."""
    table_index: int
    page: int                          # 1-based; -1 if unknown
    row_count: int
    col_count: int
    columns: List[str]
    html: str
    markdown: str
    csv: Optional[str] = None
    bbox: Optional[TableBBox] = None


@dataclass
class NormalizedExtractionResult:
    """Container returned by every ExtractionProvider.extract() call."""
    provider_id: str
    tables: List[NormalizedTable] = field(default_factory=list)
    extraction_time_ms: int = 0
    warnings: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Error type
# ---------------------------------------------------------------------------

class ProviderError(Exception):
    """Raised by an adapter when extraction fails.

    Callers should catch ProviderError and handle non-fatally — the adapter
    guarantees that no other exception type escapes extract().
    """
    def __init__(
        self,
        provider_id: str,
        message: str,
        original: Optional[Exception] = None,
    ) -> None:
        super().__init__(f"[{provider_id}] {message}")
        self.provider_id = provider_id
        self.message = message
        self.original = original


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class ExtractionProvider(Protocol):
    """Protocol for PDF extraction providers.

    Adapters implement this protocol to participate in the ProviderRegistry.
    All implementations must be importable even when the underlying library
    is not installed; ProviderError is raised at extract() time only.
    """

    @property
    def provider_id(self) -> str:
        """Stable string identifier for this provider (e.g. 'docling')."""
        ...

    def extract(
        self,
        pdf_path: str,
        *,
        pipeline_logger=None,  # Optional[PipelineLogger] — avoid import cycle
    ) -> NormalizedExtractionResult:
        """Extract tables from a PDF file.

        Args:
            pdf_path: Absolute path to the PDF file.
            pipeline_logger: Optional PipelineLogger for observability hooks.

        Returns:
            NormalizedExtractionResult — always returned even on partial failure.

        Raises:
            ProviderError: If extraction cannot proceed at all.
        """
        ...

    def supports_table_extraction(self) -> bool:
        """Return True if this provider can extract structured tables."""
        ...

    def get_field_confidence(self) -> Dict[str, float]:
        """Return per-field confidence map; empty dict if unsupported."""
        ...
```

### 4.2 `open_notebook/extractors/providers/normalizer.py`

```python
"""
Result normalizer: converts HTML or markdown table strings to NormalizedTable.

Story: E31-S2 Provider Adapter Framework
"""
from __future__ import annotations

import re
from typing import List

from open_notebook.extractors.providers.base import NormalizedTable


def normalize_html_table(
    html: str,
    table_index: int = 0,
    page: int = -1,
) -> NormalizedTable:
    """Parse an HTML <table> string into a NormalizedTable.

    Uses a lightweight regex approach rather than a full HTML parser to avoid
    adding a new dependency. Handles colspan/rowspan by ignoring them for the
    purposes of column counting.

    Args:
        html: Full HTML <table>...</table> string.
        table_index: 0-based index within the source document.
        page: 1-based page number; -1 if unknown.

    Returns:
        NormalizedTable with html, markdown, and row/col counts populated.
        csv field is left None (conversion from HTML not implemented here).

    Raises:
        ValueError: If the HTML cannot be parsed as a table.
    """
    # Extract header row: first <tr> containing <th> elements
    # Extract all rows: all <tr> elements
    # Count columns from header row or first data row
    # Build markdown from parsed cells
    ...


def normalize_markdown_table(
    markdown: str,
    table_index: int = 0,
    page: int = -1,
) -> NormalizedTable:
    """Parse a pipe-delimited markdown table into a NormalizedTable.

    Args:
        markdown: Markdown table string (may include separator row).
        table_index: 0-based index within the source document.
        page: 1-based page number; -1 if unknown.

    Returns:
        NormalizedTable with html, markdown, and row/col counts populated.

    Raises:
        ValueError: If the string doesn't contain a valid markdown table.
    """
    # Split lines, skip separator row (all dashes/colons/pipes)
    # Build columns from header row
    # Count rows
    # Generate a minimal HTML table from the parsed data
    ...
```

**Notes for implementer:**
- `normalize_html_table` can use `re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", html, re.I | re.S)`
  as a starting point, but must handle nested tags.
- Use Python's `html.parser.HTMLParser` if regex proves fragile on real Docling output.
- `normalize_markdown_table` should reuse the helper `_split_table_cells` pattern already
  established in `open_notebook/extractors/normalizers/content.py` (line 127-128) rather
  than reimplementing.

### 4.3 `open_notebook/extractors/providers/docling_adapter.py`

```python
"""
Docling extraction provider adapter.

Wraps the inline _extract_tables_with_docling logic from source_commands.py
and converts output to NormalizedExtractionResult.

Story: E31-S2 Provider Adapter Framework
"""
from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING, Dict, List, Optional

from loguru import logger

from open_notebook.extractors.providers.base import (
    NormalizedExtractionResult,
    NormalizedTable,
    ProviderError,
)

if TYPE_CHECKING:
    from open_notebook.extractors.pipeline_logger import PipelineLogger


class DoclingAdapter:
    """ExtractionProvider that wraps Docling's DocumentConverter.

    Docling is imported lazily inside extract() so that this class can be
    instantiated even when the docling package is not installed.
    """

    @property
    def provider_id(self) -> str:
        return "docling"

    def supports_table_extraction(self) -> bool:
        return True

    def get_field_confidence(self) -> Dict[str, float]:
        return {}

    def extract(
        self,
        pdf_path: str,
        *,
        pipeline_logger: Optional["PipelineLogger"] = None,
    ) -> NormalizedExtractionResult:
        start = time.monotonic()
        try:
            return self._do_extract(pdf_path, pipeline_logger=pipeline_logger)
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(
                provider_id=self.provider_id,
                message=str(e),
                original=e,
            ) from e
        finally:
            pass  # extraction_time_ms set inside _do_extract

    def _do_extract(
        self,
        pdf_path: str,
        pipeline_logger=None,
    ) -> NormalizedExtractionResult:
        start = time.monotonic()
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import (
                PdfPipelineOptions,
                TableFormerMode,
            )
            from docling.document_converter import DocumentConverter, PdfFormatOption
        except ImportError as e:
            raise ProviderError(
                provider_id=self.provider_id,
                message=f"docling not installed: {e}",
                original=e,
            ) from e

        # --- Pipeline options (matches source_commands.py existing behaviour) ---
        pipeline_options = PdfPipelineOptions(do_table_structure=True)
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
        pipeline_options.table_structure_options.do_cell_matching = True

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        result = converter.convert(pdf_path)
        doc = result.document
        tables: List[NormalizedTable] = []
        warnings: List[str] = []

        for idx, table in enumerate(doc.tables):
            try:
                df = table.export_to_dataframe(doc=doc)

                # Normalization pipeline (validated in E25-S1)
                df = df.map(
                    lambda v: re.sub(r"(\d+)-\s+(\d+)", r"\1-\2", str(v))
                    if isinstance(v, str)
                    else v
                )
                for col in df.columns:
                    col_str = str(col).lower()
                    if "hazard" in col_str or "status" in col_str:
                        df[col] = df[col].apply(
                            lambda v: re.sub(r"^Asbestos\s+", "", str(v))
                            if isinstance(v, str)
                            else v
                        )

                page_no = table.prov[0].page_no if table.prov else -1
                # TODO: E31-S3 — extract bbox from table.prov[0].bbox

                tables.append(
                    NormalizedTable(
                        table_index=idx,
                        page=page_no,
                        row_count=len(df),
                        col_count=len(df.columns),
                        columns=list(df.columns),
                        html=table.export_to_html(doc=doc),
                        markdown=df.to_markdown(index=False) or "",
                        csv=df.to_csv(index=False),
                        bbox=None,
                    )
                )
            except Exception as e:
                warnings.append(f"Table {idx} skipped: {e}")
                logger.warning(f"DoclingAdapter: table {idx} export failed: {e}")
                continue

        elapsed_ms = int((time.monotonic() - start) * 1000)
        return NormalizedExtractionResult(
            provider_id=self.provider_id,
            tables=tables,
            extraction_time_ms=elapsed_ms,
            warnings=warnings,
        )
```

### 4.4 `open_notebook/extractors/providers/mineru_adapter.py`

```python
"""
MinerU 2.x extraction provider adapter.

Wraps mineru.MinerUDocumentConverter and converts output to
NormalizedExtractionResult.

Story: E31-S2 Provider Adapter Framework
"""
from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING, Dict, List, Optional

from loguru import logger

from open_notebook.extractors.providers.base import (
    NormalizedExtractionResult,
    NormalizedTable,
    ProviderError,
)

if TYPE_CHECKING:
    from open_notebook.extractors.pipeline_logger import PipelineLogger

_MINERU_ENABLED = os.environ.get("MINERU_ENABLED", "false").lower() == "true"


class MinerUAdapter:
    """ExtractionProvider that wraps MinerU 2.x DocumentConverter.

    MinerU is imported lazily so that this class can be instantiated on
    systems where mineru is not installed. The MINERU_ENABLED env var
    must be set to 'true' to activate extraction.
    """

    @property
    def provider_id(self) -> str:
        return "mineru"

    def supports_table_extraction(self) -> bool:
        return True

    def get_field_confidence(self) -> Dict[str, float]:
        return {}

    def extract(
        self,
        pdf_path: str,
        *,
        pipeline_logger: Optional["PipelineLogger"] = None,
    ) -> NormalizedExtractionResult:
        # Check env var each time (allows test monkeypatching)
        if os.environ.get("MINERU_ENABLED", "false").lower() != "true":
            raise ProviderError(
                provider_id=self.provider_id,
                message="MinerU disabled via MINERU_ENABLED env var",
            )

        start = time.monotonic()
        try:
            return self._do_extract(pdf_path)
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(
                provider_id=self.provider_id,
                message=str(e),
                original=e,
            ) from e

    def _do_extract(self, pdf_path: str) -> NormalizedExtractionResult:
        start = time.monotonic()
        try:
            from mineru import MinerUDocumentConverter
        except ImportError as e:
            raise ProviderError(
                provider_id=self.provider_id,
                message=f"mineru not installed: {e}",
                original=e,
            ) from e

        converter = MinerUDocumentConverter()
        raw_result = converter.convert(pdf_path)

        tables = self._parse_mineru_result(raw_result)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return NormalizedExtractionResult(
            provider_id=self.provider_id,
            tables=tables,
            extraction_time_ms=elapsed_ms,
        )

    def _parse_mineru_result(self, result) -> List[NormalizedTable]:
        """Convert MinerU result object to list of NormalizedTable.

        MinerU 2.x result schema is explored here defensively — iterates
        known attribute paths and skips unknown shapes with a warning.

        NOTE: The exact MinerU 2.x result shape must be confirmed against
        the E32-S6 Ollama evaluation outputs. This implementation is a
        best-effort skeleton pending that confirmation. Update this method
        once the actual result schema is validated.
        """
        tables: List[NormalizedTable] = []
        candidates = []

        # Try known attribute paths for MinerU 2.x result shapes
        if hasattr(result, "tables"):
            candidates = list(result.tables)
        elif hasattr(result, "pages"):
            for page in result.pages:
                if hasattr(page, "tables"):
                    candidates.extend(page.tables)

        for idx, tbl in enumerate(candidates):
            try:
                html = getattr(tbl, "html", "") or ""
                markdown = getattr(tbl, "markdown", "") or ""
                page = int(getattr(tbl, "page", -1))

                # Derive columns and counts from HTML or markdown
                if html:
                    from open_notebook.extractors.providers.normalizer import (
                        normalize_html_table,
                    )
                    norm = normalize_html_table(html, table_index=idx, page=page)
                    tables.append(norm)
                elif markdown:
                    from open_notebook.extractors.providers.normalizer import (
                        normalize_markdown_table,
                    )
                    norm = normalize_markdown_table(markdown, table_index=idx, page=page)
                    tables.append(norm)
                else:
                    logger.warning(f"MinerUAdapter: table {idx} has no html/markdown, skipping")
            except Exception as e:
                logger.warning(f"MinerUAdapter: table {idx} parse failed: {e}")
                continue

        return tables
```

### 4.5 `open_notebook/extractors/providers/__init__.py`

```python
"""
Provider Registry for extraction providers.

Auto-registers DoclingAdapter and MinerUAdapter at import time.
Call get_provider_registry() to access the singleton registry.

Story: E31-S2 Provider Adapter Framework
"""
from __future__ import annotations

import os
from typing import Dict, List

from loguru import logger

from open_notebook.extractors.providers.base import ExtractionProvider, ProviderError
from open_notebook.extractors.providers.docling_adapter import DoclingAdapter
from open_notebook.extractors.providers.mineru_adapter import MinerUAdapter


class ProviderRegistry:
    """Registry for ExtractionProvider instances.

    Thread-safety: not required — registry is populated at module import
    time in a single-threaded context. Concurrent extract() calls go
    directly to provider instances which are stateless.
    """

    def __init__(self) -> None:
        self._providers: Dict[str, ExtractionProvider] = {}
        self._default_id: Optional[str] = None  # type: ignore[type-arg]

    def register(self, provider: ExtractionProvider) -> None:
        """Register a provider. Overwrites any existing registration."""
        pid = provider.provider_id
        self._providers[pid] = provider
        logger.debug(f"ProviderRegistry: registered provider '{pid}'")

    def get_provider(self, provider_id: str) -> ExtractionProvider:
        """Return provider by ID.

        Raises:
            KeyError: If provider_id not in registry.
        """
        if provider_id not in self._providers:
            raise KeyError(
                f"Provider '{provider_id}' not registered. "
                f"Available: {self.list_providers()}"
            )
        return self._providers[provider_id]

    def list_providers(self) -> List[str]:
        """Return sorted list of registered provider IDs."""
        return sorted(self._providers.keys())

    def set_default(self, provider_id: str) -> None:
        """Set the default provider by ID.

        Raises:
            KeyError: If provider_id not in registry.
        """
        self.get_provider(provider_id)  # validates existence
        self._default_id = provider_id

    def get_default(self) -> ExtractionProvider:
        """Return the default provider.

        Priority:
        1. ACM_EXTRACTION_PROVIDER env var (read each call)
        2. set_default() value
        3. First registered provider

        Raises:
            RuntimeError: If registry is empty.
        """
        if not self._providers:
            raise RuntimeError("ProviderRegistry is empty — no providers registered")

        env_id = os.environ.get("ACM_EXTRACTION_PROVIDER", "").strip()
        if env_id and env_id in self._providers:
            return self._providers[env_id]

        if self._default_id and self._default_id in self._providers:
            return self._providers[self._default_id]

        # Fall back to "docling" if present, else first alphabetically
        if "docling" in self._providers:
            return self._providers["docling"]

        return next(iter(self._providers.values()))


# ---------------------------------------------------------------------------
# Module-level singleton — populated at import time
# ---------------------------------------------------------------------------

_registry = ProviderRegistry()
_registry.register(DoclingAdapter())
_registry.register(MinerUAdapter())
_registry.set_default("docling")


def get_provider_registry() -> ProviderRegistry:
    """Return the module-level singleton ProviderRegistry."""
    return _registry
```

### 4.6 Modification to `commands/source_commands.py`

The inline `_extract_tables_with_docling` function and `_store_docling_tables` function are
RETAINED in `source_commands.py` for this story. The refactor of the call site to use
`get_provider_registry()` is out of scope for E31-S2 to minimise risk.

**Rationale:** E31-S2 is a 3-SP story focused on creating the adapter framework. The call-site
migration in `source_commands.py` belongs in E31-S3 (pipeline integration) once the adapters
have test coverage. This avoids a risky simultaneous change to the storage layer.

**What DOES change in `source_commands.py`:**
None. `source_commands.py` is not modified in this story.

If the product owner decides to include the migration, add the following diff to the story
scope:

```python
# BEFORE (source_commands.py ~line 291)
docling_tables = await _extract_tables_with_docling(
    str(processed_source.id),
    pdf_path,
    pipeline_logger=docling_pl,
)

# AFTER (if migration is in scope)
from open_notebook.extractors.providers import get_provider_registry
from open_notebook.extractors.providers.base import ProviderError

provider = get_provider_registry().get_default()
try:
    extraction_result = provider.extract(
        pdf_path,
        pipeline_logger=docling_pl,
    )
    docling_tables = [
        {
            "table_index": t.table_index,
            "page": t.page,
            "rows": t.row_count,
            "columns": t.columns,
            "csv": t.csv,
            "markdown": t.markdown,
            "html": t.html,
        }
        for t in extraction_result.tables
    ]
except ProviderError as e:
    logger.error(f"Provider extraction failed: {e}")
    docling_tables = []
```

### 4.7 `tests/test_provider_adapters.py` — Structure

```python
"""
Unit tests for E31-S2 Provider Adapter Framework.

All tests use mock/monkeypatching to avoid requiring docling or mineru
to be installed in the test environment.
"""
import sys
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest

from open_notebook.extractors.providers.base import (
    NormalizedExtractionResult,
    NormalizedTable,
    ProviderError,
    TableBBox,
)
from open_notebook.extractors.providers import ProviderRegistry, get_provider_registry
from open_notebook.extractors.providers.docling_adapter import DoclingAdapter
from open_notebook.extractors.providers.mineru_adapter import MinerUAdapter
from open_notebook.extractors.providers.normalizer import (
    normalize_html_table,
    normalize_markdown_table,
)


# ---------------------------------------------------------------------------
# NormalizedTable / NormalizedExtractionResult shape tests
# ---------------------------------------------------------------------------

class TestNormalizedTable:
    def test_fields_present(self):
        t = NormalizedTable(
            table_index=0, page=1, row_count=3, col_count=2,
            columns=["A", "B"], html="<table/>", markdown="| A | B |",
        )
        assert t.table_index == 0
        assert t.csv is None  # optional
        assert t.bbox is None  # optional

    def test_bbox_optional(self):
        bbox = TableBBox(x=0.0, y=0.0, width=100.0, height=50.0, page=1)
        t = NormalizedTable(
            table_index=0, page=1, row_count=0, col_count=0,
            columns=[], html="", markdown="", bbox=bbox,
        )
        assert t.bbox.page == 1


class TestNormalizedExtractionResult:
    def test_fields_present(self):
        r = NormalizedExtractionResult(provider_id="test")
        assert r.tables == []
        assert r.extraction_time_ms == 0
        assert r.warnings == []


# ---------------------------------------------------------------------------
# DoclingAdapter tests
# ---------------------------------------------------------------------------

class TestDoclingAdapter:
    def test_provider_id(self):
        assert DoclingAdapter().provider_id == "docling"

    def test_supports_table_extraction(self):
        assert DoclingAdapter().supports_table_extraction() is True

    def test_get_field_confidence(self):
        assert DoclingAdapter().get_field_confidence() == {}

    def test_import_error_raises_provider_error(self, monkeypatch):
        """When docling is not importable, extract() raises ProviderError."""
        adapter = DoclingAdapter()
        # Simulate missing docling by patching __import__
        import builtins
        original_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if "docling" in name:
                raise ImportError("docling not installed")
            return original_import(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", mock_import)
        with pytest.raises(ProviderError) as exc_info:
            adapter.extract("/fake/path.pdf")
        assert exc_info.value.provider_id == "docling"

    def test_docling_runtime_error_raises_provider_error(self, monkeypatch):
        """If DocumentConverter.convert() raises, ProviderError is returned."""
        # ... mock docling imports to raise RuntimeError inside convert()


# ---------------------------------------------------------------------------
# MinerUAdapter tests
# ---------------------------------------------------------------------------

class TestMinerUAdapter:
    def test_provider_id(self):
        assert MinerUAdapter().provider_id == "mineru"

    def test_disabled_env_var_raises(self, monkeypatch):
        monkeypatch.setenv("MINERU_ENABLED", "false")
        with pytest.raises(ProviderError) as exc_info:
            MinerUAdapter().extract("/fake/path.pdf")
        assert "MINERU_ENABLED" in str(exc_info.value)

    def test_import_error_raises_provider_error(self, monkeypatch):
        monkeypatch.setenv("MINERU_ENABLED", "true")
        import builtins
        original_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if "mineru" in name:
                raise ImportError("mineru not installed")
            return original_import(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", mock_import)
        with pytest.raises(ProviderError) as exc_info:
            MinerUAdapter().extract("/fake/path.pdf")
        assert exc_info.value.provider_id == "mineru"


# ---------------------------------------------------------------------------
# ProviderRegistry tests
# ---------------------------------------------------------------------------

class TestProviderRegistry:
    def _make_provider(self, pid: str):
        class FakeProvider:
            @property
            def provider_id(self):
                return pid
            def extract(self, pdf_path, *, pipeline_logger=None):
                return NormalizedExtractionResult(provider_id=pid)
            def supports_table_extraction(self):
                return True
            def get_field_confidence(self):
                return {}
        return FakeProvider()

    def test_register_and_get(self):
        reg = ProviderRegistry()
        p = self._make_provider("test")
        reg.register(p)
        assert reg.get_provider("test") is p

    def test_list_providers_sorted(self):
        reg = ProviderRegistry()
        reg.register(self._make_provider("zebra"))
        reg.register(self._make_provider("alpha"))
        assert reg.list_providers() == ["alpha", "zebra"]

    def test_unknown_provider_raises_keyerror(self):
        reg = ProviderRegistry()
        with pytest.raises(KeyError):
            reg.get_provider("nonexistent")

    def test_set_default_and_get_default(self):
        reg = ProviderRegistry()
        p = self._make_provider("myprovider")
        reg.register(p)
        reg.set_default("myprovider")
        assert reg.get_default() is p

    def test_default_env_var_respected(self, monkeypatch):
        reg = ProviderRegistry()
        pa = self._make_provider("alpha")
        pb = self._make_provider("beta")
        reg.register(pa)
        reg.register(pb)
        reg.set_default("alpha")
        monkeypatch.setenv("ACM_EXTRACTION_PROVIDER", "beta")
        assert reg.get_default() is pb

    def test_empty_registry_raises_runtime_error(self):
        reg = ProviderRegistry()
        with pytest.raises(RuntimeError):
            reg.get_default()


# ---------------------------------------------------------------------------
# Normalizer tests
# ---------------------------------------------------------------------------

class TestNormalizeHtmlTable:
    def test_basic_html_table(self):
        html = """
        <table>
          <tr><th>Name</th><th>Value</th></tr>
          <tr><td>Alpha</td><td>1</td></tr>
          <tr><td>Beta</td><td>2</td></tr>
        </table>
        """
        norm = normalize_html_table(html, table_index=0, page=3)
        assert norm.col_count == 2
        assert norm.row_count == 2
        assert "Name" in norm.columns
        assert norm.page == 3

    def test_invalid_html_raises_value_error(self):
        with pytest.raises(ValueError):
            normalize_html_table("not a table at all", table_index=0)


class TestNormalizeMarkdownTable:
    def test_basic_markdown_table(self):
        md = "| Col1 | Col2 |\n|------|------|\n| A | B |\n| C | D |"
        norm = normalize_markdown_table(md, table_index=0, page=5)
        assert norm.col_count == 2
        assert norm.row_count == 2
        assert norm.columns == ["Col1", "Col2"]
        assert norm.page == 5

    def test_invalid_markdown_raises_value_error(self):
        with pytest.raises(ValueError):
            normalize_markdown_table("no table here", table_index=0)
```

---

## 5. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MINERU_ENABLED` | `"false"` | Set to `"true"` to activate MinerUAdapter |
| `ACM_EXTRACTION_PROVIDER` | `"docling"` | ID of the default provider returned by `get_default()` |

Both variables are read at runtime (not at import time) to allow test-time overriding via
`monkeypatch.setenv`.

---

## 6. Error Handling Contract

```
PDF path → provider.extract(pdf_path)
               │
               ├── ImportError → ProviderError (provider_id, "not installed")
               │
               ├── RuntimeError from library → ProviderError (wraps original)
               │
               └── Per-table exception → warning appended, table skipped,
                   NormalizedExtractionResult returned with partial tables
```

Key rule: `ProviderError` is the ONLY exception type that can escape `extract()`. All other
exceptions must be caught inside the adapter and either re-raised as `ProviderError` (fatal
to the whole extraction) or logged as a warning with the table skipped (partial failure).

---

## 7. Dependencies

No new Python dependencies are required. Both `docling` and `mineru` are already declared in
`pyproject.toml` (Docling via `docling>=...`, MinerU via `mineru>=2.7.0`). The normalizer
uses only stdlib (`html.parser`, `re`) and is therefore always available.

---

## 8. Open Questions / TODOs

| Item | Priority | Notes |
|------|----------|-------|
| MinerU 2.x exact result schema | HIGH | `_parse_mineru_result` is a skeleton; validate against real output from E32-S6 eval runs in `scripts/research/results/` |
| Docling bbox extraction | LOW | `table.prov[0].bbox` available but not mapped in this story — marked with `TODO` comment in DoclingAdapter |
| Thread safety of ProviderRegistry | LOW | Not needed now; registry is read-only after module init |
| Async extract() variant | MEDIUM | Current protocol is synchronous; an `async def extract_async()` variant may be needed when integrating with LangGraph nodes |

---

## 9. Verification Checklist

Before marking E31-S2 done, the dev agent MUST confirm:

- [ ] `uv run ruff check open_notebook/extractors/providers/` passes with no errors
- [ ] `uv run pytest tests/test_provider_adapters.py -v` all tests pass
- [ ] `from open_notebook.extractors.providers import get_provider_registry` importable without
      docling or mineru installed (deferred import test)
- [ ] `get_provider_registry().list_providers()` returns `["docling", "mineru"]`
- [ ] `uv run pytest tests/ -x` all pre-existing tests still pass (no regressions)

---

## 10. Dev Agent Record

_To be filled in by the implementing agent._

| Field | Value |
|-------|-------|
| Agent | — |
| Start date | — |
| Completion date | — |
| Build status | — |
| Files created | — |
| Files modified | — |
| Tests passed | — |
| Ruff status | — |
| Notes | — |
