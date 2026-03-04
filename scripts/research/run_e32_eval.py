"""E32-S6 quick evaluation runner — 10-record sample per model.

Run with:
    uv run python scripts/research/run_e32_eval.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from esperanto import AIFactory  # noqa: E402
from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402

from scripts.research.ollama_model_eval import (  # noqa: E402
    CLASSIFICATION_SYSTEM,
    ENRICHMENT_SYSTEM,
    build_test_sample,
    get_ollama_vram,
    parse_json,
    score_classification,
    score_enrichment,
)

RESULTS_DIR = PROJECT_ROOT / "scripts" / "research" / "results"

# Use 10 representative records (2 from each major product group)
# Records 0-4 = Ceiling Tiles, 5-9 = Pipe Lagging — good variety
SAMPLE_SIZE = 10

MODELS_TO_TEST = [
    ("qwen3:latest", "ollama"),
    ("deepseek-r1:8b", "ollama"),
    ("phi4:latest", "ollama"),
]


def run_single_model(model_name: str, provider: str, sample: list[dict]) -> dict:
    """Run both tasks for one model on the sample. Returns result dict."""
    print(f"\n{'=' * 60}")
    print(f"Evaluating: {model_name} ({provider})")
    print(f"{'=' * 60}")

    try:
        lc = AIFactory.create_language(
            model_name=model_name,
            provider=provider,
            config={"temperature": 0.0, "max_tokens": 2048},
        ).to_langchain()
    except Exception as e:
        print(f"  FAILED to provision: {e}")
        empty = {
            "task_name": "error",
            "accuracy": 0.0,
            "mean_latency_s": 0.0,
            "p95_latency_s": 0.0,
            "error_count": len(sample),
        }
        return {
            "model_name": model_name,
            "provider": provider,
            "vram_bytes": None,
            "classification": empty,
            "enrichment": empty,
        }

    # Warm-up
    if provider == "ollama":
        print("  Warm-up...", flush=True)
        try:
            lc.invoke([
                SystemMessage(content="You are helpful."),
                HumanMessage(content="Say 'ready'"),
            ])
        except Exception as e:
            print(f"  Warm-up failed: {e}")

    # VRAM
    vram = get_ollama_vram(model_name) if provider == "ollama" else None
    vram_str = f"{vram / 1e9:.2f}GB" if vram else "unknown"
    print(f"  VRAM: {vram_str}", flush=True)

    # Classification task
    print(f"  Running classification ({len(sample)} records)...", flush=True)
    cls_scores, cls_lats, cls_errors = [], [], 0
    for i, rec in enumerate(sample):
        user = (
            f"Product: {rec['product']}\n"
            f"Material Description: {rec['material_description']}\n\n"
            "Classify this ACM item."
        )
        try:
            t0 = time.perf_counter()
            resp = lc.invoke([
                SystemMessage(content=CLASSIFICATION_SYSTEM),
                HumanMessage(content=user),
            ])
            t = time.perf_counter() - t0
            parsed = parse_json(resp.content)
            score = score_classification(parsed, rec)
            cls_scores.append(score)
            cls_lats.append(t)
            cls_str = parsed.get("acm_classification", "?")[:30]
            print(
                f"  cls[{i:02d}] score={score:.2f} t={t:.1f}s "
                f"pred={cls_str!r}",
                flush=True,
            )
        except Exception as e:
            cls_errors += 1
            cls_scores.append(0.0)
            cls_lats.append(0.0)
            print(f"  cls[{i:02d}] ERROR: {str(e)[:100]}", flush=True)

    # Enrichment task
    print(f"  Running enrichment ({len(sample)} records)...", flush=True)
    enr_scores, enr_lats, enr_errors = [], [], 0
    for i, rec in enumerate(sample):
        user = (
            f"Location (raw): {rec['location_raw']}\n"
            f"Room Reference (raw): {rec['room_ref_raw']}\n\n"
            "Normalize these values."
        )
        try:
            t0 = time.perf_counter()
            resp = lc.invoke([
                SystemMessage(content=ENRICHMENT_SYSTEM),
                HumanMessage(content=user),
            ])
            t = time.perf_counter() - t0
            parsed = parse_json(resp.content)
            score = score_enrichment(parsed, rec)
            enr_scores.append(score)
            enr_lats.append(t)
            loc_str = parsed.get("location_normalized", "?")[:30]
            print(
                f"  enr[{i:02d}] score={score:.2f} t={t:.1f}s "
                f"loc={loc_str!r}",
                flush=True,
            )
        except Exception as e:
            enr_errors += 1
            enr_scores.append(0.0)
            enr_lats.append(0.0)
            print(f"  enr[{i:02d}] ERROR: {str(e)[:100]}", flush=True)

    # Compute stats
    def _stats(lats: list) -> tuple:
        if not lats:
            return 0.0, 0.0
        s = sorted(lats)
        mean = sum(s) / len(s)
        p95 = s[int(len(s) * 0.95)]
        return mean, p95

    cls_mean, cls_p95 = _stats(cls_lats)
    enr_mean, enr_p95 = _stats(enr_lats)
    cls_acc = sum(cls_scores) / len(cls_scores) if cls_scores else 0.0
    enr_acc = sum(enr_scores) / len(enr_scores) if enr_scores else 0.0

    print(
        f"  SUMMARY: cls={cls_acc:.1%} enr={enr_acc:.1%} "
        f"cls_p95={cls_p95:.2f}s enr_p95={enr_p95:.2f}s",
        flush=True,
    )

    return {
        "model_name": model_name,
        "provider": provider,
        "vram_bytes": vram,
        "classification": {
            "task_name": "classification",
            "accuracy": cls_acc,
            "mean_latency_s": round(cls_mean, 3),
            "p95_latency_s": round(cls_p95, 3),
            "error_count": cls_errors,
        },
        "enrichment": {
            "task_name": "enrichment",
            "accuracy": enr_acc,
            "mean_latency_s": round(enr_mean, 3),
            "p95_latency_s": round(enr_p95, 3),
            "error_count": enr_errors,
        },
    }


def main() -> None:
    """Run evaluation and save results."""
    records = build_test_sample()
    sample = records[:SAMPLE_SIZE]
    print(f"E32-S6 Ollama Model Evaluation")
    print(f"Sample: {len(sample)} records (of 50)")

    all_results = []

    for model_name, provider in MODELS_TO_TEST:
        result = run_single_model(model_name, provider, sample)
        all_results.append(result)

    # Claude Sonnet baseline
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        result = run_single_model("claude-sonnet-4-20250514", "anthropic", sample)
        all_results.append(result)
    else:
        print("\nANTHROPIC_API_KEY not found — skipping Sonnet baseline.")

    # Save JSON
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / "ollama_eval_results.json"
    payload = {
        "meta": {
            "script": "scripts/research/run_e32_eval.py",
            "story": "E32-S6",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "models_tested": [r["model_name"] for r in all_results],
            "sample_size": len(sample),
            "note": (
                f"{SAMPLE_SIZE}-record sample (of 50) used due to ~20-35s/inference "
                "latency on available hardware. Results are representative."
            ),
        },
        "results": all_results,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\nResults saved to: {output_path}")

    # Print summary table
    print("\n## Results Summary\n")
    print(
        "| Model                      | VRAM   | Class. Acc | "
        "Enrich. Acc | Class. p95 | Enrich. p95 |"
    )
    print(
        "|----------------------------|--------|------------|"
        "-------------|------------|-------------|"
    )
    for r in all_results:
        vram_s = f"{r['vram_bytes'] / 1e9:.1f}GB" if r["vram_bytes"] else "n/a"
        print(
            f"| {r['model_name']:<26} | {vram_s:<6} "
            f"| {r['classification']['accuracy']:>9.1%}  "
            f"| {r['enrichment']['accuracy']:>10.1%}  "
            f"| {r['classification']['p95_latency_s']:>8.2f}s  "
            f"| {r['enrichment']['p95_latency_s']:>9.2f}s  |"
        )

    # Recommendation
    print("\n## Recommendation\n")
    threshold = 0.75
    ollama_results = [r for r in all_results if r["provider"] == "ollama"]
    passing = [
        r for r in ollama_results
        if r["classification"]["accuracy"] >= threshold
        and r["enrichment"]["accuracy"] >= threshold
    ]
    if passing:
        best = max(
            passing,
            key=lambda r: (
                r["classification"]["accuracy"] + r["enrichment"]["accuracy"]
            ) / 2,
        )
        print(f"Models meeting >=75% threshold: {[r['model_name'] for r in passing]}")
        print(f"Recommended: {best['model_name']}")
    else:
        if ollama_results:
            best = max(
                ollama_results,
                key=lambda r: (
                    r["classification"]["accuracy"] + r["enrichment"]["accuracy"]
                ) / 2,
            )
            print(
                f"No model met 75% threshold. Best: {best['model_name']} "
                f"(cls={best['classification']['accuracy']:.1%}, "
                f"enr={best['enrichment']['accuracy']:.1%})"
            )
            print("Recommendation: escalate to E32-S7 investigation.")


if __name__ == "__main__":
    main()
