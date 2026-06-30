import re

from fastapi import APIRouter, HTTPException

from app.core.config import BOT_TOKEN, ADMIN_CHAT_ID
from app.db.supabase import get_supabase
from app.schemas.order import CreateOrderRequest
from app.services.telegram import send_telegram_message
from app.services.telegram_auth import verify_telegram_data
from app.services.telegram_contacts import (
    get_telegram_contact,
    save_telegram_contact,
    upsert_telegram_user,
)

router = APIRouter()


def normalize_phone_number(value: str):
    phone = re.sub(r"[^\d+]", "", value.strip())
    return re.sub(r"(?!^)\+", "", phone)


def is_valid_phone_number(value: str):
    digit_count = len(re.sub(r"\D", "", value))
    return 7 <= digit_count <= 15


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
    is_web_checkout = username == "web_checkout"
    username_display = f"@{username}" if username else "No username"
    first_name = user_info.get("first_name") or "Customer"

    if not user_chat_id:
        raise HTTPException(
            status_code=400,
            detail="Telegram user ID not found"
        )

    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must contain items")

    upsert_telegram_user(user_info)

    raw_customer_phone = payload.customerPhone or get_telegram_contact(user_chat_id)
    customer_phone = normalize_phone_number(raw_customer_phone) if raw_customer_phone else None

    if customer_phone and not is_valid_phone_number(customer_phone):
        raise HTTPException(status_code=400, detail="A valid customer phone number is required")

    if not customer_phone and not is_web_checkout:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "PHONE_REQUIRED",
                "message": (
                    "We only need your phone number once so the seller or "
                    "delivery team can contact you about your order."
                ),
            },
        )

    if customer_phone:
        save_telegram_contact(
            user_chat_id,
            customer_phone,
            username,
            first_name,
        )

    customer_reference = customer_phone or str(user_chat_id)
    customer_reference_label = "Phone" if customer_phone else "Customer ID"

    stored_first_name = (
        first_name
        if customer_reference in first_name
        else f"{first_name} ({customer_reference})"
    )

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
                "p_first_name": stored_first_name,
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
<b>{customer_reference_label}:</b> {customer_reference}
<b>Source:</b> {"Vercel web checkout" if is_web_checkout else "Telegram Mini App"}
<b>Username:</b> {username_display}
<b>Telegram ID:</b> {user_chat_id}

{order_lines}

<b>Total:</b> ${order['total']:.2f}
"""

    telegram_sent = True
    telegram_error = None
    admin_sent = False
    admin_error = None

    if is_web_checkout:
        telegram_sent = False
        telegram_error = "Skipped customer Telegram message for web checkout"
    else:
        try:
            send_telegram_message(user_chat_id, user_message)
        except Exception as e:
            telegram_sent = False
            telegram_error = str(e)

    if ADMIN_CHAT_ID:
        try:
            send_telegram_message(ADMIN_CHAT_ID, admin_message)
            admin_sent = True
        except Exception as e:
            admin_error = str(e)

    return {
        "status": "success",
        "message": "Order created",
        "order": {
            "id": order["id"],
            "total": order["total"],
            "status": order["status"],
            "customer_phone": customer_phone,
            "customer_reference": customer_reference,
        },
        "telegram_sent": telegram_sent,
        "telegram_error": telegram_error,
        "admin_sent": admin_sent,
        "admin_error": admin_error,
    }
