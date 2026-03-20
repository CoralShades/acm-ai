"""Prompt evaluation harness for ACM extraction quality.

Compares extraction output (from DB or JSON file) against ground truth CSVs.
Scores: record-level recall, per-field accuracy, fuzzy matching.

Usage:
    # From DB (requires services running):
    uv run python scripts/eval/prompt_eval_harness.py --source-id source:ktioihsjj9ih7kd95fcx --gt broadmeadows

    # From JSON file (offline):
    uv run python scripts/eval/prompt_eval_harness.py --json scripts/eval/ground_truth/broadmeadows_extracted.json --gt broadmeadows

    # Both benchmarks:
    uv run python scripts/eval/prompt_eval_harness.py --all

    # Save results:
    uv run python scripts/eval/prompt_eval_harness.py --all --save results.json
"""

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

GT_DIR = PROJECT_ROOT / "scripts/eval/ground_truth"

# Fields to evaluate (matching both ground truth CSV and ACMExtractionRecord)
EVAL_FIELDS = [
    "room_name",
    "floor_level",
    "location",
    "product",
    "material_description",
    "friable",
    "sample_no",
    "sample_result",
    "area_type",
    "material_condition",
    "disturbance_potential",
]

# Product synonym map for fuzzy matching (from e26_s4 validation)
PRODUCT_SYNONYMS: dict[str, list[str]] = {
    "flange joints": ["flange mastic", "mastic", "flange mastic (grey)"],
    "fuse cartridge": ["fuses", "fuse", "switchboard fuses"],
    "internal lining": ["lining", "wall lining", "internal wall lining"],
    "fire door(s)": ["fire door", "fire door core"],
    "electrical board": ["electrical distribution board", "electrical panel"],
    "shower cubicle": ["shower cubicle - flat cement sheeting"],
    "ceiling": ["ceiling - flat cement sheeting"],
    "eaves": ["eaves - flat cement sheeting"],
    "ductwork": ["ductwork - mastic", "air handling unit ductwork"],
    "insulation": ["safe - insulation", "insulation - safe"],
    "floor covering": [
        "vinyl floor tiles",
        "floor tiles",
        "vinyl tiles",
        "floor covering adhesive",
        "vinyl sheet",
        "vinyl sheet (cream)",
    ],
    "skirting": [
        "skirting board",
        "skirting vinyl sheet",
        "skirting vinyl sheet (brown)",
    ],
    "vinyl sheet": [
        "vinyl sheet ",
        "hessian backed vinyl sheet",
        "hessian back sheet vinyl",
    ],
    "gasket": ["boiler pipework", "gasket (orange)", "gasket (black)"],
    "infill panels": ["fibre cement sheet infill panel", "infill panel"],
    "wall(s)": ["wall", "wall covering"],
    "filing cabinet": ["filing cabinet"],
    "expansion joint": ["expansion joint"],
}

# Area type normalization (BAR uses "Internal"/"External", extraction uses "Interior"/"Exterior")
AREA_TYPE_MAP: dict[str, str] = {
    "internal": "Internal",
    "interior": "Internal",
    "external": "External",
    "exterior": "External",
    "grounds": "Grounds",
}

# Floor level normalization (BAR uses "Ground", extraction uses "Ground floor")
FLOOR_LEVEL_MAP: dict[str, str] = {
    "ground": "Ground",
    "ground floor": "Ground",
    "ground level": "Ground",
    "first": "First",
    "first floor": "First",
    "level 1": "First",
    "second": "Second",
    "second floor": "Second",
    "level 2": "Second",
    "roof": "Roof",
    "roof space": "Roof",
    "basement": "Basement",
}

# Condition normalization (BAR uses "N/A (negative)", extraction may use None)
CONDITION_MAP: dict[str, str] = {
    "n/a (negative)": "N/A",
    "n/a": "N/A",
    "good": "Good",
    "stable": "Good",  # SF picklist: Stable = Good
    "fair": "Fair",
    "poor": "Poor",
    "severely damaged": "Severely Damaged",
}

# Friability normalization
FRIABILITY_MAP: dict[str, str] = {
    "f": "Friable",
    "friable": "Friable",
    "yes": "Friable",
    "nf": "Non-friable",
    "non-friable": "Non-friable",
    "non friable": "Non-friable",
    "nonfriable": "Non-friable",
    "no": "Non-friable",
}


def _normalize(s: Optional[str]) -> str:
    """Normalize a string for comparison: lowercase, collapse whitespace."""
    if s is None:
        return ""
    return " ".join(str(s).lower().strip().split())


def _normalize_product(product: Optional[str]) -> str:
    """Normalize product name with synonym resolution."""
    norm = _normalize(product)
    if not norm:
        return ""
    # Check if it's a known canonical name
    if norm in PRODUCT_SYNONYMS:
        return norm
    # Check if it's a synonym
    for canonical, synonyms in PRODUCT_SYNONYMS.items():
        if norm in [_normalize(s) for s in synonyms]:
            return canonical
    return norm


def _normalize_friability(raw: Optional[str]) -> str:
    """Normalize friability to canonical form."""
    if raw is None:
        return ""
    stripped = raw.strip().lower().replace("-", " ").strip()
    return FRIABILITY_MAP.get(stripped, raw.strip())


def _normalize_area_type(raw: Optional[str]) -> str:
    """Normalize area_type to canonical form."""
    if raw is None:
        return ""
    key = raw.strip().lower()
    return AREA_TYPE_MAP.get(key, raw.strip())


def _normalize_floor_level(raw: Optional[str]) -> str:
    """Normalize floor level to canonical form."""
    if raw is None:
        return ""
    key = raw.strip().lower()
    return FLOOR_LEVEL_MAP.get(key, raw.strip())


def _normalize_condition(raw: Optional[str]) -> str:
    """Normalize material condition to canonical form."""
    if raw is None:
        return ""
    key = raw.strip().lower()
    return CONDITION_MAP.get(key, raw.strip())


def _normalize_sample_no(raw: Optional[str]) -> str:
    """Normalize sample number for comparison."""
    norm = _normalize(raw)
    # Remove "as per" prefix
    if norm.startswith("as per "):
        norm = norm[7:]
    # Remove "same as" prefix
    if norm.startswith("same as "):
        norm = norm[8:]
    return norm


