from fastapi import APIRouter, HTTPException, status

from app.core.config import BOT_TOKEN
from app.schemas.auth import AuthRequest
from app.services.telegram_auth import verify_telegram_data

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

        return {
            "status": "authenticated",
            "user": {
                "id": user_info.get("id"),
                "username": user_info.get("username"),
                "first_name": user_info.get("first_name"),
                "last_name": user_info.get("last_name"),
                "language_code": user_info.get("language_code"),
            },
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )