"""
Docling extraction provider adapter.

Wraps the Docling DocumentConverter table extraction logic (originally
in commands/source_commands.py::_extract_tables_with_docling) behind
the ExtractionProvider protocol.

All docling imports are deferred inside extract() so the module is
importable even when docling is not installed.

Story: E31-S2 Provider Adapter Framework
"""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING, Dict, List

from loguru import logger

from open_notebook.extractors.providers.base import (
    NormalizedExtractionResult,
    NormalizedTable,
    ProviderError,
)

if TYPE_CHECKING:
    pass  # PipelineLogger import is deferred to avoid circular dependency


class DoclingAdapter:
    """Extraction provider that uses Docling's DocumentConverter.

    Replicates the normalization pipeline from E25-S1 validation:
    1. Fix split sample numbers: "34511-039- 001" → "34511-039-001"
    2. Strip "Asbestos " prefix from hazard/status columns
    """

    @property
    def provider_id(self) -> str:
        """Stable identifier for this provider."""
        return "docling"

    def extract(
        self,
        pdf_path: str,
        *,
        pipeline_logger=None,
    ) -> NormalizedExtractionResult:
        """Extract tables from a PDF file using Docling.

        Args:
            pdf_path: Absolute path to the PDF file.
            pipeline_logger: Optional PipelineLogger for observability hooks.

        Returns:
            NormalizedExtractionResult with all extracted tables.

        Raises:
            ProviderError: If Docling is not installed or extraction fails.
        """
        start_ms = int(time.monotonic() * 1000)

        try:
            return self._run_extraction(pdf_path, pipeline_logger, start_ms)
        except ProviderError:
            raise
        except Exception as e:
            logger.warning(f"DoclingAdapter: extraction failed: {e}")
            raise ProviderError(
                provider_id=self.provider_id,
                message=str(e),
                original=e,
            ) from e

    def _run_extraction(
        self,
        pdf_path: str,
        pipeline_logger,
        start_ms: int,
    ) -> NormalizedExtractionResult:
        """Internal extraction logic with deferred Docling imports."""
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
                message=("docling is not installed. Install it with: uv add docling"),
                original=e,
            ) from e

        from open_notebook.extractors.pipeline_events import StageId

        if pipeline_logger:
            pipeline_logger.stage_enter(
                StageId.DOCLING_EXTRACTION, "Starting Docling table extraction"
            )

        pipeline_options = PdfPipelineOptions(do_table_structure=True)
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
        pipeline_options.table_structure_options.do_cell_matching = True

        # accelerator_options belongs on PdfPipelineOptions, NOT DocumentConverter.
        # AUTO lets Docling use GPU when PyTorch has correct CUDA kernels (e.g.
        # cu128 on RTX 5090) and falls back to CPU otherwise.
        try:
            from docling.datamodel.accelerator_options import (
                AcceleratorDevice,
                AcceleratorOptions,
            )
            pipeline_options.accelerator_options = AcceleratorOptions(
                device=AcceleratorDevice.AUTO,
            )
        except ImportError:
            pass  # Older docling version without accelerator_options

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            },
        )

        result = converter.convert(pdf_path)
        doc = result.document

        tables: List[NormalizedTable] = []
        warnings: List[str] = []

        for idx, table in enumerate(doc.tables):
            try:
                df = table.export_to_dataframe(doc=doc)

                # --- Normalization pipeline (patterns validated in E25-S1) ---

                # 1. Fix split sample numbers: "34511-039- 001" → "34511-039-001"
                df = df.map(
                    lambda v: re.sub(r"(\d+)-\s+(\d+)", r"\1-\2", str(v))
                    if isinstance(v, str)
                    else v
                )

                # 2. Strip "Asbestos " prefix from hazard status columns
                for col in df.columns:
                    col_str = str(col).lower()
                    if "hazard" in col_str or "status" in col_str:
                        df[col] = df[col].apply(
                            lambda v: re.sub(r"^Asbestos\s+", "", str(v))
                            if isinstance(v, str)
                            else v
                        )

                page_no = table.prov[0].page_no if table.prov else -1

                # TODO: Extract bbox from table.prov[0].bbox when needed
                # (out of scope for E31-S2 — leave as None)

                # Capture lossless cell-level representation for per-row extraction
                try:
                    docling_json = table.data.model_dump(mode="json")
                except Exception as export_err:
                    logger.warning(
                        f"DoclingAdapter table {idx}: model_dump() failed: {export_err}"
                    )
                    docling_json = None

                normalized = NormalizedTable(
                    table_index=idx,
                    page=page_no,
                    row_count=len(df),
                    col_count=len(df.columns),
                    columns=list(df.columns),
                    html=table.export_to_html(doc=doc),
                    markdown=df.to_markdown(index=False) or "",
                    csv=df.to_csv(index=False),
                    bbox=None,
                    docling_json=docling_json,
                )
                tables.append(normalized)

                logger.info(
                    f"DoclingAdapter table {idx}: page={page_no}, "
                    f"rows={len(df)}, cols={len(df.columns)}"
                )
            except Exception as e:
                msg = f"Docling table {idx} export failed: {e}"
                logger.warning(msg)
                warnings.append(msg)
                continue

        elapsed_ms = int(time.monotonic() * 1000) - start_ms

        if pipeline_logger:
            pipeline_logger.stage_complete(
                StageId.DOCLING_EXTRACTION,
                summary=f"Extracted {len(tables)} tables from {pdf_path}",
                tables_found=len(tables),
                total_rows=sum(t.row_count for t in tables),
            )

        logger.info(
            f"DoclingAdapter: {len(tables)} tables extracted from {pdf_path} "
            f"in {elapsed_ms}ms"
        )

        return NormalizedExtractionResult(
            provider_id=self.provider_id,
            tables=tables,
            extraction_time_ms=elapsed_ms,
            warnings=warnings,
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
        """Return True — Docling specializes in table extraction."""
        return True

    def get_field_confidence(self) -> Dict[str, float]:
        """Return empty dict — Docling does not produce field-level confidence."""
        return {}
