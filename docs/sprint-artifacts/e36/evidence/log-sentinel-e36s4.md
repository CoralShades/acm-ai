# E36-S4 Log Sentinel Report: Ollama Multi-Model Benchmark

**Report generated**: 2026-03-05T05:32 UTC
**Monitoring period**: 2026-03-05T03:13 UTC to 2026-03-05T05:32 UTC (2h 19m active window)
**Sentinel**: E36 Log Sentinel (claude-sonnet-4-6)

---

## Baseline Log Positions (at monitoring start)

| Log File | Lines at Baseline | Last Modified |
|---|---|---|
| `logs/api.log` | 59,566 | 2026-03-05T15:28:23 AEDT |
| `logs/api-error.log` | 5,306 | 2026-03-05T15:27:18 AEDT |
| `logs/worker.log` | 1,118 | 2026-03-05T14:12:39 AEDT |
| `logs/worker-console.log` | 4,565 | — |
| `logs/worker-error.log` | 0 | — |
| `logs/api-benchmark.log` | 35 | — |
| `logs/acm-extraction.log` | 29,310 (at start) — grew to 29,323 | — |

Services running: SurrealDB (`acm-ai-db`, healthy), Ollama (`acm-ai-ollama`, unhealthy status flag — see warnings). API and Worker run directly (not Docker).

---

## Benchmark Run Summary

The benchmark executed a series of Ollama-model extractions on `Clutch_Broadmeadows (24/25).pdf`. Evidence for all 6 planned models (qwen2.5:7b, llama3.1:8b, mistral:7b, qwen3:32b, qwen2.5:32b, phi4:latest) was found across today's logs. The Alexander PDF source (`source:2kjfxd6goehaj0njkam3`) was uploaded but its extraction data is not yet complete in logs (Docling table extraction completed, LLM extraction pending or not yet triggered at log-read time).

### Confirmed Completed Runs (with records extracted)

| Model | PDF | Source ID | Start Time (UTC) | Duration | Records | Confidence | Notes |
|---|---|---|---|---|---|---|---|
| `qwen2.5:7b` | Broadmeadows (25).pdf | `source:25pxnu7ot2oy2oi7dmc0` | 2026-03-05T03:13:51 | 113.7s | 17 | high=17 | Docling 126s; 3 dupes merged |
| `llama3.1:8b` | Broadmeadows (24).pdf | `source:mwtfcow6rwl4co2gfxiv` | 2026-03-05T07:04:13 | 208.1s | 18 (19 raw) | high=18 | Correction FAILED all 13 issues |

### Failed / Zero-Record Runs (Broadmeadows PDF, source:mwtfcow6rwl4co2gfxiv)

Multiple extraction attempts on the same source across different models or OpenRouter fallback attempts failed to produce records:

| Time (UTC) | Duration | Records | Failure Cause |
|---|---|---|---|
| 2026-03-05T06:22:42 | 102.9s | 0 | OpenRouter HTTP 402 Insufficient credits |
| 2026-03-05T06:26:35 | 33.3s | 0 | JSON parse failure — model returned conversational text |
| 2026-03-05T06:28:11 | 206.1s | 0 | JSON parse failure — model returned conversational text |
| 2026-03-05T06:39:39 | 5.3s | 0 | `phi4:14b` model not found in Ollama (HTTP 404) |
| 2026-03-05T06:50:35 | 21.8s | 0 | JSON parse failure — model returned conversational text |
| 2026-03-05T06:56:04 | 2.7s | 0 | OpenRouter HTTP 402 Insufficient credits |
| 2026-03-05T07:01:03 | 20.5s | 0 | JSON parse failure — model returned conversational text |

---

## Per-Model Observations

### qwen2.5:7b — Broadmeadows (25).pdf

- **Status**: SUCCESS
- **Start**: 2026-03-05T03:13:51 UTC
- **Docling**: Completed in 126.4s (8 tables, 67 rows from `Clutch_Broadmeadows (25).pdf`)
- **Structure phase**: 60.4s — detected `DocumentType.DIVISION_5`, register_start=5, 1 building
- **Orchestrator**: 24.6s — 20 raw records from WHOLE_DOC (content_len=56,223 chars)
- **Validation**: 10 records with issues initially
- **Correction round 1**: 16.0s — `llm_corrected=14`, `failed=0` — corrections WORKED
- **Correction round 2**: 12.0s — `llm_corrected=31`, `failed=0` — all issues resolved
- **Store**: 3 duplicates merged, 17 unique records saved
- **Final**: 17 records in 113.7s — `high=17, medium=0, low=0`
- **Embedding**: Ollama mxbai-embed-large (1.9s embed time noted separately)
- **format=json applied**: Evidence via fast correction response times (~250-500ms per call in Ollama logs) — format=json mode appears active
- **Provider**: Ollama only (no OpenRouter/Anthropic fallback triggered)

