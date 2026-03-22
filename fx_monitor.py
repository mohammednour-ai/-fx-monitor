"""
CAD Exchange Rate Monitor
Fetches CAD rates vs USD, GBP, EUR, HKD every hour.
Compares to day-open price and sends summary via WhatsApp (Green API).
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# ─── Configuration ───────────────────────────────────────────────────────────
PAIRS = ["USD", "GBP", "EUR", "HKD"]
BASE_CURRENCY = "CAD"

# ExchangeRate-API (free, 1500 req/month)
FX_API_URL = f"https://v6.exchangerate-api.com/v6/{{api_key}}/latest/{BASE_CURRENCY}"

# Environment variables (set as GitHub Secrets)
FX_API_KEY = os.environ.get("FX_API_KEY", "")
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "")  # with country code, no +, e.g. 16475630107
GREENAPI_INSTANCE_ID = os.environ.get("GREENAPI_INSTANCE_ID", "")
GREENAPI_API_TOKEN = os.environ.get("GREENAPI_API_TOKEN", "")
GREENAPI_API_URL = os.environ.get("GREENAPI_API_URL", "https://api.green-api.com")

# File to cache the day-open prices (persisted via GitHub Actions cache)
OPEN_PRICES_FILE = "day_open_prices.json"


def fetch_rates() -> dict:
    """Fetch CAD rates and invert them to get X/CAD (e.g. USD/CAD, GBP/CAD)."""
    url = FX_API_URL.format(api_key=FX_API_KEY)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    if data.get("result") != "success":
        raise RuntimeError(f"API error: {data}")

    rates = data["conversion_rates"]
    # Invert: 1 CAD = X foreign → 1 foreign = 1/X CAD
    return {pair: 1 / rates[pair] for pair in PAIRS}


def load_day_open() -> dict | None:
    """Load cached day-open prices from file."""
    if os.path.exists(OPEN_PRICES_FILE):
        with open(OPEN_PRICES_FILE, "r") as f:
            return json.load(f)
    return None


def save_day_open(rates: dict):
    """Save today's open prices to file."""
    payload = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "rates": rates,
    }
    with open(OPEN_PRICES_FILE, "w") as f:
        json.dump(payload, f, indent=2)


def get_day_open(current_rates: dict) -> dict:
    """
    Return day-open prices. If it's a new day or no cache exists,
    use current rates as the open.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cached = load_day_open()

    if cached and cached.get("date") == today:
        return cached["rates"]

    # New day — current fetch becomes the open
    save_day_open(current_rates)
    return current_rates


def format_message(current: dict, day_open: dict) -> str:
    """Build a clean WhatsApp message with rates and changes."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"📊 CAD FX Monitor — {now}", ""]

    for pair in PAIRS:
        curr_rate = current[pair]
        open_rate = day_open[pair]
        change = curr_rate - open_rate
        pct = (change / open_rate) * 100 if open_rate else 0

        arrow = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
        sign = "+" if change >= 0 else ""

        lines.append(f"{arrow} {pair}/CAD")
        lines.append(f"   Now:  {curr_rate:.4f}")
        lines.append(f"   Open: {open_rate:.4f}")
        lines.append(f"   Chg:  {sign}{change:.4f} ({sign}{pct:.2f}%)")
        lines.append("")

    lines.append("1 unit of foreign currency = X CAD")
    return "\n".join(lines)


def send_whatsapp(message: str):
    """Send message via Green API WhatsApp."""
    url = f"{GREENAPI_API_URL}/waInstance{GREENAPI_INSTANCE_ID}/sendMessage/{GREENAPI_API_TOKEN}"
    payload = json.dumps({
        "chatId": f"{WHATSAPP_NUMBER}@c.us",
        "message": message,
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = resp.read().decode()
        print(f"Green API response: {result}")


def main():
    print("🔄 Fetching CAD exchange rates...")
    current = fetch_rates()
    print(f"   Current rates: {current}")

    day_open = get_day_open(current)
    print(f"   Day open rates: {day_open}")

    message = format_message(current, day_open)
    print(f"\n📨 Message:\n{message}\n")

    if WHATSAPP_NUMBER and GREENAPI_INSTANCE_ID and GREENAPI_API_TOKEN:
        send_whatsapp(message)
        print("✅ WhatsApp message sent!")
    else:
        print("⚠️  WhatsApp credentials not set. Message printed above only.")


if __name__ == "__main__":
    main()
