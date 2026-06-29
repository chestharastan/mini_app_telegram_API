import hmac
import hashlib
import json
from urllib.parse import parse_qsl, unquote


def verify_telegram_data(init_data: str, bot_token: str) -> dict:
    if not bot_token:
        raise ValueError("BOT_TOKEN is not configured")

    parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))

    if "hash" not in parsed_data:
        raise ValueError("Missing hash parameter")

    received_hash = parsed_data.pop("hash")

    data_check_string = "\n".join(
        f"{key}={unquote(value)}"
        for key, value in sorted(parsed_data.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256
    ).digest()

    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise ValueError("Data integrity verification failed")

    if "user" in parsed_data:
        parsed_data["user"] = json.loads(unquote(parsed_data["user"]))

    return parsed_data