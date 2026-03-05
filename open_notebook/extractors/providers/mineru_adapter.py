"""
MinerU 2.x extraction provider adapter.

Wraps the MinerU DocumentConverter behind the ExtractionProvider protocol.
All MinerU imports are deferred inside extract() so the module is
importable even when mineru is not installed.

Controlled by MINERU_ENABLED environment variable (default: false).

Story: E31-S2 Provider Adapter Framework
"""

from __future__ import annotations

import os
import time
from typing import Dict, List

from loguru import logger

from open_notebook.extractors.providers.base import (
    NormalizedExtractionResult,
    NormalizedTable,
    ProviderError,
)


class MinerUAdapter:
    """Extraction provider that uses MinerU 2.x DocumentConverter.

    Enabled only when MINERU_ENABLED environment variable is set to "true".
    Raises ProviderError at extract() time if MinerU is disabled or not installed.
    """

    @property
    def provider_id(self) -> str:
        """Stable identifier for this provider."""
        return "mineru"

    def extract(
        self,
        pdf_path: str,
        *,
        pipeline_logger=None,
    ) -> NormalizedExtractionResult:
        """Extract tables from a PDF file using MinerU 2.x.

        Args:
            pdf_path: Absolute path to the PDF file.
            pipeline_logger: Optional PipelineLogger (currently unused by MinerU).

        Returns:
            NormalizedExtractionResult with all extracted tables.

        Raises:
            ProviderError: If MinerU is disabled, not installed, or extraction fails.
        """
        # Gate: check MINERU_ENABLED env var first
        mineru_enabled = os.environ.get("MINERU_ENABLED", "false").lower()
        if mineru_enabled != "true":
            raise ProviderError(
                provider_id=self.provider_id,
                message="MinerU disabled via MINERU_ENABLED env var",
            )

        start_ms = int(time.monotonic() * 1000)

        try:
            return self._run_extraction(pdf_path, start_ms)
        except ProviderError:
            raise
        except Exception as e:
            logger.warning(f"MinerUAdapter: extraction failed: {e}")
            raise ProviderError(
                provider_id=self.provider_id,
                message=str(e),
                original=e,
            ) from e

    def _run_extraction(
        self, pdf_path: str, start_ms: int
    ) -> NormalizedExtractionResult:
        """Internal extraction logic with deferred MinerU imports."""
        try:
            from mineru import MinerUDocumentConverter
        except ImportError as e:
            raise ProviderError(
                provider_id=self.provider_id,
                message=(
                    "mineru is not installed. Install it with: uv add 'mineru>=2.7.0'"
                ),
                original=e,
            ) from e

        converter = MinerUDocumentConverter()
        result = converter.convert(pdf_path)

        tables, warnings = self._parse_mineru_result(result)

        elapsed_ms = int(time.monotonic() * 1000) - start_ms

        logger.info(
            f"MinerUAdapter: {len(tables)} tables extracted from {pdf_path} "
            f"in {elapsed_ms}ms"
        )

        return NormalizedExtractionResult(
            provider_id=self.provider_id,
            tables=tables,
            extraction_time_ms=elapsed_ms,
            warnings=warnings,
        )

    def _parse_mineru_result(self, result) -> tuple[List[NormalizedTable], List[str]]:
        """Parse MinerU result into NormalizedTable list.

        MinerU 2.x output schema is not fully documented yet. This method
        attempts multiple attribute paths and degrades gracefully.

        Args:
            result: The object returned by MinerUDocumentConverter.convert().

        Returns:
            Tuple of (tables, warnings).
        """
        tables: List[NormalizedTable] = []
        warnings: List[str] = []

        # Attempt to locate table objects via known attribute paths
        raw_tables = None

        for attr_path in ("tables", "document.tables", "pages"):
            try:
                obj = result
                for part in attr_path.split("."):
                    obj = getattr(obj, part)
                if obj is not None:
                    raw_tables = obj
                    logger.debug(f"MinerUAdapter: found tables via result.{attr_path}")
                    break
            except AttributeError:
                continue

        if raw_tables is None:
            warnings.append(
                "MinerU result does not expose a known tables attribute "
                "(checked: tables, document.tables, pages). "
                "Returning empty result."
            )
            return tables, warnings

        for idx, table_obj in enumerate(raw_tables):
            try:
                normalized = self._convert_table(table_obj, idx)
                if normalized is not None:
                    tables.append(normalized)
            except Exception as e:
                msg = f"MinerUAdapter: table {idx} conversion failed: {e}"
                logger.warning(msg)
                warnings.append(msg)
                continue

        return tables, warnings

    def _convert_table(self, table_obj, idx: int) -> NormalizedTable | None:
        """Convert a single MinerU table object to NormalizedTable.

        Args:
            table_obj: A table-like object from MinerU output.
            idx: 0-based index of this table in the document.

        Returns:
            NormalizedTable or None if conversion is not possible.
        """
        # Attempt to extract HTML
        html = ""
        for attr in ("html", "to_html", "export_to_html"):
            try:
                val = getattr(table_obj, attr)
                html = val() if callable(val) else val
                if html:
                    break
            except (AttributeError, TypeError):
                continue

        # Attempt to extract markdown
        markdown = ""
        for attr in ("markdown", "to_markdown"):
            try:
                val = getattr(table_obj, attr)
                markdown = val() if callable(val) else val
                if markdown:
                    break
            except (AttributeError, TypeError):
                continue

        # Attempt to extract page number
        page = -1
        for attr in ("page", "page_no", "page_number"):
            try:
                val = getattr(table_obj, attr)
                if val is not None:
                    page = int(val)
                    break
            except (AttributeError, TypeError, ValueError):
                continue

        # If neither html nor markdown found, skip
        if not html and not markdown:
            logger.debug(
                f"MinerUAdapter: table {idx} has no html or markdown — skipping"
            )
            return None

        # Parse columns and row_count from whichever representation we have
        columns: List[str] = []
        row_count = 0

        if html:
            try:
                from open_notebook.extractors.providers.normalizer import (
                    normalize_html_table,
                )

                temp = normalize_html_table(html, table_index=idx, page=page)
                columns = temp.columns
                row_count = temp.row_count
                if not markdown:
                    markdown = temp.markdown
            except Exception:
                pass

        if not columns and markdown:
            try:
                from open_notebook.extractors.providers.normalizer import (
                    normalize_markdown_table,
                )

                temp = normalize_markdown_table(markdown, table_index=idx, page=page)
                columns = temp.columns
                row_count = temp.row_count
                if not html:
                    html = temp.html
            except Exception:
                pass

        return NormalizedTable(
            table_index=idx,
            page=page,
            row_count=row_count,
            col_count=len(columns),
            columns=columns,
            html=html,
            markdown=markdown,
            csv=None,
            bbox=None,
        )

    def cleanup(self) -> None:
        """Release resources after extraction. Safe to call multiple times."""
        import gc

        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    def supports_table_extraction(self) -> bool:
        """Return True — MinerU specializes in table extraction."""
        return True

    def get_field_confidence(self) -> Dict[str, float]:
        """Return empty dict — MinerU does not produce field-level confidence."""
        return {}
