from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import BOT_TOKEN, ADMIN_CHAT_ID
from app.db.database import get_db
from app.db.models import Order as OrderModel
from app.db.models import OrderItem as OrderItemModel
from app.db.models import Product
from app.schemas.order import CreateOrderRequest
from app.services.telegram import send_telegram_message
from app.services.telegram_auth import verify_telegram_data

router = APIRouter()


@router.post("/orders")
async def create_order(
    payload: CreateOrderRequest,
    db: Session = Depends(get_db),
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

    order = OrderModel(
        telegram_user_id=str(user_chat_id),
        username=username,
        first_name=first_name,
        total=0,
    )

    order_lines_data = []
    total = 0.0

    try:
        for item in payload.items:
            product = db.get(Product, item.product_id)

            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product not found: {item.product_id}",
                )

            if product.stock < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Not enough stock for {product.name}",
                )

            line_total = product.price * item.quantity
            total += line_total
            product.stock -= item.quantity

            order.items.append(
                OrderItemModel(
                    product_id=product.id,
                    name=product.name,
                    price=product.price,
                    quantity=item.quantity,
                    line_total=line_total,
                )
            )
            order_lines_data.append(
                {
                    "name": product.name,
                    "quantity": item.quantity,
                    "line_total": line_total,
                }
            )

        order.total = total
        db.add(order)
        db.commit()
        db.refresh(order)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    order_lines = "\n".join(
        [
            f"• {item['name']} x{item['quantity']} - ${item['line_total']:.2f}"
            for item in order_lines_data
        ]
    )

    user_message = f"""
✅ <b>Order Received</b>

Hi {first_name}, your order has been received.

<b>Order ID:</b> #{order.id}

{order_lines}

<b>Total:</b> ${order.total:.2f}

Thank you for shopping with us!
"""

    admin_message = f"""
🛒 <b>New Order</b>

<b>Order ID:</b> #{order.id}
<b>Customer:</b> {first_name}
<b>Username:</b> {username_display}
<b>Telegram ID:</b> {user_chat_id}

{order_lines}

<b>Total:</b> ${order.total:.2f}
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
            "id": order.id,
            "total": order.total,
            "status": order.status,
        },
        "telegram_sent": telegram_sent,
        "telegram_error": telegram_error,
    }
