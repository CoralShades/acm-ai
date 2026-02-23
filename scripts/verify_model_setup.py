"""
Verify Model Setup — ACM-AI

Tests that a given model is reachable, supports JSON mode, and can extract
ACM records from a sample register chunk.

Usage:
    uv run python scripts/verify_model_setup.py --model ollama/qwen2.5:32b
    uv run python scripts/verify_model_setup.py --model openrouter/qwen/qwen2.5-32b-instruct
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

# Known model specs (provider_defaults from open_notebook/domain/models.py)
MODEL_SPECS: dict[str, dict[str, int]] = {
    "qwen2.5:32b": {"context": 131072, "max_output": 8192},
    "qwen2.5-32b-instruct": {"context": 131072, "max_output": 8192},
    "qwen2.5:14b": {"context": 131072, "max_output": 8192},
    "qwen2.5:7b": {"context": 131072, "max_output": 8192},
    "qwen2.5-72b-instruct": {"context": 131072, "max_output": 8192},
    "qwen3:32b": {"context": 131072, "max_output": 8192},
    "qwen3:14b": {"context": 131072, "max_output": 8192},
    "deepseek-chat": {"context": 163840, "max_output": 8192},
    "llama-3.3-70b-instruct": {"context": 131072, "max_output": 8192},
}

# Sample ACM register chunk for extraction test
SAMPLE_REGISTER = """
BUILDING: B00A - Administration Block

| Room | Item | Product | Condition | Result |
|------|------|---------|-----------|--------|
| Foyer | Ceiling tiles | Chrysotile | Good | Detected |
| Office 1 | Vinyl floor tiles | Chrysotile | Fair | Detected |
| Office 2 | Pipe lagging | Amosite | Poor | Detected |
| Kitchen | Splashback | No asbestos | Good | Not detected |
| Store Room | No access | - | - | Not sampled |
| Electrical | Switchboard | Fuse cartridge | Fair | Detected |
""".strip()

EXTRACTION_PROMPT = """You are an ACM (Asbestos Containing Material) register extraction assistant.
Extract all ACM records from the register data below as a JSON object with a "records" array.
Each record must have: room, item, product, condition, result.

Register data:
{register}

