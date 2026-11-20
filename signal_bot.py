import os
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
SYMBOL = os.environ.get("SYMBOL", "XAU-USDT-SWAP").strip()
BAR = os.environ.get("BAR_TIMEFRAME", "15m").strip()


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


def main() -> None:
    msg = (
        f"<b>تست اتصال ربات موفق بود</b>\n"
        f"نماد: <code>{SYMBOL}</code> ({BAR})\n"
        f"وضعیت: ارتباط GitHub Actions با تلگرام برقرار است."
    )
    send_telegram(msg)
    print("Test message sent successfully.")


if __name__ == "__main__":
    main()
