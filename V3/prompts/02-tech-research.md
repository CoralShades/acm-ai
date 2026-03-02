# 02: Technical Research — Multi-Provider Extraction Evaluation

> **BMAD Command:** `/bmad-bmm-technical-research`
> **Agent:** Mary — 📊 Business Analyst
> **Depends On:** None (can run in parallel with P0 and 01)
> **Output:** `V3/output/tech-research-extraction-providers.md`
> **Run in:** Fresh context window
> **Tools:** Context7 MCP for library documentation

---

## Pre-Read Documents

The agent should read these before starting:
- `V3/output/e30-multi-agent-audit-unified.md` — Section: "Amelia (Dev) — Unified Findings" for current extraction pipeline details
- `docs/architecture/e29-architecture-delta.md` — Current pipeline architecture
- `docs/architecture/e26-table-extraction-technical-design.md` — Docling/TableFormer design
- `docs/architecture/adr-tableformer-integration.md` — TableFormer ADR
- `open_notebook/extractors/orchestrator.py` — Current extraction orchestrator (scan structure, don't deep-read)
- `V3/output/solution-architecture-v3.md` — Client architecture requirements (from P0)

---

## Prompt

```text
/bmad-bmm-technical-research

## Research Topic: Multi-Provider Table Extraction for ACM-AI V3

### Context

ACM-AI extracts asbestos register data from PDF documents (SAMP reports). The current pipeline uses:
- **PyMuPDF** → raw text extraction (proven, 100% reliable)
- **Docling Direct API + TableFormer** → structured table extraction (93.5% raw accuracy on Broadmeadows)
- **LLM (via OpenRouter)** → interpretation and field mapping

Performance:
- Broadmeadows (1 building, 31 records): 31/31 (100%) with full pipeline
- Alexander (6 buildings, 43 records): 36/43 (~84%) after E28 fixes
- **Untested on 2000+ production documents from various consulting firms** — this is the risk

### Research Goal

Evaluate two additional extraction providers to create a triple-provider parallel extraction architecture with a consensus layer. The strategy is: **design for all 3, implement Docling + 1 other now, third provider as future epic.**

### Provider 1: Google Document AI

**Use Context7 MCP** to fetch current documentation for Google Document AI (Form Parser, Table extraction).

Research areas:
1. **Form Parser capabilities** — structured table extraction accuracy on complex PDF tables
2. **Cross-page table detection** — can it stitch tables spanning multiple pages? (critical — Broadmeadows page 8 overflow is a known gap)
3. **Cell-level confidence scores** — granularity of confidence metadata
4. **Pricing model** — cost per page at scale (2000+ documents, 10-50 pages each)
5. **Python SDK integration** — `google-cloud-documentai` library, how it fits alongside FastAPI
6. **Output format** — can we get structured DataFrames compatible with our `acm_table_section` storage?
7. **Batch processing** — async/batch API for large document sets
8. **Privacy/compliance** — data residency options (Australian government data)

### Provider 2: PaddleOCR PP-Structure

**Use Context7 MCP** to fetch current documentation for PaddleOCR and PP-Structure table recognition.

Research areas:
1. **Table detection + structure recognition** — accuracy on complex asbestos register tables (merged cells, multi-row headers)
2. **Fine-tuning capability** — can we fine-tune on our specific SAMP table formats? What data is needed?
3. **GPU requirements** — will it run efficiently on RTX 4090 (local)? Memory footprint?
4. **PaddlePaddle dependency** — the `paddlepaddle-gpu` package previously conflicted with `torch 2.10.0+cu126` in the main venv. What's the current state? Can it coexist or does it need the isolated `.venv-mineru/` pattern?
5. **PP-Structure vs MinerU** — MinerU uses PaddleOCR under the hood. We previously integrated MinerU but removed it (Docling replaced it). How does raw PP-Structure compare to MinerU's table extraction? Is PP-Structure strictly better/simpler?
6. **Output format** — HTML tables? DataFrames? How to map to our `acm_table_section` schema
7. **Cross-page table handling** — does PP-Structure handle tables spanning pages?
8. **Integration pattern** — subprocess bridge (like MinerU) or direct import?

### Provider 3: Existing Docling + PyMuPDF (Baseline)

For comparison, document:
1. Current accuracy on Broadmeadows + Alexander
2. Known gaps (page 8 overflow, below TableFormer detection threshold)
3. Current `_recover_no_access_records()` regex fallback effectiveness
4. Processing speed (target: <30s for 20-page PDF)

### Consensus Layer Design

Research how to design a provider-agnostic consensus layer:
1. **Record matching** — How to match "same record" across providers with different output formats
2. **Confidence scoring** — Records found by 2+ providers → HIGH, 1 provider → MEDIUM, 0 → LOW
3. **Conflict resolution** — When providers disagree on field values, how to resolve
4. **Architecture pattern** — Provider adapter interface, result normalization, consensus voting

### Required Output Format

Produce a research document at `V3/output/tech-research-extraction-providers.md` with:

1. **Executive Summary** — Which 2 providers to implement now and why
2. **Provider Comparison Matrix** — features, accuracy potential, cost, GPU requirements, integration effort (SP estimate), cross-page support, fine-tunability
3. **Recommendation** — Primary + secondary provider, with rationale
4. **Consensus Layer Design** — High-level architecture for the provider adapter + consensus voting pattern
5. **Risk Assessment** — What could go wrong, mitigation strategies
6. **Integration Approach** — How each provider fits into the existing pipeline (subprocess? direct? Docker?)
7. **Dependency Analysis** — Python package conflicts, venv isolation needs, GPU sharing
8. **Next Steps** — What the Architect and Dev agents need to know

### Constraints
- Do NOT recommend MinerU revival unless PP-Structure is clearly inferior AND MinerU solves problems PP-Structure cannot
- Do NOT assume cloud costs are irrelevant — VAEA processes government documents
- Consider the two-venv pattern already established (.venv/ + .venv-mineru/) as a proven isolation approach
- The RTX 4090 is available for local GPU workloads
```

---

## Verification Checklist

After running:
- [ ] `V3/output/tech-research-extraction-providers.md` exists
- [ ] Contains provider comparison matrix with quantified estimates
- [ ] Contains clear recommendation for which 2 providers to implement
- [ ] Contains consensus layer design section
- [ ] Addresses PaddlePaddle/torch conflict and venv isolation
- [ ] Includes cost analysis for Google Document AI
