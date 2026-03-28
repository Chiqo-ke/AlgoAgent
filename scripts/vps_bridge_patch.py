"""
VPS Bridge Patch — Phase 2
===========================
This script appends two new Flask endpoints to mt5_bridge.py on the VPS.

Usage (run on VPS as root or algoagent):
    python3 vps_bridge_patch.py

After running:
    sudo systemctl restart mt5_bridge
"""

import os
import re

BRIDGE_PATH = "/home/algoagent/.mt5/drive_c/mt5_bridge/mt5_bridge.py"
MARKER = "# ── order_calc_profit / order_calc_margin endpoints (Phase 2 patch) ──"

NEW_ENDPOINTS = '''

# ── order_calc_profit / order_calc_margin endpoints (Phase 2 patch) ──

@app.route("/order_calc_profit", methods=["POST"])
def order_calc_profit():
    """
    Calculate profit/loss for a hypothetical order.

    Body JSON:
        action      int   0=BUY, 1=SELL
        symbol      str
        volume      float  lots
        price_open  float
        price_close float

    Returns:
        {"profit": <float>}  or  {"error": "<msg>"}
    """
    data = request.get_json(force=True) or {}
    action      = data.get("action", 0)
    symbol      = data.get("symbol")
    volume      = data.get("volume", 1.0)
    price_open  = data.get("price_open")
    price_close = data.get("price_close")

    if not all([symbol, price_open is not None, price_close is not None]):
        return jsonify({"error": "Missing required fields: symbol, price_open, price_close"}), 400

    result = mt5.order_calc_profit(action, symbol, volume, price_open, price_close)
    if result is None:
        err = mt5.last_error()
        return jsonify({"error": f"order_calc_profit failed: {err}"}), 500
    return jsonify({"profit": result})


@app.route("/order_calc_margin", methods=["POST"])
def order_calc_margin():
    """
    Calculate required margin for a hypothetical order.

    Body JSON:
        action  int   0=BUY, 1=SELL
        symbol  str
        volume  float  lots
        price   float  opening price

    Returns:
        {"margin": <float>}  or  {"error": "<msg>"}
    """
    data = request.get_json(force=True) or {}
    action = data.get("action", 0)
    symbol = data.get("symbol")
    volume = data.get("volume", 1.0)
    price  = data.get("price")

    if not all([symbol, price is not None]):
        return jsonify({"error": "Missing required fields: symbol, price"}), 400

    result = mt5.order_calc_margin(action, symbol, volume, price)
    if result is None:
        err = mt5.last_error()
        return jsonify({"error": f"order_calc_margin failed: {err}"}), 500
    return jsonify({"margin": result})

'''


def patch():
    if not os.path.exists(BRIDGE_PATH):
        print(f"ERROR: Bridge file not found at {BRIDGE_PATH}")
        return False

    with open(BRIDGE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if MARKER in content:
        print("Bridge already patched — skipping.")
        return True

    # Find the last Flask route or app.run() to insert before it
    insert_before = re.search(r"^if __name__\s*==\s*['\"]__main__['\"]", content, re.MULTILINE)
    if insert_before:
        pos = insert_before.start()
    else:
        pos = len(content)

    patched = content[:pos] + NEW_ENDPOINTS + content[pos:]

    # Backup
    backup_path = BRIDGE_PATH + ".bak"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Backup written to {backup_path}")

    with open(BRIDGE_PATH, "w", encoding="utf-8") as f:
        f.write(patched)

    print(f"Patch applied to {BRIDGE_PATH}")
    print("IMPORTANT: Run 'sudo systemctl restart mt5_bridge' to activate.")
    return True


if __name__ == "__main__":
    patch()
