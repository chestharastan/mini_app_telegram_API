from fastapi import APIRouter

from app.core.config import FRONTEND_URL
from app.services.telegram import send_telegram_message
from app.services.telegram_contacts import save_telegram_contact

router = APIRouter()

def main_keyboard():
    return {
        "keyboard": [
            [{"text": "🛒 New Order"}, {"text": "📦 My Orders"}],
            [
                {
                    "text": "🛍 Open Shop",
                    "web_app": {
                        "url": FRONTEND_URL
                    }
                },
                {"text": "❓ Help"}
            ],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }

@router.post("/webhook")
async def telegram_webhook(update: dict):
    message = update.get("message", {})
    chat = message.get("chat", {})
    sender = message.get("from", {})
    contact = message.get("contact")
    text = message.get("text", "")
    chat_id = chat.get("id")

    if not chat_id:
        return {"ok": True}

    if contact:
        telegram_user_id = sender.get("id") or chat_id
        contact_user_id = contact.get("user_id")

        if contact_user_id and str(contact_user_id) != str(telegram_user_id):
            send_telegram_message(
                chat_id,
                "Please share your own phone number from Telegram.",
                main_keyboard(),
            )
            return {"ok": True}

        save_telegram_contact(
            telegram_user_id,
            contact.get("phone_number"),
            sender.get("username"),
            contact.get("first_name") or sender.get("first_name"),
        )
        send_telegram_message(
            chat_id,
            "Phone number saved. You can return to checkout.",
            main_keyboard(),
        )
        return {"ok": True}

    if text == "/start":
        send_telegram_message(
            chat_id,
            "Welcome to our computer accessory shop 🖥️\n\nPlease choose an option below:",
            main_keyboard(),
        )

    elif text == "/help" or text == "❓ Help":
        send_telegram_message(
            chat_id,
            "You can use this bot to shop computer accessories.\n\n"
            "🛒 New Order - Start buying products\n"
            "📦 My Orders - View your orders\n"
            "🛍 Open Shop - Open the Mini App",
            main_keyboard(),
        )

    elif text == "🛒 New Order":
        send_telegram_message(
            chat_id,
            "Great! Click 🛍 Open Shop to browse products and place an order.",
            main_keyboard(),
        )

    elif text == "📦 My Orders":
        send_telegram_message(
            chat_id,
            "You do not have any orders yet.",
            main_keyboard(),
        )

    elif text == "🛍 Open Shop":
        send_telegram_message(
            chat_id,
            "Click the 🛍 Open Shop button below to open the shop.",
            # shop_mini_app_keyboard(),
            main_keyboard(),
        )

    else:
        send_telegram_message(
            chat_id,
            "Please choose one option below:",
            main_keyboard(),
        )

    return {"ok": True}
