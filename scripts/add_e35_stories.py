"""One-time script to add E35 stories to prd.json."""
import json
import sys

prd_path = "prd.json"
d = json.load(open(prd_path, encoding="utf-8"))

# Check if E35 stories already exist
existing_e35 = [s for s in d["stories"] if s["id"].startswith("E35")]
if existing_e35:
    print(f"E35 stories already exist ({len(existing_e35)}). Skipping.")
    sys.exit(0)

e35_stories = [
    {
        "id": "E35-S1",
        "title": "Fix Sync Upload asyncio.run() Error",
        "epic": "E35",
        "sprint": "V3-8",
        "storyPoints": 2,
        "riskLevel": "LOW",
        "storyType": "backend",
        "complexity": "simple",
        "priority": "P1",
        "dependencies": [],
        "acceptanceCriteria": [
            "AC1: Sync upload path uses await instead of asyncio.run() -- no RuntimeError",
            "AC2: POST /api/sources with async_processing=false returns 200",
            "AC3: Async upload path unchanged",
            "AC4: Unit test covers both sync and async paths",
        ],
        "keyFiles": ["commands/source_commands.py", "api/routers/sources.py"],
        "techSpecFile": None,
        "implementedDate": None,
        "notes": "",
        "passes": False,
    },
    {
        "id": "E35-S2",
        "title": "Persist Model Defaults to SurrealDB",
        "epic": "E35",
        "sprint": "V3-8",
        "storyPoints": 2,
        "riskLevel": "LOW",
        "storyType": "backend",
        "complexity": "simple",
        "priority": "P1",
        "dependencies": [],
        "acceptanceCriteria": [
            "AC1: PUT /api/models/defaults writes to SurrealDB settings record",
            "AC2: GET /api/models/defaults reads from SurrealDB, falls back to in-memory",
            "AC3: Defaults survive API restart",
            "AC4: Migration creates settings table",
            "AC5: Unit test verifies persistence",
        ],
        "keyFiles": [
            "api/routers/models.py",
            "open_notebook/database/repository.py",
            "migrations/",
        ],
        "techSpecFile": None,
        "implementedDate": None,
        "notes": "",
        "passes": False,
    },
    {
        "id": "E35-S3",
        "title": "Ollama Extraction Hardening",
        "epic": "E35",
        "sprint": "V3-8",
        "storyPoints": 3,
        "riskLevel": "MEDIUM",
        "storyType": "backend",
        "complexity": "moderate",
        "priority": "P0",
        "dependencies": [],
        "acceptanceCriteria": [
            "AC1: _apply_ollama_extraction_settings() sets format=json on all Ollama models",
            "AC2: num_ctx set to 32768 (or OLLAMA_NUM_CTX) at model creation, not post-hoc mutation",
            "AC3: _split_content_by_char_budget() uses character-based multi-chunking (no hard truncation)",
            "AC4: _ollama_split_by_budget() reads actual num_ctx from model",
            "AC5: Non-Ollama models bypass all Ollama settings",
            "AC6: OLLAMA_MAX_CONTENT_CHARS env override takes priority",
            "AC7: Unit tests cover all scenarios",
        ],
        "keyFiles": [
            "open_notebook/graphs/utils.py",
            "open_notebook/extractors/orchestrator.py",
            "tests/test_ollama_chunking.py",
        ],
        "techSpecFile": None,
        "implementedDate": None,
        "notes": "",
        "passes": False,
    },
    {
        "id": "E35-S4",
        "title": "Anthropic Direct Provider Priority in Primary Path",
        "epic": "E35",
        "sprint": "V3-8",
        "storyPoints": 3,
        "riskLevel": "MEDIUM",
        "storyType": "backend",
        "complexity": "moderate",
        "priority": "P0",
        "dependencies": ["E35-S3"],
        "acceptanceCriteria": [
            "AC1: provision_langchain_model() follows Ollama-Anthropic-OpenRouter when model_type=extraction and no explicit model_id",
            "AC2: Uses ACM_ANTHROPIC_API_KEY (never bare ANTHROPIC_API_KEY)",
            "AC3: When Ollama unavailable, Anthropic Direct tried next (not OpenRouter)",
            "AC4: Integration test: OLLAMA_API_BASE unset + ACM_ANTHROPIC_API_KEY set = Anthropic used",
            "AC5: Existing fallback function remains as secondary safety net",
            "AC6: DB-stored model preferences still override when explicitly set",
        ],
        "keyFiles": [
            "open_notebook/graphs/utils.py",
            "api/model_provisioning.py",
            "tests/test_openrouter_provider_routing.py",
        ],
        "techSpecFile": None,
        "implementedDate": None,
        "notes": "",
        "passes": False,
    },
    {
        "id": "E35-S5",
        "title": "SSE Terminal Event for Completed Jobs",
        "epic": "E35",
        "sprint": "V3-8",
        "storyPoints": 2,
        "riskLevel": "LOW",
        "storyType": "frontend",
        "complexity": "simple",
        "priority": "P2",
        "dependencies": [],
        "acceptanceCriteria": [
            "AC1: SSE endpoint returns immediate {type: complete} for completed jobs",
            "AC2: Frontend SSE hook closes cleanly after terminal event",
            "AC3: No console errors on completed extraction page",
            "AC4: Unit test for SSE endpoint with completed job",
        ],
        "keyFiles": [
            "frontend/src/hooks/useExtractionSSE.ts",
            "api/routers/acm.py",
        ],
        "techSpecFile": None,
        "implementedDate": None,
        "notes": "",
        "passes": False,
    },
    {
        "id": "E35-S6",
        "title": "V3 Building Record Backfill",
        "epic": "E35",
        "sprint": "V3-8",
        "storyPoints": 3,
        "riskLevel": "MEDIUM",
        "storyType": "backend",
        "complexity": "moderate",
        "priority": "P1",
        "dependencies": [],
        "acceptanceCriteria": [
            "AC1: Script creates building_record from distinct acm_record.building_id strings",
            "AC2: acm_record.building_id updated to FK reference",
            "AC3: GET /api/acm/buildings returns buildings for pre-V3 sources",
            "AC4: Rollback script included",
            "AC5: V3 sources unaffected",
            "AC6: Unit test verifies backfill",
        ],
        "keyFiles": [
            "scripts/v3_building_backfill.py",
            "open_notebook/database/repository.py",
        ],
        "techSpecFile": None,
        "implementedDate": None,
        "notes": "",
        "passes": False,
    },
    {
        "id": "E35-S7",
        "title": "SF-First Validation Pipeline",
        "epic": "E35",
        "sprint": "V3-8",
        "storyPoints": 5,
        "riskLevel": "HIGH",
        "storyType": "backend",
        "complexity": "complex",
        "priority": "P1",
        "dependencies": ["E35-S3"],
        "acceptanceCriteria": [
            "AC1: SF validation runs BEFORE BAR validation -- SF schema is source of truth",
            "AC2: Correction loop never overwrites SF-valid values",
            "AC3: F4 product type casing: Title Case to SF sentence case normalization",
            "AC4: BAR enum values mapped to SF equivalents",
            "AC5: 5+ corruption scenarios from docs/issues have regression tests",
            "AC6: Broadmeadows produces >=28/31 records with SF-valid values",
        ],
        "keyFiles": [
            "open_notebook/extractors/validators/acm_validator.py",
            "open_notebook/extractors/normalizers/enums.py",
            "prompts/acm/correction.jinja",
            "open_notebook/extractors/parsers/config_loader.py",
        ],
        "techSpecFile": None,
        "implementedDate": None,
        "notes": "",
        "passes": False,
    },
    {
        "id": "E35-S8",
        "title": "Frontend Error Handling & Polish",
        "epic": "E35",
        "sprint": "V3-8",
        "storyPoints": 2,
        "riskLevel": "LOW",
        "storyType": "frontend",
        "complexity": "simple",
        "priority": "P2",
        "dependencies": [],
        "acceptanceCriteria": [
            "AC1: BuildingSidebar shows No buildings extracted yet empty state (not error)",
            "AC2: No 500 console errors when viewing source with 0 buildings",
            "AC3: Source page handles missing/empty building data gracefully",
            "AC4: CopilotKit dev inspector does not block user interactions",
        ],
        "keyFiles": [
            "frontend/src/components/acm/BuildingSidebar.tsx",
            "frontend/src/components/acm/ItemGrid.tsx",
            "frontend/src/app/(dashboard)/source/[id]/page.tsx",
        ],
        "techSpecFile": None,
        "implementedDate": None,
        "notes": "",
        "passes": False,
    },
]

d["stories"].extend(e35_stories)
d["totalStories"] = len(d["stories"])
d["totalStoryPoints"] = sum(s["storyPoints"] for s in d["stories"])
d["sprints"] = 8

with open(prd_path, "w", encoding="utf-8") as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

e35 = [s for s in d["stories"] if s["id"].startswith("E35")]
print(f"Total stories: {d['totalStories']}")
print(f"Total SP: {d['totalStoryPoints']}")
print(f"E35 stories: {len(e35)}")
print(f"All pending: {all(not s['passes'] for s in e35)}")
