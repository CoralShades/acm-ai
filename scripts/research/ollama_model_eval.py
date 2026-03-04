"""E32-S6 Ollama Model Evaluation Spike.

Benchmarks five Ollama local models on two ACM task types — classification
and enrichment — using a 50-record synthetic sample.

Models tested (Phase 2 — all originally planned + pre-existing):
  - llama3.1:8b    (8.0B, Q4_0)   — originally planned
  - qwen2.5:7b     (7.6B, Q4_K_M) — originally planned
  - mistral:7b     (7.2B, Q4_0)   — originally planned
  - qwen3:latest   (8.2B, Q4_K_M) — pre-existing; reasoning model
  - phi4:latest    (14.7B, Q4_K_M)— pre-existing; instruction model

Notes:
  - deepseek-r1:8b excluded: reasoning model with <think> blocks that consume
    all tokens at max_tokens=512 before outputting JSON. Unsuitable for fast
    production JSON extraction without disabling think-mode.
  - Claude Sonnet baseline skipped: API credits depleted in test environment.
    Note AC3 as "SKIPPED: API credits unavailable".
  - max_tokens=2048 used globally to allow qwen3 reasoning blocks to complete
    before JSON output is generated.

Usage:
    uv run python scripts/research/ollama_model_eval.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Project root + .env setup (mirror e29_benchmark_harness.py pattern)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

import requests  # noqa: E402  (after sys.path setup)
from esperanto import AIFactory  # noqa: E402
from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL = "http://localhost:11434"

# Models to evaluate — Phase 2: all originally planned + pre-existing available.
# deepseek-r1:8b excluded (reasoning model; <think> blocks truncate JSON output
# at max_tokens=512; unsuitable for fast production extraction without think-mode).
MODELS_TO_TEST = [
    {"name": "llama3.1:8b", "provider": "ollama"},
    {"name": "qwen2.5:7b", "provider": "ollama"},
    {"name": "mistral:7b", "provider": "ollama"},
    {"name": "qwen3:latest", "provider": "ollama"},
    {"name": "phi4:latest", "provider": "ollama"},
]

BASELINE_MODEL = {
    "name": "claude-sonnet-4-20250514",
    "provider": "anthropic",
}

RESULTS_DIR = PROJECT_ROOT / "scripts" / "research" / "results"

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class TaskResult:
    """Result metrics for a single task type across all 50 records."""

    task_name: str  # "classification" or "enrichment"
    accuracy: float  # 0.0 – 1.0
    mean_latency_s: float
    p95_latency_s: float
    error_count: int  # records that failed to parse JSON


@dataclass
class ModelResult:
    """Full benchmark result for one model."""

    model_name: str
    provider: str
    vram_bytes: Optional[int]
    classification: TaskResult
    enrichment: TaskResult


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------


def check_ollama_available() -> bool:
    """Return True if Ollama is reachable at OLLAMA_BASE_URL."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# VRAM measurement
# ---------------------------------------------------------------------------


