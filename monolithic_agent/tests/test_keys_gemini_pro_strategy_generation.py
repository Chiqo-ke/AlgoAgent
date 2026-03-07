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

from dotenv import load_dotenv, find_dotenv

# Delay heavy imports until needed to ensure summary files are written


def find_pro_keys_from_env(env_path: Path | None = None) -> list[tuple[str, str]]:
    """Return list of (env_var_name, key) for Gemini Pro keys found in environment.

    Detects any variables starting with GEMINI_KEY_pro_ or API_KEY_gemini_pro_.
    Also includes GEMINI_API_KEY/GOOGLE_API_KEY as fallback.
    """
    keys: list[tuple[str, str]] = []
    prefixes = ("GEMINI_KEY_pro_", "API_KEY_gemini_pro_")
    for name, val in os.environ.items():
        if any(name.startswith(pfx) for pfx in prefixes):
            if val:
                keys.append((name, val))
    # Fallback: single key
    single = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if single:
        keys.append(("GEMINI_API_KEY", single))
    # Deduplicate by name
    seen = set()
    deduped: list[tuple[str, str]] = []
    for name, val in keys:
        if name not in seen:
            deduped.append((name, val))
            seen.add(name)
    # If none detected via os.environ, try parsing the .env directly as fallback
    if not deduped and env_path and env_path.exists():
        try:
            text = env_path.read_text(encoding="utf-8")
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('GEMINI_KEY_pro_') or line.startswith('API_KEY_gemini_pro_'):
                    if '=' in line:
                        name, val = line.split('=', 1)
                        name = name.strip()
                        val = val.strip()
                        if name and val:
                            deduped.append((name, val))
        except Exception:
            pass

    # Sort by name for stable output
    deduped.sort(key=lambda x: x[0])
    return deduped


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
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError:
            raise RuntimeError("google-generativeai not installed. Run: pip install google-generativeai")
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
    # Ensure we load the monolithic_agent/.env specifically,
    # not the project root .env.
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"Loaded env from {env_path}")
    else:
        # Fallback to auto-discovery
        found = find_dotenv(usecwd=True)
        load_dotenv(found) if found else load_dotenv()
        print(f"Loaded env via auto-discovery: {found or 'default search'}")
    keys = find_pro_keys_from_env(env_path)
    print("=" * 80)
    print("GEMINI 2.5 PRO KEY ITERATION TEST")
    print("=" * 80)
    if not keys:
        print("❌ No Gemini Pro keys found in environment. Populate .env (e.g., API_KEY_gemini_pro_01).")
        # Write an empty summary so the user has an artifact
        summary_dir = Path(__file__).parent / "Backtest" / "codes"
        summary_dir.mkdir(parents=True, exist_ok=True)
        summary_file = summary_dir / "key_test_summary_gemini_2_5_pro.txt"
        summary_file.write_text(
            "GEMINI 2.5 PRO KEY ITERATION TEST SUMMARY\nTotal keys: 0\nWorking: 0\nFailing: 0\n",
            encoding="utf-8",
        )
        print(f"Summary saved to: {summary_file}")
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

    # Write file summary for reliable inspection
    summary_dir = Path(__file__).parent / "Backtest" / "codes"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_file = summary_dir / "key_test_summary_gemini_2_5_pro.txt"
    try:
        lines = []
        lines.append("GEMINI 2.5 PRO KEY ITERATION TEST SUMMARY\n")
        lines.append(f"Total keys: {len(results)}\n")
        lines.append(f"Working: {len(ok)}\n")
        for r in ok:
            lines.append(f"OK  {r['key_name']} -> {r['outfile']}\n")
        lines.append(f"Failing: {len(fail)}\n")
        for r in fail:
            lines.append(f"ERR {r['key_name']} -> {r['error']}\n")
        summary_file.write_text("".join(lines), encoding="utf-8")
        print(f"\nSummary saved to: {summary_file}")
    except Exception as e:
        print(f"\nFailed to write summary file: {e}")

    # Exit code: success if at least one key worked
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