def _fuzzy_match(a: str, b: str) -> float:
    """Compute fuzzy match ratio between two strings."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


@dataclass
class FieldScore:
    """Score for a single field comparison."""

    field_name: str
    exact_matches: int = 0
    fuzzy_matches: int = 0  # >= 0.8 similarity
    mismatches: int = 0
    gt_empty: int = 0  # Ground truth is empty (skip from accuracy)
    ext_empty: int = 0  # Extracted is empty when GT has value
    total: int = 0
    mismatch_examples: list[dict] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        """Exact match accuracy (excluding GT-empty fields)."""
        evaluated = self.total - self.gt_empty
        if evaluated == 0:
            return 1.0
        return self.exact_matches / evaluated

    @property
    def fuzzy_accuracy(self) -> float:
        """Fuzzy match accuracy (exact + fuzzy, excluding GT-empty)."""
        evaluated = self.total - self.gt_empty
        if evaluated == 0:
            return 1.0
        return (self.exact_matches + self.fuzzy_matches) / evaluated

    @property
    def coverage(self) -> float:
        """How often the field has a value when GT has one."""
        evaluated = self.total - self.gt_empty
        if evaluated == 0:
            return 1.0
        return (evaluated - self.ext_empty) / evaluated


@dataclass
class RecordMatch:
    """Result of matching an extracted record to a ground truth record."""

    gt_index: int
    ext_index: int
    match_method: str  # "sample_no", "room_location", "fuzzy"
    match_score: float
    field_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class EvalResult:
    """Full evaluation result for one benchmark."""

    benchmark_name: str
    gt_count: int
    extracted_count: int
    matched_count: int
    field_scores: dict[str, FieldScore] = field(default_factory=dict)
    unmatched_gt: list[dict] = field(default_factory=list)
    unmatched_ext: list[dict] = field(default_factory=list)

    @property
    def recall(self) -> float:
        """Record-level recall: matched / ground_truth."""
        if self.gt_count == 0:
            return 1.0
        return self.matched_count / self.gt_count

    @property
    def precision(self) -> float:
        """Record-level precision: matched / extracted."""
        if self.extracted_count == 0:
            return 0.0
        return self.matched_count / self.extracted_count

    @property
    def f1(self) -> float:
        """F1 score (harmonic mean of precision and recall)."""
        p, r = self.precision, self.recall
        if p + r == 0:
            return 0.0
        return 2 * p * r / (p + r)

    @property
    def overall_accuracy(self) -> float:
        """Average exact accuracy across all evaluated fields."""
        scores = [fs.accuracy for fs in self.field_scores.values()]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def to_dict(self) -> dict:
        """Serialize to dict for JSON output."""
        return {
            "benchmark": self.benchmark_name,
            "gt_count": self.gt_count,
            "extracted_count": self.extracted_count,
            "matched_count": self.matched_count,
            "recall": round(self.recall, 4),
            "precision": round(self.precision, 4),
            "f1": round(self.f1, 4),
            "overall_accuracy": round(self.overall_accuracy, 4),
            "field_scores": {
                name: {
                    "accuracy": round(fs.accuracy, 4),
                    "fuzzy_accuracy": round(fs.fuzzy_accuracy, 4),
                    "coverage": round(fs.coverage, 4),
                    "exact_matches": fs.exact_matches,
                    "fuzzy_matches": fs.fuzzy_matches,
                    "mismatches": fs.mismatches,
                    "gt_empty": fs.gt_empty,
                    "ext_empty": fs.ext_empty,
                    "mismatch_examples": fs.mismatch_examples[:5],
                }
                for name, fs in self.field_scores.items()
            },
            "unmatched_gt": self.unmatched_gt[:10],
            "unmatched_ext": self.unmatched_ext[:10],
        }


def load_ground_truth(name: str) -> list[dict]:
    """Load ground truth CSV by benchmark name."""
    path = GT_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Ground truth not found: {path}")
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def load_extracted_from_json(path: str) -> list[dict]:
    """Load extracted records from a JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_extracted_from_db(source_id: str) -> list[dict]:
    """Load extracted records from SurrealDB via HTTP API."""
    import urllib.request

    surreal_url = os.environ.get("SURREAL_URL", "ws://localhost:8000/rpc")
    # Convert ws:// to http:// for REST API
    http_base = surreal_url.replace("ws://", "http://").replace("/rpc", "")

    # Use record link syntax for SurrealDB (no quotes around source:xxx)
    query = f"SELECT * FROM acm_record WHERE source_id = {source_id}"

    import base64

    user = os.environ.get("SURREAL_USER", "root")
    password = os.environ.get("SURREAL_PASSWORD", "root")
    auth = base64.b64encode(f"{user}:{password}".encode()).decode()

    req = urllib.request.Request(
        f"{http_base}/sql",
        data=query.encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "text/plain",
            "surreal-ns": os.environ.get("SURREAL_NAMESPACE", "open_notebook"),
            "surreal-db": os.environ.get("SURREAL_DATABASE", "development"),
            "Authorization": f"Basic {auth}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())

    if not data or data[0].get("status") != "OK":
        raise RuntimeError(f"SurrealDB query failed: {data}")

    return data[0]["result"]


def match_records(
    gt_records: list[dict], ext_records: list[dict]
) -> tuple[list[RecordMatch], list[int], list[int]]:
    """Match extracted records to ground truth records.

    Uses a 3-stage matching strategy:
    1. Exact sample_no match (most reliable)
    2. Room + location match
    3. Fuzzy product + room match

    Returns:
        (matches, unmatched_gt_indices, unmatched_ext_indices)
    """
    matches: list[RecordMatch] = []
    matched_gt: set[int] = set()
    matched_ext: set[int] = set()

    # Stage 1: Sample number match
    for gi, gt in enumerate(gt_records):
        gt_sno = _normalize_sample_no(gt.get("sample_no", ""))
        if not gt_sno or gt_sno in ("not sampled", ""):
            continue
        for ei, ext in enumerate(ext_records):
            if ei in matched_ext:
                continue
            ext_sno = _normalize_sample_no(ext.get("sample_no", ""))
            if ext_sno and ext_sno == gt_sno:
                matches.append(
                    RecordMatch(
                        gt_index=gi,
                        ext_index=ei,
                        match_method="sample_no",
                        match_score=1.0,
                    )
                )
                matched_gt.add(gi)
                matched_ext.add(ei)
                break

    # Stage 2: Room + location + product match
    for gi, gt in enumerate(gt_records):
        if gi in matched_gt:
            continue
        gt_room = _normalize(gt.get("room_name", ""))
        gt_loc = _normalize(gt.get("location", ""))
        gt_prod = _normalize_product(gt.get("product", ""))

        best_score = 0.0
        best_ei = -1
        for ei, ext in enumerate(ext_records):
            if ei in matched_ext:
                continue
            ext_room = _normalize(ext.get("room_name", ""))
            ext_loc = _normalize(ext.get("location", ""))
            ext_prod = _normalize_product(ext.get("product", ""))

            # Composite score: room + location + product
            room_sim = _fuzzy_match(gt_room, ext_room)
            loc_sim = _fuzzy_match(gt_loc, ext_loc)
            prod_sim = _fuzzy_match(gt_prod, ext_prod)
            score = room_sim * 0.3 + loc_sim * 0.3 + prod_sim * 0.4

            if score > best_score:
                best_score = score
                best_ei = ei

        if best_score >= 0.6 and best_ei >= 0:
            matches.append(
                RecordMatch(
                    gt_index=gi,
                    ext_index=best_ei,
                    match_method="room_location_product",
                    match_score=best_score,
                )
            )
            matched_gt.add(gi)
            matched_ext.add(best_ei)

    unmatched_gt = [i for i in range(len(gt_records)) if i not in matched_gt]
    unmatched_ext = [i for i in range(len(ext_records)) if i not in matched_ext]

    return matches, unmatched_gt, unmatched_ext


def evaluate_fields(
    matches: list[RecordMatch],
    gt_records: list[dict],
    ext_records: list[dict],
) -> dict[str, FieldScore]:
    """Evaluate per-field accuracy across matched record pairs."""
    scores: dict[str, FieldScore] = {}
    for field_name in EVAL_FIELDS:
        scores[field_name] = FieldScore(field_name=field_name)

    for match in matches:
        gt = gt_records[match.gt_index]
        ext = ext_records[match.ext_index]

        for field_name in EVAL_FIELDS:
            fs = scores[field_name]
            fs.total += 1

            gt_val = gt.get(field_name, "")
            ext_val = ext.get(field_name, "")

            # Handle None values
            gt_val = str(gt_val).strip() if gt_val else ""
            ext_val = str(ext_val).strip() if ext_val else ""

            # Field-specific normalization
            if field_name == "friable":
                gt_val = _normalize_friability(gt_val) if gt_val else ""
                ext_val = _normalize_friability(ext_val) if ext_val else ""
            elif field_name == "sample_no":
                gt_val = _normalize_sample_no(gt_val)
                ext_val = _normalize_sample_no(ext_val)
            elif field_name == "product":
                gt_val = _normalize_product(gt_val) if gt_val else ""
                ext_val_raw = ext_val
                ext_val = _normalize_product(ext_val) if ext_val else ""
                # If product is "Other", check data_issues for actual product name
                if ext_val == "other" and ext_val_raw.lower() == "other":
                    data_issues = ext.get("data_issues", []) or []
                    for issue in data_issues:
                        if isinstance(issue, str) and issue.startswith("Item name: "):
                            real_product = issue[11:].strip()
                            ext_val = _normalize_product(real_product)
            elif field_name == "area_type":
                gt_val = _normalize_area_type(gt_val) if gt_val else ""
                ext_val = _normalize_area_type(ext_val) if ext_val else ""
            elif field_name == "floor_level":
                gt_val = _normalize_floor_level(gt_val) if gt_val else ""
                ext_val = _normalize_floor_level(ext_val) if ext_val else ""
            elif field_name == "material_condition":
                gt_val = _normalize_condition(gt_val) if gt_val else ""
                ext_val = _normalize_condition(ext_val) if ext_val else ""

            # Skip if ground truth is empty or N/A
            # "N/A (negative)" in condition/disturbance means the field is
            # not applicable for negative samples — treat as empty in GT
            if not gt_val or gt_val.lower().startswith("n/a"):
                fs.gt_empty += 1
                continue

            # Check if extracted is empty
            if not ext_val:
                fs.ext_empty += 1
                fs.mismatches += 1
                fs.mismatch_examples.append(
                    {
                        "gt": gt.get(field_name, ""),
                        "ext": "(empty)",
                        "gt_record": f"GT#{match.gt_index}",
                    }
                )
                continue

            # Compare
            gt_norm = _normalize(gt_val)
            ext_norm = _normalize(ext_val)

            if gt_norm == ext_norm:
                fs.exact_matches += 1
            elif _fuzzy_match(gt_val, ext_val) >= 0.8:
                fs.fuzzy_matches += 1
            else:
                fs.mismatches += 1
                if len(fs.mismatch_examples) < 10:
                    fs.mismatch_examples.append(
                        {
                            "gt": gt.get(field_name, ""),
                            "ext": ext.get(field_name, ""),
                            "gt_record": f"GT#{match.gt_index}",
                        }
                    )

    return scores


def evaluate(
    benchmark_name: str,
    gt_records: list[dict],
    ext_records: list[dict],
) -> EvalResult:
    """Run full evaluation: match records, score fields."""
    matches, unmatched_gt, unmatched_ext = match_records(gt_records, ext_records)

    field_scores = evaluate_fields(matches, gt_records, ext_records)

    result = EvalResult(
        benchmark_name=benchmark_name,
        gt_count=len(gt_records),
        extracted_count=len(ext_records),
        matched_count=len(matches),
        field_scores=field_scores,
        unmatched_gt=[gt_records[i] for i in unmatched_gt],
        unmatched_ext=[
            {
                k: ext_records[i].get(k)
                for k in ["room_name", "product", "sample_no", "location"]
            }
            for i in unmatched_ext
        ],
    )

    return result


def print_report(result: EvalResult) -> None:
    """Print a human-readable evaluation report."""
    print(f"\n{'=' * 70}")
    print(f"  EVALUATION REPORT: {result.benchmark_name}")
    print(f"{'=' * 70}")
    print(f"  Ground Truth: {result.gt_count} records")
    print(f"  Extracted:    {result.extracted_count} records")
    print(f"  Matched:      {result.matched_count} records")
    print(f"  Recall:       {result.recall:.1%}")
    print(f"  Precision:    {result.precision:.1%}")
    print(f"  F1:           {result.f1:.1%}")
    print(f"  Overall Acc:  {result.overall_accuracy:.1%}")

    print(f"\n  {'Field':<25} {'Exact':>7} {'Fuzzy':>7} {'Cover':>7} {'Miss':>5}")
    print(f"  {'-' * 25} {'-' * 7} {'-' * 7} {'-' * 7} {'-' * 5}")
    for name, fs in result.field_scores.items():
        evaluated = fs.total - fs.gt_empty
        if evaluated == 0:
            print(f"  {name:<25} {'N/A':>7} {'N/A':>7} {'N/A':>7} {'N/A':>5}")
        else:
            print(
                f"  {name:<25} {fs.accuracy:>6.1%} {fs.fuzzy_accuracy:>6.1%} "
                f"{fs.coverage:>6.1%} {fs.mismatches:>5}"
            )

    # Show worst fields with examples
    worst = sorted(
        [
            (name, fs)
            for name, fs in result.field_scores.items()
            if (fs.total - fs.gt_empty) > 0
        ],
        key=lambda x: x[1].accuracy,
    )

    if worst:
        print(f"\n  WORST FIELDS (by exact accuracy):")
        for name, fs in worst[:5]:
            if fs.accuracy < 1.0 and fs.mismatch_examples:
                print(f"\n  {name} ({fs.accuracy:.1%}):")
                for ex in fs.mismatch_examples[:3]:
                    print(f"    GT: {ex['gt']!r}  →  EXT: {ex['ext']!r}")

    if result.unmatched_gt:
        print(f"\n  UNMATCHED GROUND TRUTH ({len(result.unmatched_gt)} records):")
        for gt in result.unmatched_gt[:5]:
            room = gt.get("room_name", "?")
            prod = gt.get("product", "?")
            sno = gt.get("sample_no", "?")
            print(f"    {room} / {prod} / {sno}")

    if result.unmatched_ext:
        print(f"\n  UNMATCHED EXTRACTED ({len(result.unmatched_ext)} records):")
        for ext in result.unmatched_ext[:5]:
            room = ext.get("room_name", "?")
            prod = ext.get("product", "?")
            sno = ext.get("sample_no", "?")
            print(f"    {room} / {prod} / {sno}")

    print(f"\n{'=' * 70}\n")


def print_markdown_report(result: EvalResult) -> None:
    """Print a Markdown-formatted evaluation report."""
    print(f"\n## Benchmark: {result.benchmark_name}\n")
    print(f"| Metric | Value |")
    print(f"|--------|-------|")
    print(f"| Ground Truth | {result.gt_count} records |")
    print(f"| Extracted | {result.extracted_count} records |")
    print(f"| Matched | {result.matched_count} records |")
    print(f"| Precision | {result.precision:.1%} |")
    print(f"| Recall | {result.recall:.1%} |")
    print(f"| F1 | {result.f1:.1%} |")
    print(f"| Overall Accuracy | {result.overall_accuracy:.1%} |")

    print(f"\n### Per-Field Accuracy\n")
    print(f"| Field | Exact | Fuzzy | Coverage | Mismatches |")
    print(f"|-------|-------|-------|----------|------------|")
    for name, fs in result.field_scores.items():
        evaluated = fs.total - fs.gt_empty
        if evaluated == 0:
            print(f"| {name} | N/A | N/A | N/A | N/A |")
        else:
            print(
                f"| {name} | {fs.accuracy:.1%} | {fs.fuzzy_accuracy:.1%} | "
                f"{fs.coverage:.1%} | {fs.mismatches} |"
            )

    if result.unmatched_gt:
        print(f"\n### Unmatched Ground Truth ({len(result.unmatched_gt)} records)\n")
        for gt in result.unmatched_gt[:10]:
            room = gt.get("room_name", "?")
            prod = gt.get("product", "?")
            sno = gt.get("sample_no", "?")
            print(f"- {room} / {prod} / {sno}")

    if result.unmatched_ext:
        print(f"\n### Unmatched Extracted ({len(result.unmatched_ext)} records)\n")
        for ext in result.unmatched_ext[:10]:
            room = ext.get("room_name", "?")
            prod = ext.get("product", "?")
            sno = ext.get("sample_no", "?")
            print(f"- {room} / {prod} / {sno}")

    print()


def main():
    parser = argparse.ArgumentParser(description="ACM Prompt Evaluation Harness")
    parser.add_argument(
        "--gt", help="Ground truth benchmark name (broadmeadows, alexander)"
    )
    parser.add_argument("--json", help="Path to extracted records JSON file")
    parser.add_argument("--source-id", help="SurrealDB source ID to fetch records from")
    parser.add_argument(
        "--all", action="store_true", help="Run all benchmarks from cached JSON"
    )
    parser.add_argument("--save", help="Save results to JSON file")
    parser.add_argument(
        "--format",
        choices=["text", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")

    report_fn = print_markdown_report if args.format == "markdown" else print_report
    results: list[EvalResult] = []

    if args.all:
        # Run all benchmarks from cached JSON files
        benchmarks = [
            ("broadmeadows", GT_DIR / "broadmeadows_extracted.json"),
            ("alexander", GT_DIR / "alexander_extracted.json"),
        ]
        for name, json_path in benchmarks:
            if not json_path.exists():
                print(f"Skipping {name}: {json_path} not found")
                continue
            gt = load_ground_truth(name)
            ext = load_extracted_from_json(str(json_path))
            result = evaluate(name, gt, ext)
            report_fn(result)
            results.append(result)
    else:
        if not args.gt:
            parser.error("--gt is required (or use --all)")

        gt = load_ground_truth(args.gt)

        if args.json:
            ext = load_extracted_from_json(args.json)
        elif args.source_id:
            ext = load_extracted_from_db(args.source_id)
        else:
            # Try cached JSON first
            cached = GT_DIR / f"{args.gt}_extracted.json"
            if cached.exists():
                ext = load_extracted_from_json(str(cached))
                print(f"Using cached extraction: {cached}")
            else:
                parser.error(
                    "Provide --json or --source-id (or cache extraction first)"
                )

        result = evaluate(args.gt, gt, ext)
        report_fn(result)
        results.append(result)

    if args.save:
        save_data = [r.to_dict() for r in results]
        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2)
        print(f"Results saved to {args.save}")


if __name__ == "__main__":
    main()
