from datetime import datetime, timezone
import re

from app.db.supabase import get_supabase


def normalize_phone_number(value):
    phone = re.sub(r"[^\d+]", "", str(value or "").strip())
    return re.sub(r"(?!^)\+", "", phone)


def current_timestamp():
    return datetime.now(timezone.utc).isoformat()


def upsert_telegram_user(user_info):
    telegram_id = user_info.get("id")
    if not telegram_id:
        return

    data = {
        "telegram_id": str(telegram_id),
        "username": user_info.get("username"),
        "first_name": user_info.get("first_name"),
        "updated_at": current_timestamp(),
    }

    get_supabase().table("users").upsert(
        data,
        on_conflict="telegram_id",
    ).execute()


def save_telegram_contact(user_id, phone_number, username=None, first_name=None):
    if not user_id or not phone_number:
        return

    data = {
        "telegram_id": str(user_id),
        "phone_number": normalize_phone_number(phone_number),
        "phone_verified_at": current_timestamp(),
        "updated_at": current_timestamp(),
    }

    if username:
        data["username"] = username

    if first_name:
        data["first_name"] = first_name

    get_supabase().table("users").upsert(
        data,
        on_conflict="telegram_id",
    ).execute()


def get_telegram_contact(user_id):
    if not user_id:
        return None

    response = (
        get_supabase()
        .table("users")
        .select("phone_number")
        .eq("telegram_id", str(user_id))
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0].get("phone_number")
