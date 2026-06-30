from fastapi import APIRouter, HTTPException, status

from app.core.config import BOT_TOKEN
from app.schemas.auth import AuthRequest
from app.services.telegram_auth import verify_telegram_data
from app.services.telegram_contacts import get_telegram_contact, upsert_telegram_user

router = APIRouter()


@router.post("/auth")
async def authenticate_telegram_user(payload: AuthRequest):
    if not BOT_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="BOT_TOKEN is not configured"
        )

    try:
        validated_data = verify_telegram_data(payload.initData, BOT_TOKEN)
        user_info = validated_data.get("user", {})
        upsert_telegram_user(user_info)
        saved_phone = get_telegram_contact(user_info.get("id"))

        return {
            "status": "authenticated",
            "user": {
                "id": user_info.get("id"),
                "username": user_info.get("username"),
                "first_name": user_info.get("first_name"),
                "last_name": user_info.get("last_name"),
                "language_code": user_info.get("language_code"),
                "has_phone": bool(saved_phone),
            },
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
