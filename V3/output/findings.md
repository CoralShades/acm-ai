# V3 Planning — Findings Log

## Key Findings from Pre-Read

1. **MinerU 2.x torch COMPATIBLE** — pyproject.toml requires `torch>2.6.0,<3`. Our torch 2.10.0+cu126 satisfies both bounds. Direct install in main venv. No subprocess bridge needed. PaddlePaddle/paddleocr2torch NOT listed as direct deps.
2. **E29 S1-S4 completed** — JSON parser, benchmark harness, unified orchestrator, capability registry. Foundation retained.
3. **SF alignment is massive** — 143 Building__c fields, 154 Item__c fields, 18+23 picklists, 2 dependency chains (36 valid Friability×Classification combos, 114 BuildingType→13 Category).
4. **Multi-agent audit consensus** — 14 stories, ~48 SP for SF alignment alone (revised from SCP's 28 SP).
5. **Docling has no cross-page stitching** — MinerU 2.x does. Critical for production documents.
6. **Google Doc AI deferred** — cloud dependency, per-page cost ($600-1500), no fine-tuning.
7. **Solution Architecture V3** — Client-facing spec defines 5-phase pipeline, per-building extraction, SF schema drives everything.
8. **Heuristic rules** — 60+ regex patterns carry forward. BAR vocabulary must transition to SF vocabulary.
9. **Current BAR "Good" → SF "Stable"** — Cross-cutting vocabulary mismatch affects 33+ test files.
10. **Building_Sub_Category__c does NOT exist** — Confirmed absent from `building_fields_summary.md`. Dependency chain is BuildingType→Category only (2 levels, not 3). E30-S4 simplified.
11. **Validation policy: WARN on edit, REJECT on export** — Officers see inline AG Grid badges (red/orange/yellow). Export grayed out until all validation errors resolved.
12. **OpenRouter MUST remain fully supported** — Not just Anthropic direct. Fallback chain: Anthropic → OpenRouter. Admin toggle. Esperanto retained for non-extraction tasks.
13. **Ollama model candidates**: `llama3.1:8b`, `qwen2.5:7b`, `mistral:7b` for classification + enrichment evaluation spike (E32-S6).
14. **MinerU has 3 backends since v2.7.0** — pipeline (fast, ~6GB), VLM (1.2B param vision model, ~10GB, highest accuracy), hybrid (auto-routes, default). Hybrid recommended for production. VLM processes page IMAGES (vision-based), fundamentally different from Docling (structure-based) — maximizes consensus diversity.
15. **Alexander 0/43 is a completionState bug, NOT extraction** — JSON parsing bug in orchestrator path (E27-related). MinerU has zero effect. Fix completionState separately to get baseline ~40/43, then measure MinerU delta.
16. **CUDA 12.6 compat** — low risk. Torch handles CUDA internally. One source claims 12.8+ needed for MinerU VLM. Verify in E31-S1 install step.
