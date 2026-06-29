from fastapi import APIRouter, HTTPException

from app.core.config import BOT_TOKEN, ADMIN_CHAT_ID
from app.schemas.order import CreateOrderRequest
from app.services.telegram import send_telegram_message
from app.services.telegram_auth import verify_telegram_data

router = APIRouter()


@router.post("/orders")
async def create_order(payload: CreateOrderRequest):
    if not BOT_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="BOT_TOKEN is not configured"
        )

    try:
        validated_data = verify_telegram_data(payload.initData, BOT_TOKEN)
        user_info = validated_data.get("user", {})

        user_chat_id = user_info.get("id")
        username = user_info.get("username", "No username")
        first_name = user_info.get("first_name", "Customer")

        if not user_chat_id:
            raise HTTPException(
                status_code=400,
                detail="Telegram user ID not found"
            )

        order_lines = "\n".join(
            [
                f"• {item.name} x{item.quantity} - ${item.price * item.quantity:.2f}"
                for item in payload.items
            ]
        )

        user_message = f"""
✅ <b>Order Received</b>

Hi {first_name}, your order has been received.

{order_lines}

<b>Total:</b> ${payload.total:.2f}

Thank you for shopping with us!
"""

        admin_message = f"""
🛒 <b>New Order</b>

<b>Customer:</b> {first_name}
<b>Username:</b> @{username}
<b>Telegram ID:</b> {user_chat_id}

{order_lines}

<b>Total:</b> ${payload.total:.2f}
"""

        send_telegram_message(user_chat_id, user_message)

        if ADMIN_CHAT_ID:
            send_telegram_message(ADMIN_CHAT_ID, admin_message)

        return {
            "status": "success",
            "message": "Order created and Telegram message sent",
        }

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))