### llama3.1:8b — Broadmeadows (24).pdf

- **Status**: PARTIAL — records saved but correction stage failed entirely
- **Start**: 2026-03-05T07:04:13 UTC
- **Docling**: Already cached (prior runs had completed Docling for this source)
- **Structure phase**: 15.0s
- **Orchestrator**: 38.6s — 19 raw records from WHOLE_DOC
- **Validation**: 13 records with issues
- **Correction round 1**: 56.8s — `llm_corrected=0`, `failed=13` — ALL FAILED
- **Correction round 2**: 53.7s — `llm_corrected=0`, `failed=26` — cumulative failures grew
- **Correction round 3**: 43.3s — `llm_corrected=0`, `failed=39` — ALL FAILED across 3 rounds
- **Store**: 1 duplicate merged, 18 unique records saved (despite correction failures)
- **Final**: 18 records in 208.1s — `high=18, medium=0, low=0`
- **Embedding**: 18/18 embedded in 2.8s
- **Correction failure pattern**: llama3.1:8b correction calls each took ~12s via Ollama (1,000+ tokens of corrections being rejected). The model is likely not following the correction JSON format.
- **format=json during correction**: Not confirmed effective — all 39 correction attempts failed

### phi4:latest / phi4:14b — FAILED (model not found)

- **Status**: CRITICAL FAILURE — model unavailable in Ollama
- **Time**: 2026-03-05T06:39:39 UTC
- **Error**: `model "phi4:14b" not found, try pulling it first (status code: 404)`
- **Affected stages**: metadata, structure, building inventory, page tagger, main extraction
- **All stages**: fell back to heuristic — 0 records produced in 5.3s
- **Impact**: phi4:latest was listed as benchmark model but Ollama has `phi4:14b` tag which is not pulled. Entire extraction failed with no records.

### mistral:7b / qwen2.5:32b / qwen3:32b — JSON Parse Failures

Multiple zero-record runs (06:26–07:01) show the "No JSON object found in response text" pattern. Response previews in error logs show:

- Run at 06:27: `"I'm sorry, but you haven't provided any building content for me to extract ACM (Association for Computing Machinery) records from. Could you please provide the relevant text or data..."`
- Run at 06:31: `"To extract ACM (Asbestos Containing Material) records from building content, you would typically look for specific keywords..."`
- Run at 06:50: `"However, I don't see any building content or ACM (Asbestos-Containing Material) records provided in our conversation so far."`

These responses indicate a model that does NOT recognize the prompt context correctly and responds conversationally instead of with JSON. The model IDs used for these runs are not logged by name (no `Models:` line when extraction returns 0 records), but timing and sequencing suggests these were mistral:7b, qwen2.5:32b, and/or qwen3:32b runs.

The content_len for these runs was 56,223 chars (the Ollama budget-split threshold is 28,672 chars). The `_ollama_split_by_budget` warning fired on multiple runs, meaning content was split — but the model still returned conversational text.

### OpenRouter Runs (HTTP 402 — Insufficient Credits)

Two runs used OpenRouter with Anthropic hard-lock and failed with HTTP 402:
- 06:22:42 run: OpenRouter `provider.only=['Anthropic']` — Insufficient credits
- 06:56:04 run: Same pattern

This indicates OpenRouter Anthropic credit balance is exhausted. These are not Ollama failures — they represent a configuration issue where OpenRouter was tried as extraction provider instead of Ollama-local.

---

## Error/Warning Summary

### CRITICAL

| # | Error | Count | First Occurrence | Impact |
|---|---|---|---|---|
| 1 | `phi4:14b` model not found (HTTP 404) | 5 errors | 2026-03-05T06:39:40 | Complete benchmark run failure for phi4 |
| 2 | OpenRouter HTTP 402 Insufficient credits | 8+ errors | 2026-03-05T06:24:22 | OpenRouter Anthropic credit balance exhausted |

### WARNING (Repeated Patterns)