def get_ollama_vram(model_name: str) -> Optional[int]:
    """Query /api/ps and return size_vram for the named model, or None."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/ps", timeout=5)
        for m in resp.json().get("models", []):
            # Match on prefix before colon (e.g. "qwen3" matches "qwen3:latest")
            if m.get("name", "").startswith(model_name.split(":")[0]):
                return m.get("size_vram")
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# JSON parsing (mirrors parse_json_response in open_notebook/graphs/utils.py)
# ---------------------------------------------------------------------------


def parse_json(text: str) -> dict:
    """Extract a JSON object from LLM response text.

    Handles markdown fences, preamble, trailing text, and deepseek-r1
    <think>...</think> reasoning blocks which appear before the JSON output.
    Raises ValueError if no valid JSON object is found.
    """
    # Strip deepseek-r1 <think>...</think> reasoning blocks
    if "<think>" in text:
        think_end = text.rfind("</think>")
        if think_end >= 0:
            text = text[think_end + len("</think>") :].strip()

    # Strip markdown fences
    cleaned = re.sub(r"```(?:json|JSON)?\s*\n?", "", text)
    cleaned = cleaned.replace("```", "").strip()

    # Find the first { ... } block using brace depth tracking
    depth = 0
    start = -1
    in_string = False
    i = 0
    while i < len(cleaned):
        c = cleaned[i]
        if in_string:
            if c == "\\" and i + 1 < len(cleaned):
                i += 2
                continue
            if c == '"':
                in_string = False
        else:
            if c == '"':
                in_string = True
            elif c == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0 and start >= 0:
                    candidate = cleaned[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        # Reset and continue scanning
                        start = -1
        i += 1

    raise ValueError(f"No valid JSON object found in response: {text[:200]!r}")


# ---------------------------------------------------------------------------
# Synthetic test data (50 records, 10+ distinct product types)
# ---------------------------------------------------------------------------

# ACM classification domain values used in ground truth
ACM_CLASSIFICATIONS = [
    "Sprayed Coatings",
    "Insulation",
    "Thermal Insulation",
    "Floor Tiles",
    "Ceiling Tiles",
    "Roofing",
    "Textured Coatings",
    "Boards",
    "Gaskets",
    "Pipe Lagging",
]

ACM_SUB_CLASSIFICATIONS = [
    "Amosite",
    "Chrysotile",
    "Crocidolite",
    "Chrysotile / Amosite",
    None,
]


def build_test_sample() -> list[dict]:
    """Build a 50-record synthetic ACM dataset with ground truth labels.

    Records cover 10+ product types, mix of friable/non-friable, varied
    location strings with capitalisation issues, and unusual room refs.
    """
    records = [
        # --- Ceiling Tiles (Non Friable / Chrysotile) ---
        {
            "product": "Ceiling Tiles",
            "material_description": "Vinyl asbestos ceiling tiles, 300x300mm grid pattern",
            "location_raw": "ground floor corridor",
            "room_ref_raw": "  GF-CORR-01 ",
            "ground_truth_classification": "Ceiling Tiles",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Ground Floor Corridor",
            "ground_truth_room_ref": "GF-Corr-01",
        },
        {
            "product": "Ceiling Tiles",
            "material_description": "Asbestos-containing suspended ceiling panels, cracked",
            "location_raw": "FIRST FLOOR OFFICE",
            "room_ref_raw": "1F-OFF-02",
            "ground_truth_classification": "Ceiling Tiles",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "First Floor Office",
            "ground_truth_room_ref": "1F-Off-02",
        },
        {
            "product": "Ceiling Tiles",
            "material_description": "Textured plaster ceiling with ACM fibres",
            "location_raw": "basement car park",
            "room_ref_raw": "B1-PARK",
            "ground_truth_classification": "Ceiling Tiles",
            "ground_truth_sub_classification": None,
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Basement Car Park",
            "ground_truth_room_ref": "B1-Park",
        },
        {
            "product": "Ceiling Tiles",
            "material_description": "Sprayed asbestos texture coating on ceiling tiles",
            "location_raw": "science block level 2",
            "room_ref_raw": "SCI-L2-001",
            "ground_truth_classification": "Ceiling Tiles",
            "ground_truth_sub_classification": "Amosite",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Science Block Level 2",
            "ground_truth_room_ref": "Sci-L2-001",
        },
        {
            "product": "Ceiling Tiles",
            "material_description": "Mineral fibre ceiling tiles with low ACM content",
            "location_raw": "admin wing, room 4",
            "room_ref_raw": "ADM-004",
            "ground_truth_classification": "Ceiling Tiles",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Admin Wing, Room 4",
            "ground_truth_room_ref": "Adm-004",
        },
        # --- Pipe Lagging (Friable / Amosite) ---
        {
            "product": "Pipe Lagging",
            "material_description": "Amosite pipe lagging wrapped in hessian cloth, boiler room",
            "location_raw": "boiler room",
            "room_ref_raw": " BOILER-01",
            "ground_truth_classification": "Pipe Lagging",
            "ground_truth_sub_classification": "Amosite",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Boiler Room",
            "ground_truth_room_ref": "Boiler-01",
        },
        {
            "product": "Pipe Lagging",
            "material_description": "Lagged hot water pipes, corrugated paper wrapping",
            "location_raw": "roof void",
            "room_ref_raw": "RV-PIPE-03",
            "ground_truth_classification": "Pipe Lagging",
            "ground_truth_sub_classification": "Amosite",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Roof Void",
            "ground_truth_room_ref": "Rv-Pipe-03",
        },
        {
            "product": "Pipe Lagging",
            "material_description": "Insulated steam pipes with ACM wrap, partial damage",
            "location_raw": "plant room level 1",
            "room_ref_raw": "PL-L1-SteamPipes",
            "ground_truth_classification": "Pipe Lagging",
            "ground_truth_sub_classification": "Chrysotile / Amosite",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Plant Room Level 1",
            "ground_truth_room_ref": "Pl-L1-Steampipes",
        },
        {
            "product": "Pipe Lagging",
            "material_description": "Chrysotile lagged pipework in ceiling void, intact",
            "location_raw": "CEILING VOID ABOVE LIBRARY",
            "room_ref_raw": "LIB-VOID",
            "ground_truth_classification": "Pipe Lagging",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Ceiling Void Above Library",
            "ground_truth_room_ref": "Lib-Void",
        },
        {
            "product": "Pipe Lagging",
            "material_description": "Loose ACM lagging on heating pipes, multiple sections missing",
            "location_raw": "subfloor service duct",
            "room_ref_raw": "SF-DUCT-A",
            "ground_truth_classification": "Pipe Lagging",
            "ground_truth_sub_classification": "Amosite",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Subfloor Service Duct",
            "ground_truth_room_ref": "Sf-Duct-A",
        },
        # --- Floor Tiles (Non Friable / Chrysotile) ---
        {
            "product": "Floor Tiles",
            "material_description": "9-inch vinyl asbestos floor tiles, black/white pattern",
            "location_raw": "main entrance lobby",
            "room_ref_raw": "ENT-LOBBY",
            "ground_truth_classification": "Floor Tiles",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Main Entrance Lobby",
            "ground_truth_room_ref": "Ent-Lobby",
        },
        {
            "product": "Floor Tiles",
            "material_description": "Asbestos vinyl composite tiles with mastic adhesive",
            "location_raw": "Staff Room",
            "room_ref_raw": " SR-001 ",
            "ground_truth_classification": "Floor Tiles",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Staff Room",
            "ground_truth_room_ref": "Sr-001",
        },
        {
            "product": "Floor Tiles",
            "material_description": "Thermoplastic floor tiles laid over ACM adhesive",
            "location_raw": "gymnasium",
            "room_ref_raw": "GYM-FL",
            "ground_truth_classification": "Floor Tiles",
            "ground_truth_sub_classification": None,
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Gymnasium",
            "ground_truth_room_ref": "Gym-Fl",
        },
        {
            "product": "Floor Tiles",
            "material_description": "Bitumen-backed asbestos tiles, partially lifted",
            "location_raw": "craft room & store",
            "room_ref_raw": "CRAFT-STR",
            "ground_truth_classification": "Floor Tiles",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Craft Room & Store",
            "ground_truth_room_ref": "Craft-Str",
        },
        {
            "product": "Floor Tiles",
            "material_description": "ACM floor tiles in good condition under carpet",
            "location_raw": "headmaster's office",
            "room_ref_raw": "HM-OFF",
            "ground_truth_classification": "Floor Tiles",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Headmaster's Office",
            "ground_truth_room_ref": "Hm-Off",
        },
        # --- Sprayed Coatings (Friable / Amosite) ---
        {
            "product": "Sprayed Limpet Coating",
            "material_description": "Blue Limpet amosite sprayed coating on structural steel",
            "location_raw": "sports hall roof steelwork",
            "room_ref_raw": "SPALL-ROOF",
            "ground_truth_classification": "Sprayed Coatings",
            "ground_truth_sub_classification": "Amosite",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Sports Hall Roof Steelwork",
            "ground_truth_room_ref": "Spall-Roof",
        },
        {
            "product": "Sprayed Limpet Coating",
            "material_description": "ACM sprayed fire protection on concrete beams",
            "location_raw": "car park upper deck",
            "room_ref_raw": "CP-UPPER",
            "ground_truth_classification": "Sprayed Coatings",
            "ground_truth_sub_classification": "Amosite",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Car Park Upper Deck",
            "ground_truth_room_ref": "Cp-Upper",
        },
        {
            "product": "Sprayed Coating",
            "material_description": "Chrysotile-containing sprayed plaster, water damaged",
            "location_raw": "changing rooms male",
            "room_ref_raw": "CHG-M",
            "ground_truth_classification": "Sprayed Coatings",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Changing Rooms Male",
            "ground_truth_room_ref": "Chg-M",
        },
        {
            "product": "Sprayed Coating",
            "material_description": "Mixed fibre sprayed coating on underside of floors",
            "location_raw": "under floor 2",
            "room_ref_raw": "UF-L2",
            "ground_truth_classification": "Sprayed Coatings",
            "ground_truth_sub_classification": "Chrysotile / Amosite",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Under Floor 2",
            "ground_truth_room_ref": "Uf-L2",
        },
        {
            "product": "Sprayed Coating",
            "material_description": "Partially removed sprayed ACM, high fibre release risk",
            "location_raw": "plant room roof",
            "room_ref_raw": "PLT-ROOF",
            "ground_truth_classification": "Sprayed Coatings",
            "ground_truth_sub_classification": "Amosite",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Plant Room Roof",
            "ground_truth_room_ref": "Plt-Roof",
        },
        # --- Insulation Board / AIB (Non Friable) ---
        {
            "product": "Asbestos Insulation Board (AIB)",
            "material_description": "Asbestos insulation board panels on fire doors",
            "location_raw": "fire door fire escape route",
            "room_ref_raw": "FD-ESC-01",
            "ground_truth_classification": "Boards",
            "ground_truth_sub_classification": "Amosite",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Fire Door Fire Escape Route",
            "ground_truth_room_ref": "Fd-Esc-01",
        },
        {
            "product": "Asbestos Insulation Board",
            "material_description": "AIB partition walls in good condition, no visible damage",
            "location_raw": "STORAGE CUPBOARD UNDER STAIRS",
            "room_ref_raw": "STAIR-STORE",
            "ground_truth_classification": "Boards",
            "ground_truth_sub_classification": "Amosite",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Storage Cupboard Under Stairs",
            "ground_truth_room_ref": "Stair-Store",
        },
        {
            "product": "AIB Ceiling",
            "material_description": "Asbestos insulation board ceiling tiles, crumbling edges",
            "location_raw": "caretaker room",
            "room_ref_raw": "CARE-01",
            "ground_truth_classification": "Boards",
            "ground_truth_sub_classification": "Amosite",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Caretaker Room",
            "ground_truth_room_ref": "Care-01",
        },
        {
            "product": "AIB Panel",
            "material_description": "Amosite AIB used as electrical panel backing board",
            "location_raw": "electrical switchroom",
            "room_ref_raw": "ELEC-SW",
            "ground_truth_classification": "Boards",
            "ground_truth_sub_classification": "Amosite",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Electrical Switchroom",
            "ground_truth_room_ref": "Elec-Sw",
        },
        {
            "product": "AIB Soffit",
            "material_description": "AIB soffit panels below staircase, minor delamination",
            "location_raw": "stairwell level 1-2",
            "room_ref_raw": "STAIR-L1L2",
            "ground_truth_classification": "Boards",
            "ground_truth_sub_classification": "Amosite",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Stairwell Level 1-2",
            "ground_truth_room_ref": "Stair-L1L2",
        },
        # --- Roofing (Non Friable / Chrysotile) ---
        {
            "product": "Corrugated Asbestos Cement Roof Sheeting",
            "material_description": "External corrugated asbestos cement roof panels",
            "location_raw": "main building rooftop",
            "room_ref_raw": "ROOF-MAIN",
            "ground_truth_classification": "Roofing",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Main Building Rooftop",
            "ground_truth_room_ref": "Roof-Main",
        },
        {
            "product": "Asbestos Cement Cladding",
            "material_description": "Flat asbestos cement cladding panels on external wall",
            "location_raw": "north elevation external",
            "room_ref_raw": "EXT-NORTH",
            "ground_truth_classification": "Roofing",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "North Elevation External",
            "ground_truth_room_ref": "Ext-North",
        },
        {
            "product": "AC Roof Sheet",
            "material_description": "Asbestos cement roof sheets over workshop, good condition",
            "location_raw": "WORKSHOP ROOF",
            "room_ref_raw": "WKSHP-ROOF",
            "ground_truth_classification": "Roofing",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Workshop Roof",
            "ground_truth_room_ref": "Wkshp-Roof",
        },
        {
            "product": "Asbestos Cement Downpipe",
            "material_description": "AC downpipes and guttering along east facade",
            "location_raw": "east facade external",
            "room_ref_raw": "EXT-EAST-DP",
            "ground_truth_classification": "Roofing",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "East Facade External",
            "ground_truth_room_ref": "Ext-East-Dp",
        },
        {
            "product": "Asbestos Cement Fascia",
            "material_description": "AC fascia boards under eaves, weathered but intact",
            "location_raw": "south eaves",
            "room_ref_raw": "EAVES-S",
            "ground_truth_classification": "Roofing",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "South Eaves",
            "ground_truth_room_ref": "Eaves-S",
        },
        # --- Thermal Insulation (Friable) ---
        {
            "product": "Boiler Insulation",
            "material_description": "Amosite sectional boiler lagging, poor condition",
            "location_raw": "boiler house",
            "room_ref_raw": "BH-BOILER",
            "ground_truth_classification": "Thermal Insulation",
            "ground_truth_sub_classification": "Amosite",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Boiler House",
            "ground_truth_room_ref": "Bh-Boiler",
        },
        {
            "product": "Duct Insulation",
            "material_description": "ACM duct insulation wrap in ceiling, delaminating",
            "location_raw": "ceiling void block A",
            "room_ref_raw": "CV-BLK-A",
            "ground_truth_classification": "Thermal Insulation",
            "ground_truth_sub_classification": "Amosite",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Ceiling Void Block A",
            "ground_truth_room_ref": "Cv-Blk-A",
        },
        {
            "product": "Calorifier Insulation",
            "material_description": "Hot water calorifier with ACM sectional insulation",
            "location_raw": "plant room ground floor",
            "room_ref_raw": "PLT-GF",
            "ground_truth_classification": "Thermal Insulation",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Plant Room Ground Floor",
            "ground_truth_room_ref": "Plt-Gf",
        },
        {
            "product": "Tank Insulation",
            "material_description": "ACM insulation blanket on cold water storage tank",
            "location_raw": "roof tank room",
            "room_ref_raw": "TANK-ROOF",
            "ground_truth_classification": "Thermal Insulation",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Roof Tank Room",
            "ground_truth_room_ref": "Tank-Roof",
        },
        {
            "product": "Flue Insulation",
            "material_description": "ACM rope seal and insulation around boiler flue",
            "location_raw": "BOILER FLUE DUCT",
            "room_ref_raw": "BH-FLUE",
            "ground_truth_classification": "Thermal Insulation",
            "ground_truth_sub_classification": "Chrysotile / Amosite",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Boiler Flue Duct",
            "ground_truth_room_ref": "Bh-Flue",
        },
        # --- Textured Coatings (Non Friable / Chrysotile) ---
        {
            "product": "Artex / Textured Coating",
            "material_description": "Artex stipple finish on classroom ceilings, chrysotile",
            "location_raw": "classroom block 2",
            "room_ref_raw": "CL-BLK-2-01",
            "ground_truth_classification": "Textured Coatings",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Classroom Block 2",
            "ground_truth_room_ref": "Cl-Blk-2-01",
        },
        {
            "product": "Textured Paint",
            "material_description": "Swirl pattern textured paint on walls containing ACM",
            "location_raw": "corridor main block",
            "room_ref_raw": "MB-CORR",
            "ground_truth_classification": "Textured Coatings",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Corridor Main Block",
            "ground_truth_room_ref": "Mb-Corr",
        },
        {
            "product": "Artex Ceiling Finish",
            "material_description": "Blown Artex coating in good condition, low risk",
            "location_raw": "hall and assembly area",
            "room_ref_raw": "HALL-ASSY",
            "ground_truth_classification": "Textured Coatings",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Hall And Assembly Area",
            "ground_truth_room_ref": "Hall-Assy",
        },
        {
            "product": "Pebble Dash",
            "material_description": "External pebble dash render with ACM binder",
            "location_raw": "external south wall",
            "room_ref_raw": "EXT-SW",
            "ground_truth_classification": "Textured Coatings",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "External South Wall",
            "ground_truth_room_ref": "Ext-Sw",
        },
        {
            "product": "Spray Plaster Finish",
            "material_description": "Machine-applied spray plaster with chrysotile, ceiling",
            "location_raw": "dining room",
            "room_ref_raw": "DINING-01",
            "ground_truth_classification": "Textured Coatings",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Dining Room",
            "ground_truth_room_ref": "Dining-01",
        },
        # --- Gaskets (Non Friable) ---
        {
            "product": "Gasket / Rope Seal",
            "material_description": "ACM rope seals and gaskets on boiler access doors",
            "location_raw": "boiler room",
            "room_ref_raw": "BOILER-GSK",
            "ground_truth_classification": "Gaskets",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Boiler Room",
            "ground_truth_room_ref": "Boiler-Gsk",
        },
        {
            "product": "Pipe Gasket",
            "material_description": "Asbestos compressed sheet gaskets on flanged joints",
            "location_raw": "plant room level 2",
            "room_ref_raw": "PLT-L2-GSK",
            "ground_truth_classification": "Gaskets",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Plant Room Level 2",
            "ground_truth_room_ref": "Plt-L2-Gsk",
        },
        # --- Insulation (Loose / Friable) ---
        {
            "product": "Loose Insulation Fill",
            "material_description": "Loose ACM fill in wall cavity, likely blown insulation",
            "location_raw": "wall cavity block C",
            "room_ref_raw": "WALL-CAV-C",
            "ground_truth_classification": "Insulation",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Wall Cavity Block C",
            "ground_truth_room_ref": "Wall-Cav-C",
        },
        {
            "product": "Cavity Insulation",
            "material_description": "Vermiculite ACM cavity insulation, highly friable",
            "location_raw": "external wall cavity",
            "room_ref_raw": "EXT-CAV",
            "ground_truth_classification": "Insulation",
            "ground_truth_sub_classification": None,
            "ground_truth_friability": "Friable",
            "ground_truth_location": "External Wall Cavity",
            "ground_truth_room_ref": "Ext-Cav",
        },
        # --- Edge cases / mixed scenarios ---
        {
            "product": "Bitumen Felt Roofing",
            "material_description": "Bituminous roof felt with ACM reinforcement, west wing",
            "location_raw": "west wing flat roof",
            "room_ref_raw": "ROOF-WEST",
            "ground_truth_classification": "Roofing",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "West Wing Flat Roof",
            "ground_truth_room_ref": "Roof-West",
        },
        {
            "product": "Rope Packing",
            "material_description": "Chrysotile rope packing around window frames",
            "location_raw": "window frames ground floor external",
            "room_ref_raw": "WIN-GF-EXT",
            "ground_truth_classification": "Gaskets",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Window Frames Ground Floor External",
            "ground_truth_room_ref": "Win-Gf-Ext",
        },
        {
            "product": "Fire Door Infill Panel",
            "material_description": "AIB infill panels in steel fire door frames",
            "location_raw": "fire escape stairwell",
            "room_ref_raw": "ESC-STAIR",
            "ground_truth_classification": "Boards",
            "ground_truth_sub_classification": "Amosite",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Fire Escape Stairwell",
            "ground_truth_room_ref": "Esc-Stair",
        },
        {
            "product": "Ceiling Plaster",
            "material_description": "ACM plaster skim coat on lath, highly friable if disturbed",
            "location_raw": "old building first floor",
            "room_ref_raw": "OLD-1F-PL",
            "ground_truth_classification": "Sprayed Coatings",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Old Building First Floor",
            "ground_truth_room_ref": "Old-1F-Pl",
        },
        {
            "product": "Sprayed Steel Beams",
            "material_description": "Crocidolite sprayed fire protection on structural steelwork",
            "location_raw": "sports hall main frame",
            "room_ref_raw": "SH-STEEL",
            "ground_truth_classification": "Sprayed Coatings",
            "ground_truth_sub_classification": "Crocidolite",
            "ground_truth_friability": "Friable",
            "ground_truth_location": "Sports Hall Main Frame",
            "ground_truth_room_ref": "Sh-Steel",
        },
        {
            "product": "Bitumen DPC",
            "material_description": "Bitumen damp proof course containing ACM fibres",
            "location_raw": "foundation wall damp course",
            "room_ref_raw": "FOUND-DPC",
            "ground_truth_classification": "Roofing",
            "ground_truth_sub_classification": "Chrysotile",
            "ground_truth_friability": "Non Friable",
            "ground_truth_location": "Foundation Wall Damp Course",
            "ground_truth_room_ref": "Found-Dpc",
        },
    ]

    assert len(records) == 50, f"Expected 50 records, got {len(records)}"
    return records


# ---------------------------------------------------------------------------
# Classification task
# ---------------------------------------------------------------------------

CLASSIFICATION_SYSTEM = (
    "You are an ACM (Asbestos Containing Material) classification expert.\n"
    "Given an ACM product name and material description, output ONLY a JSON object\n"
    "with exactly these fields:\n"
    '- "acm_classification": the ACM material classification\n'
    '- "acm_sub_classification": the sub-classification, or null if unknown\n'
    '- "friability": "Friable", "Non Friable", or null\n'
    "\nDo not include any explanation. Output only valid JSON."
)

CLASSIFICATION_USER_TMPL = (
    "Product: {product}\n"
    "Material Description: {material_description}\n\n"
    "Classify this ACM item."
)


def score_classification(predicted: dict, record: dict) -> float:
    """Return fractional score: 1/3 per correct field (3 fields total).

    Fields scored: acm_classification, acm_sub_classification, friability.
    Sub-classification null == null is a match.
    """
    score = 0.0

    pred_cls = (predicted.get("acm_classification") or "").strip().lower()
    true_cls = (record["ground_truth_classification"] or "").strip().lower()
    if pred_cls and pred_cls == true_cls:
        score += 1 / 3

    pred_sub = predicted.get("acm_sub_classification")
    true_sub = record["ground_truth_sub_classification"]
    if pred_sub is None and true_sub is None:
        score += 1 / 3
    elif (
        pred_sub is not None
        and true_sub is not None
        and str(pred_sub).strip().lower() == str(true_sub).strip().lower()
    ):
        score += 1 / 3

    pred_fri = (predicted.get("friability") or "").strip().lower()
    true_fri = (record["ground_truth_friability"] or "").strip().lower()
    if pred_fri and pred_fri == true_fri:
        score += 1 / 3

    return score


def run_classification_task(lc_model, records: list[dict]) -> tuple[TaskResult, list]:
    """Run classification task against all records.

    Returns (TaskResult, list of per-record details for debugging).
    """
    latencies: list[float] = []
    scores: list[float] = []
    error_count = 0
    details = []

    for record in records:
        user_content = CLASSIFICATION_USER_TMPL.format(
            product=record["product"],
            material_description=record["material_description"],
        )
        try:
            start = time.perf_counter()
            response = lc_model.invoke(
                [
                    SystemMessage(content=CLASSIFICATION_SYSTEM),
                    HumanMessage(content=user_content),
                ]
            )
            latency = time.perf_counter() - start

            raw_text = response.content
            predicted = parse_json(raw_text)
            score = score_classification(predicted, record)
            latencies.append(latency)
            scores.append(score)
            details.append(
                {
                    "product": record["product"],
                    "score": score,
                    "latency_s": round(latency, 3),
                    "predicted": predicted,
                }
            )
        except Exception as exc:
            error_count += 1
            latencies.append(0.0)
            scores.append(0.0)
            details.append(
                {
                    "product": record["product"],
                    "score": 0.0,
                    "latency_s": 0.0,
                    "error": str(exc)[:200],
                }
            )

    latencies_sorted = sorted(latencies)
    mean_latency = sum(latencies_sorted) / len(latencies_sorted)
    p95_idx = int(len(latencies_sorted) * 0.95)
    p95_latency = latencies_sorted[min(p95_idx, len(latencies_sorted) - 1)]

    return (
        TaskResult(
            task_name="classification",
            accuracy=sum(scores) / len(scores) if scores else 0.0,
            mean_latency_s=round(mean_latency, 3),
            p95_latency_s=round(p95_latency, 3),
            error_count=error_count,
        ),
        details,
    )


# ---------------------------------------------------------------------------
# Enrichment task
# ---------------------------------------------------------------------------

ENRICHMENT_SYSTEM = (
    "You are an ACM data normalization assistant.\n"
    "Given raw location and room reference strings from an asbestos register,\n"
    "output ONLY a JSON object with:\n"
    '- "location_normalized": the standardized location string (title case, no special chars)\n'
    '- "room_ref_standardized": the standardized room reference (title case, trimmed)\n'
    "\nDo not include any explanation. Output only valid JSON."
)

ENRICHMENT_USER_TMPL = (
    "Location (raw): {location_raw}\n"
    "Room Reference (raw): {room_ref_raw}\n\n"
    "Normalize these values."
)


def score_enrichment(predicted: dict, record: dict) -> float:
    """Return fractional score: 0.5 per correct field (2 fields total).

    Uses exact string match after strip and lower-case normalisation.
    """
    score = 0.0

    pred_loc = (predicted.get("location_normalized") or "").strip().lower()
    true_loc = (record["ground_truth_location"] or "").strip().lower()
    if pred_loc and pred_loc == true_loc:
        score += 0.5

    pred_ref = (predicted.get("room_ref_standardized") or "").strip().lower()
    true_ref = (record["ground_truth_room_ref"] or "").strip().lower()
    if pred_ref and pred_ref == true_ref:
        score += 0.5

    return score


def run_enrichment_task(lc_model, records: list[dict]) -> tuple[TaskResult, list]:
    """Run enrichment task against all records.

    Returns (TaskResult, list of per-record details for debugging).
    """
    latencies: list[float] = []
    scores: list[float] = []
    error_count = 0
    details = []

    for record in records:
        user_content = ENRICHMENT_USER_TMPL.format(
            location_raw=record["location_raw"],
            room_ref_raw=record["room_ref_raw"],
        )
        try:
            start = time.perf_counter()
            response = lc_model.invoke(
                [
                    SystemMessage(content=ENRICHMENT_SYSTEM),
                    HumanMessage(content=user_content),
                ]
            )
            latency = time.perf_counter() - start

            raw_text = response.content
            predicted = parse_json(raw_text)
            score = score_enrichment(predicted, record)
            latencies.append(latency)
            scores.append(score)
            details.append(
                {
                    "location_raw": record["location_raw"],
                    "room_ref_raw": record["room_ref_raw"],
                    "score": score,
                    "latency_s": round(latency, 3),
                    "predicted": predicted,
                }
            )
        except Exception as exc:
            error_count += 1
            latencies.append(0.0)
            scores.append(0.0)
            details.append(
                {
                    "location_raw": record["location_raw"],
                    "room_ref_raw": record["room_ref_raw"],
                    "score": 0.0,
                    "latency_s": 0.0,
                    "error": str(exc)[:200],
                }
            )

    latencies_sorted = sorted(latencies)
    mean_latency = sum(latencies_sorted) / len(latencies_sorted)
    p95_idx = int(len(latencies_sorted) * 0.95)
    p95_latency = latencies_sorted[min(p95_idx, len(latencies_sorted) - 1)]

    return (
        TaskResult(
            task_name="enrichment",
            accuracy=sum(scores) / len(scores) if scores else 0.0,
            mean_latency_s=round(mean_latency, 3),
            p95_latency_s=round(p95_latency, 3),
            error_count=error_count,
        ),
        details,
    )


# ---------------------------------------------------------------------------
# Model evaluation runner
# ---------------------------------------------------------------------------


def run_eval_for_model(
    model_name: str, provider: str, records: list[dict]
) -> tuple[ModelResult, dict]:
    """Run both tasks for one model and return (ModelResult, debug_details)."""
    print(f"\n{'=' * 60}")
    print(f"Evaluating: {model_name} ({provider})")
    print("=" * 60)

    # Provision model — no tool calling for any model in this spike
    # (qwen2.5, phi4 are in TOOL_CALLING_BLOCKLIST; use plain-text prompts).
    # max_tokens=2048 gives reasoning models (qwen3) enough room to close
    # their <think> block before emitting JSON output.
    try:
        lc_model = AIFactory.create_language(
            model_name=model_name,
            provider=provider,
            config={"temperature": 0.0, "max_tokens": 2048},
        ).to_langchain()
    except Exception as e:
        print(f"ERROR: Failed to provision model {model_name}: {e}")
        empty_task = TaskResult("error", 0.0, 0.0, 0.0, 50)
        return (
            ModelResult(model_name, provider, None, empty_task, empty_task),
            {"classification": [], "enrichment": []},
        )

    # Warm-up inference (loads model into VRAM for Ollama)
    if provider == "ollama":
        print("  Running warm-up inference...")
        try:
            lc_model.invoke(
                [
                    SystemMessage(content="You are a helpful assistant."),
                    HumanMessage(content="Say 'ready' in one word."),
                ]
            )
        except Exception as e:
            print(f"  Warm-up failed: {e}")

    # Measure VRAM after warm-up
    vram_bytes: Optional[int] = None
    if provider == "ollama":
        vram_bytes = get_ollama_vram(model_name)
        vram_display = f"{vram_bytes / 1e9:.2f} GB" if vram_bytes else "unknown"
        print(f"  VRAM: {vram_display}")

    # Classification task
    print(f"  Running classification task (50 records)...")
    cls_result, cls_details = run_classification_task(lc_model, records)
    print(
        f"  Classification: accuracy={cls_result.accuracy:.1%}, "
        f"mean={cls_result.mean_latency_s:.2f}s, "
        f"p95={cls_result.p95_latency_s:.2f}s, "
        f"errors={cls_result.error_count}"
    )

    # Enrichment task
    print(f"  Running enrichment task (50 records)...")
    enr_result, enr_details = run_enrichment_task(lc_model, records)
    print(
        f"  Enrichment:     accuracy={enr_result.accuracy:.1%}, "
        f"mean={enr_result.mean_latency_s:.2f}s, "
        f"p95={enr_result.p95_latency_s:.2f}s, "
        f"errors={enr_result.error_count}"
    )

    model_result = ModelResult(
        model_name=model_name,
        provider=provider,
        vram_bytes=vram_bytes,
        classification=cls_result,
        enrichment=enr_result,
    )
    debug = {
        "classification": cls_details,
        "enrichment": enr_details,
    }
    return model_result, debug


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def _vram_str(vram_bytes: Optional[int]) -> str:
    if vram_bytes is None:
        return "n/a"
    return f"{vram_bytes / 1e9:.1f}GB"


def print_markdown_table(results: list[ModelResult]) -> None:
    """Print a formatted markdown results table to stdout."""
    header = (
        "| Model                    | Provider  | VRAM   "
        "| Class. Acc | Enrich. Acc | Class. p95 | Enrich. p95 |"
    )
    separator = (
        "|--------------------------|-----------|--------|"
        "------------|-------------|------------|-------------|"
    )
    print("\n" + header)
    print(separator)
    for r in results:
        row = (
            f"| {r.model_name:<24} "
            f"| {r.provider:<9} "
            f"| {_vram_str(r.vram_bytes):<6} "
            f"| {r.classification.accuracy:>9.1%}  "
            f"| {r.enrichment.accuracy:>10.1%}  "
            f"| {r.classification.p95_latency_s:>8.2f}s  "
            f"| {r.enrichment.p95_latency_s:>9.2f}s  |"
        )
        print(row)
    print()


def save_json_results(results: list[ModelResult], debug: dict) -> Path:
    """Serialise results + debug details to RESULTS_DIR/ollama_eval_results.json."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / "ollama_eval_results.json"

    payload = {
        "meta": {
            "script": "scripts/research/ollama_model_eval.py",
            "story": "E32-S6",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "models_tested": [r.model_name for r in results],
        },
        "results": [],
    }

    for r in results:
        payload["results"].append(
            {
                "model_name": r.model_name,
                "provider": r.provider,
                "vram_bytes": r.vram_bytes,
                "classification": asdict(r.classification),
                "enrichment": asdict(r.enrichment),
                "debug": debug.get(r.model_name, {}),
            }
        )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Results written to: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    # 1. Check Ollama availability
    if not check_ollama_available():
        print(
            "ERROR: Ollama is not running at http://localhost:11434.\n"
            "Start Ollama with: ollama serve\n"
            "Then pull models:\n"
            "  ollama pull llama3.1:8b\n"
            "  ollama pull qwen2.5:7b\n"
            "  ollama pull mistral:7b\n"
            "  ollama pull qwen3:latest\n"
            "  ollama pull phi4:latest\n"
            "Exiting."
        )
        return 1

    print("Ollama is available.")

    # 2. Build test sample
    records = build_test_sample()
    print(f"Test sample built: {len(records)} records")

    # 3. Determine which models to run
    models_to_run = list(MODELS_TO_TEST)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        models_to_run.append(BASELINE_MODEL)
        print(f"ANTHROPIC_API_KEY found — Claude Sonnet baseline included.")
    else:
        print("WARNING: ANTHROPIC_API_KEY not found — skipping Sonnet baseline.")

    # 4. Run evaluations
    all_results: list[ModelResult] = []
    all_debug: dict = {}

    for model_cfg in models_to_run:
        result, debug_details = run_eval_for_model(
            model_cfg["name"], model_cfg["provider"], records
        )
        all_results.append(result)
        all_debug[model_cfg["name"]] = debug_details

    # 5. Print summary table
    print("\n--- BENCHMARK RESULTS ---")
    print_markdown_table(all_results)

    # 6. Save JSON results
    output_path = save_json_results(all_results, all_debug)

    # 7. Quick recommendation summary
    print("--- RECOMMENDATION SUMMARY ---")
    threshold = 0.75
    passing = [
        r
        for r in all_results
        if r.provider == "ollama"
        and r.classification.accuracy >= threshold
        and r.enrichment.accuracy >= threshold
    ]
    if passing:
        best = max(
            passing,
            key=lambda r: (r.classification.accuracy + r.enrichment.accuracy) / 2,
        )
        print(
            f"Models meeting >=75% threshold on both tasks: "
            f"{[r.model_name for r in passing]}"
        )
        print(
            f"Recommended for production: {best.model_name} "
            f"(classification: {best.classification.accuracy:.1%}, "
            f"enrichment: {best.enrichment.accuracy:.1%})"
        )
    else:
        ollama_results = [r for r in all_results if r.provider == "ollama"]
        if ollama_results:
            best = max(
                ollama_results,
                key=lambda r: (r.classification.accuracy + r.enrichment.accuracy) / 2,
            )
            print(
                f"No model met the 75% threshold. Best performer: {best.model_name} "
                f"(classification: {best.classification.accuracy:.1%}, "
                f"enrichment: {best.enrichment.accuracy:.1%})"
            )
            print("Recommendation: escalate to E32-S7 investigation.")
        else:
            print("No Ollama results available.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
