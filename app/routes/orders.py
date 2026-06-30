from fastapi import APIRouter, HTTPException

from app.core.config import BOT_TOKEN, ADMIN_CHAT_ID
from app.db.supabase import get_supabase
from app.schemas.order import CreateOrderRequest
from app.services.telegram import send_telegram_message
from app.services.telegram_auth import verify_telegram_data

router = APIRouter()


def get_supabase_or_500():
    try:
        return get_supabase()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def order_error_status(error: Exception):
    message = str(error)

    if "Product not found" in message:
        return 404

    if "Not enough stock" in message or "Order must contain items" in message:
        return 400

    return 500


@router.post("/orders")
async def create_order(
    payload: CreateOrderRequest,
):
    if not BOT_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="BOT_TOKEN is not configured"
        )

    try:
        validated_data = verify_telegram_data(payload.initData, BOT_TOKEN)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user_info = validated_data.get("user", {})

    user_chat_id = user_info.get("id")
    username = user_info.get("username")
    username_display = f"@{username}" if username else "No username"
    first_name = user_info.get("first_name") or "Customer"

    if not user_chat_id:
        raise HTTPException(
            status_code=400,
            detail="Telegram user ID not found"
        )

    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must contain items")

    supabase = get_supabase_or_500()
    order_items = [
        {
            "product_id": item.product_id,
            "quantity": item.quantity,
        }
        for item in payload.items
    ]

    try:
        response = supabase.rpc(
            "create_order_with_items",
            {
                "p_telegram_user_id": str(user_chat_id),
                "p_username": username,
                "p_first_name": first_name,
                "p_items": order_items,
            },
        ).execute()
    except Exception as e:
        raise HTTPException(status_code=order_error_status(e), detail=str(e)) from e

    if not response.data:
        raise HTTPException(status_code=500, detail="Supabase did not return the created order")

    order = response.data[0] if isinstance(response.data, list) else response.data
    order_lines_data = order.get("items") or []

    order_lines = "\n".join(
        [
            f"• {item['name']} x{item['quantity']} - ${item['line_total']:.2f}"
            for item in order_lines_data
        ]
    )

    user_message = f"""
✅ <b>Order Received</b>

Hi {first_name}, your order has been received.

<b>Order ID:</b> #{order['id']}

{order_lines}

<b>Total:</b> ${order['total']:.2f}

Thank you for shopping with us!
"""

    admin_message = f"""
🛒 <b>New Order</b>

<b>Order ID:</b> #{order['id']}
<b>Customer:</b> {first_name}
<b>Username:</b> {username_display}
<b>Telegram ID:</b> {user_chat_id}

{order_lines}

<b>Total:</b> ${order['total']:.2f}
"""

    telegram_sent = True
    telegram_error = None

    try:
        send_telegram_message(user_chat_id, user_message)

        if ADMIN_CHAT_ID:
            send_telegram_message(ADMIN_CHAT_ID, admin_message)

    except Exception as e:
        telegram_sent = False
        telegram_error = str(e)

    return {
        "status": "success",
        "message": "Order created",
        "order": {
            "id": order["id"],
            "total": order["total"],
            "status": order["status"],
        },
        "telegram_sent": telegram_sent,
        "telegram_error": telegram_error,
    }