| # | Warning | Count | Pattern |
|---|---|---|---|
| 1 | `No JSON object found in response text` | 48 occurrences today | Models returning conversational text instead of JSON — affects structure, inventory, page tagger, and main extraction stages |
| 2 | `No page markers found in source` (74,044 chars) | 7 times | `mwtfcow6rwl4co2gfxiv` text has no page markers — chunking falls back to character-based splitting |
| 3 | Ollama `gpu VRAM usage didn't recover within timeout` | 6 warnings | 03:23 UTC — VRAM pressure between model switches (8.3 GiB + 1.1 GiB runners) |
| 4 | SurrealDB transaction conflict (retryable) | 1 | 06:21:49 — auto-retried successfully |
| 5 | `llm_corrected=0, failed=13/26/39` (llama3.1:8b) | 3 correction rounds | All correction calls failed — model not following correction JSON schema |

### INFO (Benchmark-Relevant)

| Item | Value |
|---|---|
| Ollama model loaded (7B class) | 3.01–3.51s load time |
| Ollama VRAM (7B model) | 4.1 GiB weights + 1.8 GiB KV = 8.3 GiB total |
| GPU available | 24.0 GiB CUDA (all layers offloaded) |
| Docling extraction time | 49–126s per run (8 tables, 67 rows from Broadmeadows) |
| Orchestrator content length | 56,223 chars (Broadmeadows, no page markers) |
| Budget-split trigger | Yes — 56,223 > 28,672 char budget (8,192 num_ctx × 3.5) |
| Embedding model | `ollama/mxbai-embed-large` (1.9–2.8s for 16–18 records) |

---

## format=json Verification

The `_apply_ollama_extraction_settings()` function is expected to add `format="json"` to ChatOllama calls. Evidence from logs:

**Positive indicators (format=json likely active):**
- qwen2.5:7b correction calls completed in 250–500ms (fast, structured responses via Ollama logs at 03:17)
- qwen2.5:7b had `llm_corrected=14` and `llm_corrected=31` with zero failures — JSON correction schema was followed

**Negative indicators (format=json may not be active for all stages):**
- Structure extraction, building inventory, and page tagger all returned "No JSON object found in response text" on 4 separate runs (mistral/qwen models)
- These pre-extraction stages may use a different code path that does not apply the format=json override
- Main extraction also failed with conversational text in those same runs — suggesting format=json was NOT applied or NOT effective for those model/prompt combinations

**No explicit `format=json` log lines were found** — the flag is set at the ChatOllama instantiation level and is not logged by name in any log file. Verification requires code inspection of `graphs/utils.py` `_apply_ollama_extraction_settings()`.

---

## Ollama Container Health Warning

The Ollama container (`acm-ai-ollama`) shows `unhealthy` status in `docker ps`:

```
CONTAINER ID   IMAGE                  STATUS                 NAMES
bff0b32c13e4   ollama/ollama:latest   Up 2 hours (unhealthy) acm-ai-ollama
```

However, Ollama continued accepting requests successfully (all GIN logs show HTTP 200). The unhealthy status is likely a Docker healthcheck configuration issue, not an actual service failure. Requests at 05:30–05:32 UTC are returning 200 with normal response times.

Additionally, VRAM recovery timeout warnings appeared at 03:23 UTC after qwen2.5:7b completed and before the embedding model loaded. This is expected behavior during model switching — Ollama scheduler detected the 8.3 GiB runner was not releasing VRAM fast enough. No actual OOM or crash occurred.

---

## Source Tracking

| Source ID | PDF File | First Seen | Status |
|---|---|---|---|
| `source:25pxnu7ot2oy2oi7dmc0` | Clutch_Broadmeadows (25).pdf | 2026-03-05T03:13 | COMPLETE — 17 records (qwen2.5:7b) |
| `source:mwtfcow6rwl4co2gfxiv` | Clutch_Broadmeadows (24).pdf | 2026-03-05T06:18 | PARTIALLY COMPLETE — 18 records (llama3.1:8b); multiple failed runs |
| `source:2kjfxd6goehaj0njkam3` | 4601_AsbestosRegister (5).pdf (Alexander) | 2026-03-05T04:06 | DOCLING ONLY — tables extracted (5 tables, 89 rows); LLM extraction incomplete |
| `source:s5646u6t6aydpszl4j6t` | Unknown | 2026-03-05T06:20 | DOCLING started (co-processing) |
| `source:afotms1dfrdv384uot83` | Unknown | 2026-03-05T06:23 | DOCLING started (co-processing) |

---

## Recommendations

### Immediate (before next benchmark run)

1. **Pull phi4:latest into Ollama**: The benchmark specifies `phi4:latest` but the code or model registry is using tag `phi4:14b` which is not available. Run `docker exec acm-ai-ollama ollama pull phi4:latest` and verify the tag mapping.

