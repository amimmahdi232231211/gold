import json
import os
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
SYMBOL = os.environ.get("SYMBOL", "XAU-USDT-SWAP").strip()
BAR = os.environ.get("BAR_TIMEFRAME", "15m").strip()
STATE_FILE = "state.json"


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {"last_sent_ts": 0}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def fetch_candles(inst_id: str, bar: str, limit: int = 250) -> list[dict]:
    url = "https://www.okx.com/api/v5/market/candles"
    params = {"instId": inst_id, "bar": bar, "limit": str(limit)}
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != "0" or not data.get("data"):
        raise RuntimeError(f"OKX API error: {data}")

    candles = []
    for row in reversed(data["data"]):
        candles.append({
            "ts": int(row[0]),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "vol": float(row[5]),
            "confirm": row[8] == "1",
        })
    return candles


def send_telegram(text: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()


def evaluate_signal(closed_candles: list[dict]) -> dict | None:
    if len(closed_candles) < 20:
        return None

    last = closed_candles[-1]
    prev_highs = max(c["high"] for c in closed_candles[-13:-1])
    prev_lows = min(c["low"] for c in closed_candles[-13:-1])

    if last["close"] > prev_highs:
        return {
            "side": "LONG",
            "price": last["close"],
            "reason": "شکست سقف کندل‌های اخیر (تست اولیه)",
        }
    if last["close"] < prev_lows:
        return {
            "side": "SHORT",
            "price": last["close"],
            "reason": "شکست کف کندل‌های اخیر (تست اولیه)",
        }
    return None


def main() -> None:
    candles = fetch_candles(SYMBOL, BAR, limit=250)
    closed = [c for c in candles if c["confirm"]]
    if not closed:
        print("No confirmed candle yet.")
        return

    latest_closed = closed[-1]
    state = load_state()
    last_sent_ts = int(state.get("last_sent_ts", 0))

    if latest_closed["ts"] == last_sent_ts:
        print("Already processed this candle.")
        return

    sig = evaluate_signal(closed)
    if sig:
        msg = (
            f"<b>هشدار سیگنال طلا</b>\n"
            f"نماد: <code>{SYMBOL}</code> ({BAR})\n"
            f"جهت: <b>{sig['side']}</b>\n"
            f"قیمت بسته شدن: <code>{sig['price']}</code>\n"
            f"توضیح: {sig['reason']}"
        )
        send_telegram(msg)
        state["last_sent_ts"] = latest_closed["ts"]
        save_state(state)
        print("Alert sent and state updated.")
    else:
        print("No signal on latest closed candle.")


if __name__ == "__main__":
    main()