Respond ONLY with a JSON object. No other text."""


def check_pass(label: str) -> None:
    print(f"  [PASS] {label}")


def check_fail(label: str, detail: str = "") -> None:
    msg = f"  [FAIL] {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)


def check_skip(label: str, detail: str = "") -> None:
    msg = f"  [SKIP] {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)


def parse_model_arg(model_str: str) -> tuple[str, str]:
    """Parse provider/model_name from CLI argument."""
    parts = model_str.split("/", 1)
    if len(parts) != 2:
        print(f"Error: Invalid model format '{model_str}'. Expected 'provider/model_name'")
        sys.exit(1)
    return parts[0], parts[1]


def check_reachability_ollama(base_url: str, model_name: str) -> bool:
    """Check if Ollama is reachable and the model is available."""
    try:
        req = urllib.request.Request(f"{base_url}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            models = [m.get("name", "") for m in data.get("models", [])]
            # Check exact match or prefix match (e.g., qwen2.5:32b matches qwen2.5:32b-q4_K_M)
            found = any(
                model_name == m or m.startswith(model_name.split(":")[0])
                for m in models
            )
            if found:
                check_pass(f"Model reachable at {base_url}")
            else:
                check_fail(
                    "Model not found",
                    f"Available: {', '.join(models[:5])}{'...' if len(models) > 5 else ''}",
                )
            return found
    except (urllib.error.URLError, OSError) as e:
        check_fail("Model reachable", f"Cannot connect to Ollama at {base_url}: {e}")
        return False


def check_reachability_openrouter(api_key: str) -> bool:
    """Check if OpenRouter API is reachable."""
    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                check_pass("OpenRouter API reachable")
                return True
            check_fail("OpenRouter API reachable", f"HTTP {resp.status}")
            return False
    except (urllib.error.URLError, OSError) as e:
        check_fail("OpenRouter API reachable", str(e))
        return False


def check_context_window(model_name: str) -> bool:
    """Verify context window from known specs."""
    # Normalize model name for lookup
    lookup_name = model_name.split("/")[-1] if "/" in model_name else model_name
    specs = MODEL_SPECS.get(lookup_name)

    if specs:
        ctx = specs["context"]
        check_pass(f"Context window: {ctx:,} tokens")
        # Check if Broadmeadows PDF fits (~45k tokens)
        if ctx >= 45000:
            check_pass(f"Token estimate for Broadmeadows PDF: ~45,000 tokens (fits in {ctx:,})")
        else:
            check_fail(
                "Broadmeadows PDF fit",
                f"~45,000 tokens needed but context is only {ctx:,}",
            )
        return True
    else:
        check_skip("Context window", f"No specs for '{lookup_name}' — check docs/development/qwen25-setup-guide.md")
        return True  # Not a failure, just unknown


def check_json_mode_ollama(base_url: str, model_name: str) -> bool:
    """Test JSON mode extraction with Ollama."""
    prompt = EXTRACTION_PROMPT.format(register=SAMPLE_REGISTER)
    payload = json.dumps({
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0, "num_predict": 2048},
    }).encode()

    try:
        req = urllib.request.Request(
            f"{base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
            response_text = data.get("response", "")

            # Try to parse JSON
            try:
                parsed = json.loads(response_text)
            except json.JSONDecodeError:
                # Try brace-depth extraction
                parsed = _extract_json(response_text)

            if parsed is None:
                check_fail("JSON mode", "Response is not valid JSON")
                return False

            check_pass("JSON mode: supported")

            # Check record count
            records = parsed.get("records", parsed.get("data", []))
            if isinstance(records, list) and len(records) >= 4:
                check_pass(f"Sample extraction: {len(records)} records from test chunk")
                return True
            else:
                check_fail(
                    "Sample extraction",
                    f"Expected >= 4 records, got {len(records) if isinstance(records, list) else 0}",
                )
                return False

    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        check_fail("JSON mode", str(e))
        return False


def check_json_mode_openrouter(api_key: str, model_name: str) -> bool:
    """Test JSON mode extraction with OpenRouter."""
    prompt = EXTRACTION_PROMPT.format(register=SAMPLE_REGISTER)
    payload = json.dumps({
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"},
    }).encode()

    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                parsed = _extract_json(content)

            if parsed is None:
                check_fail("JSON mode", "Response is not valid JSON")
                return False

            check_pass("JSON mode: supported")

            records = parsed.get("records", parsed.get("data", []))
            if isinstance(records, list) and len(records) >= 4:
                check_pass(f"Sample extraction: {len(records)} records from test chunk")
                return True
            else:
                check_fail(
                    "Sample extraction",
                    f"Expected >= 4 records, got {len(records) if isinstance(records, list) else 0}",
                )
                return False

    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        check_fail("JSON mode", str(e))
        return False


def _extract_json(text: str) -> dict | None:
    """Extract JSON object using brace-depth matching (mirrors parse_json_response in utils.py)."""
    brace_start = text.find("{")
    if brace_start < 0:
        return None
    depth = 0
    for idx, c in enumerate(text[brace_start:]):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[brace_start : brace_start + idx + 1])
                except json.JSONDecodeError:
                    return None
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify AI model setup for ACM-AI extraction"
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Model in provider/name format (e.g., ollama/qwen2.5:32b or openrouter/qwen/qwen2.5-32b-instruct)",
    )
    parser.add_argument(
        "--skip-extraction",
        action="store_true",
        help="Skip the live extraction test (only check reachability and specs)",
    )
    args = parser.parse_args()

    provider, model_name = parse_model_arg(args.model)
    print(f"\nVerifying model: {provider}/{model_name}")
    print("=" * 60)

    results: list[bool] = []

    if provider == "ollama":
        base_url = os.getenv("OLLAMA_API_BASE", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        results.append(check_reachability_ollama(base_url, model_name))
        results.append(check_context_window(model_name))
        if not args.skip_extraction and results[0]:
            results.append(check_json_mode_ollama(base_url, model_name))
        elif args.skip_extraction:
            check_skip("JSON mode", "skipped via --skip-extraction")
            check_skip("Sample extraction", "skipped via --skip-extraction")

    elif provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            check_fail("OpenRouter API key", "OPENROUTER_API_KEY not set in environment")
            results.append(False)
        else:
            results.append(check_reachability_openrouter(api_key))
            results.append(check_context_window(model_name))
            if not args.skip_extraction and results[0]:
                results.append(check_json_mode_openrouter(api_key, model_name))
            elif args.skip_extraction:
                check_skip("JSON mode", "skipped via --skip-extraction")
                check_skip("Sample extraction", "skipped via --skip-extraction")

    else:
        check_fail("Provider", f"Unknown provider '{provider}'. Supported: ollama, openrouter")
        results.append(False)

    # Summary
    print("=" * 60)
    passed = sum(1 for r in results if r)
    total = len(results)
    if all(results):
        print(f"\nAll checks passed ({passed}/{total})")
        sys.exit(0)
    else:
        failed = total - passed
        print(f"\n{failed} check(s) failed ({passed}/{total} passed)")
        sys.exit(1)


if __name__ == "__main__":
    main()