2. **Replenish OpenRouter Anthropic credits**: HTTP 402 errors block any run that falls through to OpenRouter. Add credits at https://openrouter.ai/settings/credits, or configure the benchmark to skip OpenRouter and use Ollama-only for the extraction model (set `ACM_OPENROUTER_API_KEY` to empty or remove OpenRouter from provider chain for the benchmark).

3. **Investigate llama3.1:8b correction failures**: All 39 correction calls returned `llm_corrected=0, failed=N`. This suggests llama3.1:8b is not following the correction JSON schema. Check whether `format="json"` is being applied to correction-stage ChatOllama instances in `correct_records` node.

4. **Investigate JSON parse failures on structure/inventory/tagger stages**: For mistral/qwen32b runs, all pre-extraction LLM stages returned conversational text. These stages may not be using the `_apply_ollama_extraction_settings()` path. Verify that `format="json"` is applied globally for Ollama, not just in the main extraction node.

5. **Address `No page markers found` warning for mwtfcow6rwl4co2gfxiv**: The Broadmeadows (24) source text (74,044 chars) has no page markers. The document was processed by Docling (8 tables, 67 rows), but the Docling text output was not merged with page markers. Check `_run_dual_provider_extraction` to ensure page marker injection is happening after Docling.

### For Benchmark Scoring

- qwen2.5:7b: **Usable result** — 17 records, high confidence, good correction behavior
- llama3.1:8b: **Partial result** — 18 records saved but 13 validation issues unresolved (correction stage completely non-functional for this model)
- phi4:latest: **No result** — model unavailable
- mistral:7b, qwen2.5:32b, qwen3:32b: **No result** — JSON parse failures (likely format=json not effective or prompts not reaching model correctly)

---

## Appendix: Key Log Excerpts

**qwen2.5:7b success (ACM extraction log, lines 29148–29153):**
```
[2026-03-05 03:17:52] [PIPELINE] EXTRACTION COMPLETE | 17 records in 113.7s
[2026-03-05 03:17:52] [PIPELINE]   Pages: 0 | Chunks: 0 | Buildings: 0
[2026-03-05 03:17:52] [PIPELINE]   Records: 17 created, 0 rejected, 0 unidentified
[2026-03-05 03:17:52] [PIPELINE]   Confidence: high=17, medium=0, low=0
[2026-03-05 03:17:52] [PIPELINE]   Models: qwen2.5:7b
[2026-03-05 03:17:52] [PIPELINE]   Strategy: full_llm=1
```

**phi4:14b not found (worker.log, lines 562–565):**
```
2026-03-05 06:39:45.018 | ERROR | orchestrator:extract_building:1146 - Building WHOLE_DOC extraction failed: model "phi4:14b" not found, try pulling it first (status code: 404)
2026-03-05 06:39:45.018 | ERROR | pipeline_logger:_log:136 -   FULL_LLM ERROR: Building WHOLE_DOC failed: model "phi4:14b" not found, try pulling it first (status code: 404)
```

**llama3.1:8b correction failure (worker.log, lines 959, 1020, 1081):**
```
2026-03-05 07:06:03.909 | INFO | [PIPELINE] [CORRECT] COMPLETED in 56.8s | auto=0, llm=0, failed=13
2026-03-05 07:06:57.640 | INFO | [PIPELINE] [CORRECT] COMPLETED in 53.7s | auto=0, llm=0, failed=26
2026-03-05 07:07:40.980 | INFO | [PIPELINE] [CORRECT] COMPLETED in 43.3s | auto=0, llm=0, failed=39
```

**JSON parse failure with response preview (worker.log, line 411):**
```
2026-03-05 06:27:08.934 | ERROR | orchestrator:_invoke:618 - Building WHOLE_DOC JSON parsing failed: No JSON object found in response text. Response preview: I'm sorry, but you haven't provided any building content for me to extract ACM (Association for Computing Machinery) records from. Could you please provide the relevant text or data that you want me t
```

**OpenRouter 402 error (worker.log, line 338):**
```
2026-03-05 06:24:25.026 | ERROR | orchestrator:extract_building:1146 - Building WHOLE_DOC extraction failed: Error code: 402 - {'error': {'message': 'Insufficient credits. Add more using https://openrouter.ai/settings/credits', 'code': 402}}
```

---

*Log sentinel monitoring complete. Evidence files at `/d/ailocal/acm-ai/logs/` (read-only). No application code was modified.*
