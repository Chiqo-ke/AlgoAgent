"""
Iterate Gemini Pro API keys and attempt strategy code generation.

For each detected key, uses model 'gemini-2.5-pro' to generate a simple
EMA crossover bot script and saves the output for inspection.

This does NOT rely on the internal GeminiStrategyGenerator to allow
explicit model control and per-key isolation during diagnostics.
"""

import os
import sys
from pathlib import Path
import time

from dotenv import load_dotenv

try:
    import google.generativeai as genai
except ImportError:
    print("google-generativeai not installed. Run: pip install google-generativeai")
    sys.exit(1)


def find_pro_keys_from_env() -> list[tuple[str, str]]:
    """Return list of (env_var_name, key) for Gemini Pro keys in environment."""
    keys: list[tuple[str, str]] = []
    # Common patterns from .env.example and prior tests
    patterns = [
        "API_KEY_gemini_pro_01",
        "API_KEY_gemini_pro_02",
        "API_KEY_gemini_pro_03",
        "GEMINI_KEY_pro_01",
        "GEMINI_KEY_pro_02",
        "GEMINI_KEY_pro_03",
    ]
    for name in patterns:
        val = os.getenv(name)
        if val:
            keys.append((name, val))
    # Fallback: single key
    single = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if single:
        keys.append(("GEMINI_API_KEY", single))
    return keys


def build_prompt() -> str:
    """Construct a concise prompt asking for a SimBroker-compatible bot script."""
    system_hint = (
        "You are generating Python trading bot code compatible with a stable SimBroker API. "
        "Produce a single, self-contained Python script with a strategy class and entry/exit logic. "
        "Avoid external network calls, keep it deterministic, and include a simple run() entry."
    )
    user_request = (
        "Create a minimal EMA crossover bot using fast=12 and slow=26. "
        "Open long when EMA12 crosses above EMA26; short when below. "
        "Include stop loss and take profit placeholders (no live data). "
        "Return only code; no Markdown or prose."
    )
    return f"{system_hint}\n\n{user_request}"


def try_generate_with_key(key_name: str, api_key: str, out_dir: Path) -> dict:
    """Attempt generation with a given key; return result dict."""
    result = {"key_name": key_name, "ok": False, "error": None, "outfile": None}
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-pro")
        prompt = build_prompt()

        # Basic throttling to be courteous to quotas
        time.sleep(float(os.getenv("GEMINI_REQUEST_DELAY", "2")))

        resp = model.generate_content(prompt)
        text = getattr(resp, "text", None) or (resp.candidates[0].content.parts[0].text if getattr(resp, "candidates", None) else "")
        if not text:
            raise RuntimeError("Empty response text")

        # Save output
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"generated_by_{key_name.lower().replace(' ', '_')}.py"
        outfile = out_dir / filename
        outfile.write_text(text)
        result["ok"] = True
        result["outfile"] = str(outfile)
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


def main():
    load_dotenv()
    keys = find_pro_keys_from_env()
    print("=" * 80)
    print("GEMINI 2.5 PRO KEY ITERATION TEST")
    print("=" * 80)
    if not keys:
        print("❌ No Gemini Pro keys found in environment. Populate .env (e.g., API_KEY_gemini_pro_01).")
        sys.exit(1)

    out_dir = Path(__file__).parent / "Backtest" / "codes" / "generated_by_keys"
    results = []
    for name, key in keys:
        safe = f"{key[:10]}..." if key else "(empty)"
        print(f"\nTesting key {name}: {safe}")
        res = try_generate_with_key(name, key, out_dir)
        status = "✅ OK" if res["ok"] else "❌ FAIL"
        print(f"Result: {status}")
        if res["ok"]:
            print(f"Saved: {res['outfile']}")
        else:
            print(f"Error: {res['error']}")
        results.append(res)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    ok = [r for r in results if r["ok"]]
    fail = [r for r in results if not r["ok"]]
    print(f"Working keys: {len(ok)}")
    for r in ok:
        print(f" - {r['key_name']} -> {r['outfile']}")
    print(f"Failing keys: {len(fail)}")
    for r in fail:
        print(f" - {r['key_name']} -> {r['error']}")

    # Exit code: success if at least one key worked
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
