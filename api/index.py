import hmac
import hashlib
import json
import os
from urllib.parse import parse_qsl, unquote

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from api.products import PRODUCTS, CATEGORIES

load_dotenv()

app = FastAPI()

FRONTEND_URL = os.getenv("FRONTEND_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL] if FRONTEND_URL else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuthRequest(BaseModel):
    initData: str


def verify_telegram_data(init_data: str, bot_token: str) -> dict:
    parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))

    if "hash" not in parsed_data:
        raise ValueError("Missing hash parameter")

    received_hash = parsed_data.pop("hash")

    data_check_string = "\n".join(
        f"{k}={unquote(v)}" for k, v in sorted(parsed_data.items())
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


@app.get("/")
def home():
    return {"message": "API is running"}


@app.post("/api/auth")
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
            },
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@app.get("/api/products")
async def get_products():
    return {"data": PRODUCTS}


@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"data": product}


@app.get("/api/products/category/{category}")
async def get_products_by_category(category: str):
    filtered = [p for p in PRODUCTS if p["category"] == category]
    return {"data": filtered}


@app.get("/api/categories")
async def get_categories():
    return {"data": CATEGORIES}