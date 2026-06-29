import json
import urllib.request
import urllib.error
from typing import Optional

from app.core.config import BOT_TOKEN


def call_telegram_api(method: str, data: dict):
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print("Telegram API Error:", error_body)
        raise RuntimeError(error_body)


def send_telegram_message(
    chat_id: int | str,
    text: str,
    reply_markup: Optional[dict] = None,
):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    return call_telegram_api("sendMessage", payload)