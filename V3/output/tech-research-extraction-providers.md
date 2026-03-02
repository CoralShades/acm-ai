# Technical Research: Multi-Provider Table Extraction for ACM-AI V3

| Field | Value |
|-------|-------|
| **Date** | 2026-03-02 |
| **Author** | Technical Research Agent |
| **Status** | Complete |
| **Scope** | Evaluate extraction providers for triple-provider parallel architecture |
| **Decision Required** | Which 2 providers to implement now (Docling + 1) |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current Baseline: Docling + PyMuPDF](#2-current-baseline-docling--pymupdf)
3. [Provider 1: Google Document AI (Gemini Layout Parser)](#3-provider-1-google-document-ai-gemini-layout-parser)
4. [Provider 2: PaddleOCR PP-StructureV3](#4-provider-2-paddleocr-pp-structurev3)
5. [Provider 2b: MinerU 2.x (Alternative to Raw PP-Structure)](#5-provider-2b-mineru-2x-alternative-to-raw-pp-structure)
6. [Provider Comparison Matrix](#6-provider-comparison-matrix)
7. [Recommendation](#7-recommendation)
8. [Consensus Layer Design](#8-consensus-layer-design)
9. [Risk Assessment](#9-risk-assessment)
10. [Integration Approach](#10-integration-approach)
11. [Dependency Analysis](#11-dependency-analysis)
12. [Next Steps](#12-next-steps)

---

## 1. Executive Summary

**Recommendation: Implement Docling + MinerU 2.x now. Google Document AI as the third provider in a future epic.**

The research evaluated three additional extraction providers to complement the current Docling + PyMuPDF pipeline. The critical finding is that **MinerU 2.x has fundamentally changed** since we last evaluated it: it has replaced `paddlepaddle-gpu` with `paddleocr2torch`, eliminating the PyTorch conflict that originally forced us to abandon it. MinerU 2.x can now be installed directly in the main `.venv/` alongside PyTorch, Docling, and all existing dependencies — no subprocess bridge, no isolated venv needed.

| Provider | Implement Now? | Rationale |
|----------|:--------------:|-----------|
| **Docling + PyMuPDF** (current) | Already live | 31/31 Broadmeadows, 100% accuracy baseline |
| **MinerU 2.x** | **Yes** | PyTorch-native (no venv conflict), cross-page stitching, fine-tunable, zero cloud cost, runs on RTX 4090 |
| **Google Document AI** | Future epic | Strong merged-cell handling, Australian data residency, but adds cloud dependency + per-page cost |
| **PP-StructureV3 (raw)** | **No** | Still requires PaddlePaddle isolation; MinerU 2.x is strictly superior (wraps PP-Structure + adds cross-page stitching, reading order, document cleanup) |

**Key insight**: MinerU 2.x uses PP-StructureV3's table recognition models internally but wraps them in a PyTorch-native runtime, eliminating the fundamental dependency conflict. Choosing raw PP-Structure over MinerU 2.x means doing more work for less capability.

---

## 2. Current Baseline: Docling + PyMuPDF

### Architecture

```
PDF Upload
  ├── PyMuPDF (via content-core)
  │   └── source.full_text (reading-order text, page markers)
  │
  └── Docling Direct API (parallel, E26)
      └── DocumentConverter(TableFormerMode.ACCURATE)
          └── table.export_to_dataframe(doc=doc)
              ├── df.to_markdown() → acm_table_section.raw_text
              ├── table.export_to_html() → acm_table_section.raw_html
              └── df.to_csv() → acm_table_section.structured_json
```

### Accuracy

| Document | Records | Current Accuracy | Known Gaps |
|----------|--------:|:----------------:|------------|
| Broadmeadows (1 bldg, Prensa) | 31 | **31/31 (100%)** | None after E26 fixes |
| Alexander (6 bldgs, Prensa ARA) | 43 | **36/43 (~84%)** | ARA format differences, page overflow |
| Production docs (2000+, various firms) | Unknown | **Untested** | Variable PDF formats, unknown table layouts |

### Known Gaps

1. **Page 8 overflow** — Docling's TableFormer doesn't detect tables with < ~3 rows below its detection threshold. PyMuPDF covers this via `full_text`, but only through LLM interpretation.
2. **Cross-page tables** — Docling does NOT stitch tables spanning pages. Each page produces a separate DataFrame. The LLM must infer continuity from context.
3. **Single-provider fragility** — If Docling misparses a table, there is no second opinion. The regex recovery (`_recover_no_access_records()`) catches some edge cases but is pattern-specific.
4. **Consultant format diversity** — Broadmeadows + Alexander are both Prensa format. Greencap, WSP, AEI, and other consulting firms use different layouts. Zero validation on these formats.

### Processing Speed

- Docling extraction: ~22s for a 20-page PDF
- Full pipeline (including LLM): ~222-244s total
- Target: < 30s for extraction-only, < 300s for full pipeline

---

## 3. Provider 1: Google Document AI (Gemini Layout Parser)

### Overview

Google Document AI offers two relevant processors:

| Processor | Merged Cells | Price/1k pages | Best For |
|-----------|:------------:|---------------:|----------|
| Form Parser | No | $30 | Simple tables only |
| **Gemini Layout Parser** | **Yes** | **$10** | Complex tables with merged cells |

**Form Parser is unsuitable** for ACM registers — it cannot handle `colspan`/`rowspan`, which are present in virtually all SAMP report tables. The Gemini Layout Parser is the only viable Google offering.

### Capabilities Assessment

| Capability | Rating | Detail |
|------------|:------:|--------|
| Merged cell handling | Good | Explicitly handles colspan/rowspan (Form Parser does not) |
| Cross-page table stitching | **No** | "Tables spanning multiple pages might be split in two tables" — requires post-processing |
| Cell-level confidence scores | **No** | Entity-level and token-level confidence only; no per-cell scores on table output |
| Batch processing | Yes | Up to 1,000 docs/request via GCS, async LRO |
| DataFrame output | Yes | Via `documentai-toolbox` (`table.to_dataframe()`) — but toolbox is "experimental" |
| Fine-tuning | **No** | No table-labeling workflow available (unlike Azure) |

### Pricing

| Scenario | Documents | Avg Pages | Total Pages | Cost (Layout Parser) |
|----------|----------:|----------:|------------:|---------------------:|
| Base case | 2,000 | 30 | 60,000 | **$600** |
| Scale case | 5,000 | 30 | 150,000 | **$1,500** |
| Ongoing monthly (est.) | 200 | 30 | 6,000 | **$60/month** |

Note: Assured Workloads (Australian data boundary) adds +5% premium.

### Australian Data Residency

- `australia-southeast1` (Sydney) is a supported Document AI region
- **Assured Workloads** available: restricts all data to Australian soil
- Compliance: ISO 27001/27017/27018, SOC 2/3, FedRAMP High, HIPAA
- Data NOT used for model training (confirmed in security docs)
- Sync requests: processed in-memory, never written to disk
- Batch requests: documents deleted after processing (1-day failsafe TTL)

### Python SDK Integration

```python
# Core SDK
pip install google-cloud-documentai           # ~50 KB
pip install google-cloud-documentai-toolbox   # For DataFrame export (experimental)

# Usage
from google.cloud import documentai
from google.api_core.client_options import ClientOptions

client = documentai.DocumentProcessorServiceClient(
    client_options=ClientOptions(
        api_endpoint="australia-southeast1-documentai.googleapis.com"
    )
)

# Process document → extract tables → toolbox.to_dataframe()
```

No GPU required. No CUDA dependency. No venv conflicts. Pure REST API calls.

### Integration Effort Estimate

| Task | SP |
|------|---:|
| GCP project setup, processor creation, auth | 1 |
| `GoogleDocumentAIAdapter` implementation | 3 |
| Cross-page table stitching post-processor | 2 |
| Integration tests + benchmark validation | 2 |
| **Total** | **8 SP** |

---

## 4. Provider 2: PaddleOCR PP-StructureV3

### Overview

PP-StructureV3 (released May 2025 with PaddleOCR 3.0) is the latest open-source document parsing pipeline from Baidu. Its table component, **PP-TableMagic**, uses:

- **SLANeXt** model — separate weights for wired (bordered) and wireless (borderless) tables
- **RT-DETR-L** — cell detection with specialized pre-training
- **Dual-stream architecture** — classifies tables as wired/wireless, then routes to specialized models
- HTML output with full `colspan`/`rowspan` support

### Accuracy

| Benchmark | PP-StructureV3 | MinerU 1.3 | Docling (est.) | Notes |
|-----------|:--------------:|:----------:|:--------------:|-------|
| OmniDocBench (EN, edit dist.) | **0.145** | 0.166 | ~0.15* | Lower is better |
| OmniDocBench (ZH, edit dist.) | **0.206** | 0.310 | N/A | |
| PubTabNet TEDS (SLANet) | 95.89% | ~93%* | ~94%* | SLANeXt reportedly higher |

*Estimated from E25 spike data and published comparisons.

### GPU Requirements (RTX 4090)

| Config | VRAM (Peak) | Seconds/Page (A100) | RTX 4090 Est. |
|--------|------------:|--------------------:|--------------:|
| Mobile OCR + FormulaNet-M (light) | 8-12 GB | 0.64 s | ~0.6 s |
| Server OCR + FormulaNet-L + charts (full) | 17-22 GB | 2.76 s | ~2.5 s |
| **Tables-only (no formulas/charts)** | **6-10 GB** | **~0.5 s** | **~0.5 s** |

RTX 4090 (24 GB VRAM) can run ANY configuration comfortably.

**20-page SAMP PDF estimate: 10-14 seconds** (tables-only config).

### PaddlePaddle/PyTorch Conflict

**Status: STILL BROKEN as of 2026.**

The conflict is at the CUDA shared library level:
- `torch 2.10.0+cu126` requires `nvidia-cusparselt-cu12==0.7.1`
- `paddlepaddle-gpu 3.2.x` requires `nvidia-cusparselt-cu12==0.6.3`
- Runtime error: `"_CudaDeviceProperties" is already registered!` (PaddleOCR #12046)

**Verdict: Two-venv isolation mandatory.** Would require `.venv-ppstructure/` with subprocess bridge, identical to the old MinerU pattern.

### Cross-Page Tables

**Not supported natively.** Each page processed independently. Custom post-processing required for continuation detection and stitching.

### Fine-Tuning

Supported via PaddleX 3.3. Requires:
- PubTabTableRecDataset format (image + HTML pairs)
- 500-2,000 labeled table images for meaningful improvement
- Training demonstrated on Tesla T4 (any GPU works)

### Integration Effort Estimate

| Task | SP |
|------|---:|
| `.venv-ppstructure/` setup + subprocess bridge | 2 |
| `PaddleOCRAdapter` implementation | 3 |
| Cross-page table stitching post-processor | 2 |
| Fine-tuning data labeling pipeline | 3 |
| Integration tests + benchmark validation | 2 |
| **Total** | **12 SP** |

---

## 5. Provider 2b: MinerU 2.x (Alternative to Raw PP-Structure)

### The Game-Changer: PaddlePaddle Eliminated

**MinerU 2.x (current: v2.7.6, Feb 2026) has completely replaced `paddlepaddle-gpu` with `paddleocr2torch`.** This is a fundamental architecture change from the MinerU 1.x we previously integrated and removed:

| Aspect | MinerU 1.x (removed) | MinerU 2.x (current) |
|--------|:---------------------:|:---------------------:|
| Table engine | PaddleOCR via `paddlepaddle-gpu` | PaddleOCR via `paddleocr2torch` (PyTorch-native) |
| PyTorch conflict | **YES** — subprocess bridge required | **NO** — direct import in main venv |
| CUDA dependency | `paddlepaddle-gpu` CUDA builds | Standard PyTorch CUDA (cu126) |
| Min PyTorch | N/A (separate venv) | `torch 2.2–2.6` (excl. 2.5) |
| Min VRAM | ~4 GB | 6 GB |
| Venv isolation | `.venv-mineru/` required | **Not needed** — installs in main `.venv/` |

### Capabilities vs Raw PP-Structure

| Capability | Raw PP-StructureV3 | MinerU 2.x |
|------------|:------------------:|:----------:|
| Table extraction to HTML | Yes | Yes |
| Multi-page PDF pipeline | Manual | Built-in |
| **Cross-page table stitching** | **No** | **Yes** (`concatenate_markdown_pages`) |
| Header/footer removal | No | Yes |
| Reading order recovery | Partial | Yes |
| Column-to-field mapping | Manual | Built-in markdown output |
| PyTorch conflict | **YES** | **NO** |
| Fine-tuning (via PP-Structure) | Yes (in isolated venv) | Yes (models are compatible) |

### Integration Pattern

**Direct import** — no subprocess, no isolated venv:

```python
# In main .venv/ — alongside torch, docling, langchain
from mineru import MinerUDocumentConverter

converter = MinerUDocumentConverter(device="cuda:0")
result = converter.convert("document.pdf")

for table in result.tables:
    html = table.to_html()
    df = pd.read_html(html)[0]
```

### Integration Effort Estimate

| Task | SP |
|------|---:|
| `pip install mineru` in main venv + verify no conflict | 1 |
| `MinerUAdapter` implementation | 2 |
| Column-mapping normalization | 1 |
| Integration tests + benchmark validation | 2 |
| Update CLAUDE.md / memory for new MinerU status | 0.5 |
| **Total** | **~6.5 SP** |

**This is roughly half the effort of raw PP-Structure** (no venv setup, no subprocess bridge, built-in cross-page handling).

---

## 6. Provider Comparison Matrix

| Dimension | Docling (current) | MinerU 2.x | Google Doc AI (Gemini) | PP-StructureV3 (raw) |
|-----------|:-----------------:|:----------:|:----------------------:|:--------------------:|
| **Table accuracy** | 93.5% DataFrames (E25) | 0.145 edit dist (OmniDocBench) | "95-99%" (vendor claim) | 0.145 edit dist |
| **Merged cells** | Yes (TableFormer) | Yes (SLANeXt) | Yes (Layout Parser) | Yes (SLANeXt) |
| **Cross-page tables** | **No** | **Yes** | **No** | **No** |
| **Confidence scores** | No | Per-model scores | Entity-level only | Per-model scores |
| **Fine-tuning** | No | Yes (via PP-Structure models) | **No** | Yes |
| **GPU required** | Yes (CUDA) | Yes (CUDA) | **No** (cloud API) | Yes (CUDA) |
| **VRAM (RTX 4090)** | ~2-4 GB | ~6-10 GB | N/A | ~6-10 GB |
| **Speed (20p PDF)** | ~22s | ~10-14s | ~5-10s (cloud) | ~10-14s |
| **PyTorch conflict** | No | **No** (2.x) | No | **YES** |
| **Venv isolation** | No | **No** (2.x) | No | **YES** (.venv-ppstructure/) |
| **Cloud dependency** | No | No | **YES** (GCP) | No |
| **Per-page cost** | $0 | $0 | **$0.01** | $0 |
| **Cost @ 60k pages** | $0 | $0 | **$600** | $0 |
| **Cost @ 150k pages** | $0 | $0 | **$1,500** | $0 |
| **AU data residency** | Local (no cloud) | Local (no cloud) | Yes (Assured Workloads) | Local (no cloud) |
| **Integration effort** | Already done | **~6.5 SP** | **~8 SP** | **~12 SP** |
| **Subprocess needed** | No | No | No | **Yes** |
| **Output format** | DataFrame, HTML, CSV | HTML, Markdown, JSON | Protobuf/JSON → DataFrame | HTML, JSON, Markdown |
| **Active maintenance** | Yes (IBM) | Yes (OpenDataLab) | Yes (Google) | Yes (Baidu) |

---

## 7. Recommendation

### Primary: Docling + MinerU 2.x (implement now)

**Rationale:**

1. **Zero cloud dependency** — Both run locally on RTX 4090. No GCP account, no per-page costs, no network latency. Critical for government data that may have strict data residency requirements.

2. **No venv isolation needed** — MinerU 2.x's `paddleocr2torch` eliminates the exact dependency conflict that caused us to remove MinerU 1.x. Direct import in main `.venv/`.

3. **Cross-page table stitching** — MinerU 2.x has this built-in. Docling and Google Doc AI both lack it. This is the single biggest gap in our current pipeline for production documents where tables regularly span pages.

4. **Fine-tunable** — If SAMP table formats from new consulting firms (Greencap, WSP, AEI) have significantly different layouts, we can fine-tune the underlying SLANeXt models on labeled examples. Google Doc AI has no table fine-tuning capability.

5. **Lowest integration effort** — 6.5 SP vs 8 SP (Google) or 12 SP (raw PP-Structure). Leverages existing knowledge from MinerU 1.x integration.

6. **Different extraction approach** — Docling (TableFormer) and MinerU (SLANeXt/PP-TableMagic) use different model architectures for table recognition. This diversity is what makes the consensus layer valuable — two identical models would produce correlated errors.

### Secondary: Google Document AI (future epic)

**Rationale for deferral:**

1. Cloud dependency adds operational complexity (GCP project, auth, billing, network)
2. Per-page cost ($600-$1,500 for initial backlog) needs budget approval
3. No cross-page table stitching — same gap as current Docling
4. Assured Workloads for AU data boundary is a procurement-level decision
5. No fine-tuning capability limits adaptability to new PDF formats

**Rationale for inclusion as future provider:**

1. Different technology stack (cloud ML vs local inference) — truly independent extraction opinion
2. Strong for scanned/degraded PDFs where local OCR may struggle
3. Batch API enables bulk reprocessing of historical documents
4. Australian data residency story is solid when Assured Workloads is configured
5. Extremely simple Python SDK integration — no GPU, no CUDA, no model management

### Rejected: Raw PP-StructureV3

MinerU 2.x wraps PP-StructureV3's table models and adds cross-page stitching, reading order recovery, and document cleanup — while also solving the PaddlePaddle conflict. There is no scenario where raw PP-Structure is preferable to MinerU 2.x.

---

## 8. Consensus Layer Design

### Architecture Overview

```
                    ┌──────────────────────────────────────────┐
                    │          Provider Registry               │
                    │  ┌──────────┐  ┌──────────┐  ┌────────┐ │
                    │  │ Docling   │  │ MinerU   │  │ Future │ │
                    │  │ Adapter   │  │ Adapter   │  │ (GDoc) │ │
                    │  └─────┬────┘  └─────┬────┘  └───┬────┘ │
                    └────────┼─────────────┼───────────┼──────┘
                             │             │           │
                   ┌─────────▼─────────────▼───────────▼──────┐
                   │        Result Normalizer                  │
                   │   Provider-specific → NormalizedRecord[]  │
                   └──────────────────┬───────────────────────┘
                                      │
                   ┌──────────────────▼───────────────────────┐
                   │          Record Matcher                   │
                   │   Stage 1: Key-field anchor matching      │
                   │   Stage 2: Fuzzy string matching          │
                   │   Stage 3: Row position fallback          │
                   └──────────────────┬───────────────────────┘
                                      │
                   ┌──────────────────▼───────────────────────┐
                   │        Consensus Engine                   │
                   │   Per-field confidence-weighted voting     │
                   │   Provider track-record weighting         │
                   └──────────────────┬───────────────────────┘
                                      │
                   ┌──────────────────▼───────────────────────┐
                   │       Conflict Resolver                   │
                   │   Strategy A: Weighted majority vote      │
                   │   Strategy B: Provider priority hierarchy │
                   │   Strategy C: LLM arbitration (high-risk) │
                   │   Strategy D: Human escalation queue      │
                   └──────────────────┬───────────────────────┘
                                      │
                                      ▼
                           ACMExtractionRecord
                           + consensus_metadata
```

### 8.1 Provider Adapter Interface

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class ExtractionProvider(Protocol):
    """
    Provider-agnostic interface. Adding a new provider = implementing
    this protocol + registering in the ProviderRegistry.
    """

    @property
    def provider_id(self) -> str: ...

    async def extract(
        self,
        pdf_path: str,
        page_range: tuple[int, int],
        config: ProviderConfig,
    ) -> NormalizedExtractionResult: ...

    def supports_table_extraction(self) -> bool: ...

    def get_field_confidence(self, field_name: str) -> float: ...
```

Concrete adapters: `DoclingAdapter` (wraps existing `_extract_tables_with_docling()`), `MinerUAdapter` (wraps MinerU 2.x `DocumentConverter`), future `GoogleDocAIAdapter`.

### 8.2 Record Matching

Four-stage matching pipeline, applied after normalization:

| Stage | Algorithm | Handles | Coverage |
|-------|-----------|---------|:--------:|
| 1. Key-field anchor | Exact match on `(building_id, room_id, product, page)` | Clean extractions | ~70-80% |
| 2. Fuzzy string | `rapidfuzz` Jaro-Winkler (codes) + Token Set Ratio (descriptions) | OCR variants | ~15-20% |
| 3. Row position | Same-table index proximity (tiebreaker only) | Same row count, different text | ~5% |
| 4. Embedding semantic | Sentence-transformer cosine similarity | Paraphrase variants | Reserve |

Match thresholds:
- `>= 0.85` composite score → confirmed match
- `0.65 – 0.84` → probable match (flag for review)
- `< 0.65` → distinct records (both preserved)

### 8.3 Confidence Scoring

**Per-field, Calamari-style confidence voting:**

```
For each field in a matched record group:
  1. Each provider emits (value, confidence)
  2. Aggregate by value: weighted_sum = Σ(confidence × provider_weight)
  3. Winner = argmax(weighted_sum)
  4. Consensus score = winner_sum / total_sum
```

**Tier assignment:**

| Tier | Condition | Action |
|------|-----------|--------|
| **HIGH** | All providers agree | Accept automatically |
| **MEDIUM** | 2/3 agree OR supermajority confidence | Accept with flag |
| **LOW** | Only 1 provider found the record | Accept with warning, prioritize human review |
| **CONTESTED** | Providers disagree on high-stakes field | Trigger conflict resolution |

**Provider weights** are per-field-type and dynamically updated based on human review outcomes (Bayesian posterior: `Beta(correct + 2, total + 3)`). Initial weights: all 1.0.

### 8.4 Conflict Resolution

Escalation chain for contested fields:

1. **Weighted majority vote** (default) — cheapest, handles OCR noise
2. **Provider priority hierarchy** (domain-specific) — for known field strengths:
   - Enum fields (`friable`, `result`, `condition`): Docling > MinerU > LLM
   - Free text (`recommendations`, `comments`): LLM > Docling > MinerU
   - Numeric (`quantity`, `sample_number`): MinerU > Docling > LLM
3. **LLM arbitration** (DAFE pattern) — only for high-stakes fields (`result`, `friable`, `risk_status`) where compliance risk is high. Send source text + both values to Claude for adjudication.
4. **Human escalation** — unresolved conflicts queued for officer review in AG Grid with "Conflict" badge

### 8.5 Integration with Existing Architecture

The consensus layer maps to existing patterns:

| Existing Pattern | Consensus Layer Extension |
|-----------------|--------------------------|
| `FallbackId` enum in `strategy_registry.py` | Add `F9_PROVIDER_CONFLICT`, `F10_LLM_ARBITRATION` |
| `FallbackContract` | Add `ConflictResolutionContract` |
| `emit_fallback_telemetry()` | Emit `consensus.tier`, `consensus.agreement_count`, `consensus.provider_votes` |
| `ACMExtractionRecord.extraction_confidence` | Extend to `consensus_metadata: {tier, scores, votes}` |
| `ACMExtractionRecord.data_issues` | Append conflict resolution notes |

---

## 9. Risk Assessment

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|:---------:|:------:|------------|
| R1 | **MinerU 2.x install breaks existing dependencies** — Despite PyTorch compatibility claims, a transitive dependency may conflict | Low | High | Test in a branch first. `pip install mineru --dry-run` to check constraints. Fallback: subprocess bridge pattern if needed. |
| R2 | **MinerU 2.x accuracy differs from MinerU 1.x** — The `paddleocr2torch` port may have subtle numerical differences from native PaddlePaddle | Low | Medium | Benchmark on Broadmeadows + Alexander immediately after integration. Require >= Docling-equivalent accuracy. |
| R3 | **Consensus layer adds latency** — Running 2 providers + matching + voting adds processing time | Medium | Medium | Run providers in parallel (`asyncio.gather`). Matching + voting is < 1s. Net latency ≈ max(provider_A, provider_B). |
| R4 | **Record matching produces false positives** — Two different records matched as "same" | Low | High | Conservative threshold (0.85). Human review for MEDIUM tier. Unit tests with edge cases (similar but different records). |
| R5 | **Record matching produces false negatives** — Same record not matched across providers | Medium | Medium | Records from all providers preserved. Union behavior: if provider A finds a record that B misses, it's kept with LOW confidence. |
| R6 | **GPU memory contention** — Both Docling and MinerU competing for RTX 4090 VRAM | Medium | Medium | Sequential execution (Docling first, then MinerU) rather than concurrent GPU access. Total VRAM: ~4 GB (Docling) + ~8 GB (MinerU) = ~12 GB, well within 24 GB. |
| R7 | **MinerU 2.x version drift** — Rapid releases (v2.0 → v2.7 in 8 months) may break API | Medium | Low | Pin version in `pyproject.toml`. Adapter pattern isolates version-specific code. |
| R8 | **Google Doc AI (future) data sovereignty concerns** — Government stakeholders may reject cloud processing | Medium | High | Mitigated by Assured Workloads + `australia-southeast1` region. But procurement process may delay adoption regardless. |
| R9 | **Consensus layer over-engineering** — For documents where one provider is clearly sufficient | Low | Low | Tiered cost model: Tier 1 = Docling only; Tier 2 = add MinerU on low-confidence results. Consensus is not always-on. |
| R10 | **MinerU models consume disk** — Model weights may be 500 MB - 2 GB | Low | Low | Already managing Docling model cache (~500 MB). Disk is cheap. |

---

## 10. Integration Approach

### MinerU 2.x (implement now)

```
Phase 1: Installation + Validation (1 SP)
  ├── pip install mineru in main .venv/
  ├── Verify torch compatibility (no _CudaDeviceProperties error)
  ├── Verify Docling still works (no regression)
  └── Run MinerU on Broadmeadows PDF, inspect HTML output

Phase 2: Adapter Implementation (2 SP)
  ├── Create MinerUAdapter implementing ExtractionProvider
  ├── HTML → NormalizedRecord normalization
  ├── Column-mapping to ACM field schema
  └── Unit tests for adapter

Phase 3: Consensus Layer Core (2 SP)
  ├── NormalizedRecord schema
  ├── RecordMatcher (stages 1-2)
  ├── ConsensusEngine (weighted voting)
  ├── ConflictResolver (strategies A-B)
  └── Unit tests for matching + voting

Phase 4: Pipeline Integration (1.5 SP)
  ├── Wire into orchestrator.py (parallel extraction)
  ├── Emit consensus telemetry via PipelineLogger
  ├── Benchmark: Broadmeadows + Alexander
  └── Integration tests
```

### Google Document AI (future epic)

```
Prerequisites:
  ├── GCP project with Document AI API enabled
  ├── Service account with AU region restriction
  ├── Assured Workloads evaluation (if government data)
  └── Budget approval for per-page costs

Implementation:
  ├── GoogleDocAIAdapter implementing ExtractionProvider
  ├── Cross-page table stitching post-processor
  ├── Batch processing pipeline for historical backlog
  └── Integration tests + benchmark validation
```

### File Impact Map

| File | Change | Story |
|------|--------|-------|
| `pyproject.toml` | Add `mineru` dependency | Phase 1 |
| `open_notebook/extractors/providers/__init__.py` | New: provider adapter package | Phase 2 |
| `open_notebook/extractors/providers/base.py` | New: `ExtractionProvider` protocol, `NormalizedRecord` | Phase 2 |
| `open_notebook/extractors/providers/docling_adapter.py` | New: wrap existing Docling extraction | Phase 2 |
| `open_notebook/extractors/providers/mineru_adapter.py` | New: MinerU 2.x adapter | Phase 2 |
| `open_notebook/extractors/consensus/matcher.py` | New: record matching engine | Phase 3 |
| `open_notebook/extractors/consensus/engine.py` | New: confidence voting + conflict resolution | Phase 3 |
| `open_notebook/extractors/orchestrator.py` | Modify: wire consensus layer into per-building extraction | Phase 4 |
| `open_notebook/extractors/strategy_registry.py` | Modify: add consensus-related FallbackIds | Phase 4 |
| `open_notebook/extractors/acm_schemas.py` | Modify: add `consensus_metadata` to ACMExtractionRecord | Phase 3 |
| `tests/test_mineru_adapter.py` | New | Phase 2 |
| `tests/test_record_matcher.py` | New | Phase 3 |
| `tests/test_consensus_engine.py` | New | Phase 3 |

---

## 11. Dependency Analysis

### MinerU 2.x in Main Venv

```
mineru v2.7.6 requires:
  torch >= 2.2, < 2.7 (excluding 2.5)     ← Our torch 2.10.0 may be out of range!
  paddleocr2torch                          ← PyTorch-native PaddleOCR port
  opencv-python                            ← Already in our venv (Docling uses it)
  Pillow                                   ← Already present
  numpy                                    ← Already present
  pandas                                   ← Already present
```

**CRITICAL RISK: torch version constraint.** MinerU 2.x as of v2.7.6 requires `torch >= 2.2, < 2.7`. Our main venv has `torch 2.10.0+cu126`, which is ABOVE the upper bound. This needs validation:

1. Check if MinerU has updated its constraint in the latest release
2. If not, check if it actually works with torch 2.10 despite the constraint
3. Fallback: subprocess bridge pattern if the constraint is hard

**Mitigation**: The `paddleocr2torch` package itself may have looser constraints. Test with `pip install mineru --dry-run` first.

### Google Document AI (future)

```
google-cloud-documentai requires:
  google-api-core >= 2.x                   ← No CUDA dependency
  google-cloud-storage (for batch)         ← Optional
  google-cloud-documentai-toolbox          ← Experimental, pin version
```

Zero GPU/CUDA dependency. No venv conflicts. Pure REST client.

### GPU Sharing Strategy

Both Docling and MinerU need CUDA. With 24 GB RTX 4090 VRAM:

| Scenario | Docling VRAM | MinerU VRAM | Total | Fits? |
|----------|:-----------:|:-----------:|:-----:|:-----:|
| Sequential (recommended) | 2-4 GB → freed | 6-10 GB | 10 GB max | Yes |
| Concurrent (risky) | 2-4 GB | 6-10 GB | 8-14 GB | Yes, but fragmentation risk |

**Recommendation**: Run providers sequentially to avoid CUDA memory fragmentation. Use `asyncio` for I/O parallelism but serialize GPU-bound work.

---

## 12. Next Steps

### For the Architect (Winston)

1. **Validate MinerU 2.x torch constraint** — Check if `torch 2.10.0` is supported. If not, determine if subprocess bridge is needed (reverts to ~12 SP effort).
2. **Design the `ExtractionProvider` protocol** as an ADR addition to `adr-tableformer-integration.md`.
3. **Define consensus metadata schema** — extension to `ACMExtractionRecord` for storing per-field agreement data.
4. **Decide on tiered cost model** — Is consensus always-on, or triggered by low-confidence results?

### For the Dev Agent (Amelia)

1. **Test MinerU 2.x installation** — `pip install mineru` in a branch copy of `.venv/`. Verify no conflicts with torch, docling, langchain.
2. **Run MinerU on Broadmeadows** — Capture HTML output, compare table quality to Docling DataFrames.
3. **Implement provider adapter package** — Start with `ExtractionProvider` protocol and `DoclingAdapter` (refactoring existing code).
4. **Benchmark** — Both providers on both benchmark documents. Capture per-field accuracy.

### For the PM (John)

1. **Create Epic 31: Multi-Provider Extraction** with stories:
   - E31-S1: MinerU 2.x integration + validation (2 SP)
   - E31-S2: Provider adapter framework (3 SP)
   - E31-S3: Consensus layer core (3 SP)
   - E31-S4: Pipeline integration + benchmark (2 SP)
   - E31-S5: Google Document AI adapter (future, 8 SP)
2. **Budget discussion** — Google Doc AI costs for production scale
3. **Dependency tracking** — E31 depends on E30 completion (Salesforce schema must be stable before adding providers)

### For the QA Agent (Quinn)

1. **Benchmark ground truth** — Ensure Broadmeadows + Alexander ground truth CSVs are complete and field-level accurate
2. **Test plan for consensus** — Scenarios: both providers agree, providers disagree on enum field, one provider misses a record, cross-page table found by MinerU but not Docling
3. **Regression suite** — Existing 31/31 and 36/43 accuracy must not regress

---

## Appendix A: Sources

### Google Document AI
- [Form Parser | Google Cloud](https://docs.google.com/document-ai/docs/form-parser)
- [Gemini Layout Parser | Google Cloud](https://docs.google.com/document-ai/docs/layout-parse-chunk)
- [Pricing | Google Cloud](https://cloud.google.com/document-ai/pricing)
- [Australia Data Boundary | Assured Workloads](https://docs.google.com/assured-workloads/docs/control-packages/australia-data-boundary-support)
- [Document AI Security](https://docs.google.com/document-ai/docs/security)
- [Toolbox - Table to DataFrame](https://docs.google.com/document-ai/docs/samples/documentai-toolbox-table)

### PaddleOCR / PP-StructureV3
- [PP-StructureV3 Introduction](http://www.paddleocr.ai/main/en/version3.x/algorithm/PP-StructureV3/PP-StructureV3.html)
- [PaddleOCR 3.0 Technical Report](https://arxiv.org/html/2507.05595v1)
- [PP-TableMagic Overview](https://aisharenet.com/en/pp-tablemagic/)
- [PaddleOCR PyPI](https://pypi.org/project/paddleocr/)
- [PyTorch Conflict Issue #12046](https://github.com/PaddlePaddle/PaddleOCR/issues/12046)
- [Table Structure Recognition (PaddleX)](https://paddlepaddle.github.io/PaddleX/3.3/en/module_usage/tutorials/ocr_modules/table_structure_recognition.html)

### MinerU
- [MinerU GitHub](https://github.com/opendatalab/MinerU)
- [MinerU 2.0 PyPI](https://pypi.org/project/mineru/2.0.0/)
- [MinerU 2.5 Technical Paper](https://wangbindl.github.io/publications/MinerU2_5.pdf)

### Consensus Layer Patterns
- [Calamari OCR Ensemble Voting](https://calamari-ocr.readthedocs.io/en/latest/doc.command-line-usage.html)
- [DAFE: Dynamic Arbitration Framework](https://arxiv.org/html/2503.08542v1)
- [deepdoctection Multi-Backend](https://github.com/deepdoctection/deepdoctection)
- [Microsoft Table Transformer](https://github.com/microsoft/table-transformer)
- [Confidence Scoring Systems - Extend AI](https://www.extend.ai/resources/best-confidence-scoring-systems-document-processing)
- [Entity Resolution Introduction](https://medium.com/@adev94/entity-resolution-an-introduction-fb2394d9a04e)

### OmniDocBench
- [OmniDocBench (CVPR 2025)](https://github.com/opendatalab/OmniDocBench)

---

*Technical Research — ACM-AI V3 Multi-Provider Table Extraction*
*Generated 2026-03-02*
