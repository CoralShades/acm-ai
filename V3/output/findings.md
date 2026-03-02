# V3 Planning — Findings Log

## Key Findings from Pre-Read

1. **MinerU 2.x eliminates PaddlePaddle conflict** — paddleocr2torch is PyTorch-native. BUT torch constraint (2.2-2.7) conflicts with our torch 2.10.0+cu126. Subprocess bridge may still be needed.
2. **E29 S1-S4 completed** — JSON parser, benchmark harness, unified orchestrator, capability registry. Foundation retained.
3. **SF alignment is massive** — 143 Building__c fields, 154 Item__c fields, 18+23 picklists, 2 dependency chains (36 valid Friability×Classification combos, 114 BuildingType→13 Category).
4. **Multi-agent audit consensus** — 14 stories, ~48 SP for SF alignment alone (revised from SCP's 28 SP).
5. **Docling has no cross-page stitching** — MinerU 2.x does. Critical for production documents.
6. **Google Doc AI deferred** — cloud dependency, per-page cost ($600-1500), no fine-tuning.
7. **Solution Architecture V3** — Client-facing spec defines 5-phase pipeline, per-building extraction, SF schema drives everything.
8. **Heuristic rules** — 60+ regex patterns carry forward. BAR vocabulary must transition to SF vocabulary.
9. **Current BAR "Good" → SF "Stable"** — Cross-cutting vocabulary mismatch affects 33+ test files.
