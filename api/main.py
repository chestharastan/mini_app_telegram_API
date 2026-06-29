import hmac
import hashlib
import json
import os
from urllib.parse import parse_qsl, unquote
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from products import PRODUCTS, CATEGORIES
from dotenv import load_dotenv

load_dotenv()  
app = FastAPI()
FRONTEND_URL = os.getenv("FRONTEND_URL")

# Enable CORS so your frontend Web UI can talk to your FastAPI server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Load your bot token securely from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")


class AuthRequest(BaseModel):
    initData: str

def verify_telegram_data(init_data: str, bot_token: str) -> dict:
    """
    Validates Telegram Mini App initData according to Telegram's core specifications.
    Returns the parsed data dictionary if valid, otherwise raises ValueError.
    """
    try:
        # 1. Parse the query string into a dictionary
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
        if "hash" not in parsed_data:
            raise ValueError("Missing hash parameter")
            
        received_hash = parsed_data.pop("hash")
        
        # 2. Sort keys and format as key=value joined by newlines (\n)
        # Note: items must be unquoted as per Telegram specifications
        data_check_string = "\n".join(
            f"{k}={unquote(v)}" for k, v in sorted(parsed_data.items())
        )
        
        # 3. Compute HMAC-SHA256 signature
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        # 4. Compare the hashes securely
        if not hmac.compare_digest(computed_hash, received_hash):
            raise ValueError("Data integrity verification failed")
            
        # 5. Extract and parse the nested user JSON if present
        if "user" in parsed_data:
            parsed_data["user"] = json.loads(unquote(parsed_data["user"]))
            
        return parsed_data
    except Exception as e:
        raise ValueError(f"Invalid initData structure: {str(e)}")

@app.post("/api/auth")
async def authenticate_telegram_user(payload: AuthRequest):
    try:
        # Validate the telegram string
        validated_data = verify_telegram_data(payload.initData, BOT_TOKEN)
        
        # Pull the user object out
        user_info = validated_data.get("user", {})
        
        # SUCCESS! The data is genuine. 
        # Here you would typically look up the user in your DB or create a JWT session.
        return {
            "status": "authenticated",
            "user": {
                "id": user_info.get("id"),
                "username": user_info.get("username"),
                "first_name": user_info.get("first_name")
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@app.get("/api/products")
async def get_products():
    """Get all products"""
    return {"data": PRODUCTS}

@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    """Get a specific product by ID"""
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"data": product}

@app.get("/api/products/category/{category}")
async def get_products_by_category(category: str):
    """Get products filtered by category"""
    filtered = [p for p in PRODUCTS if p["category"] == category]
    return {"data": filtered}

@app.get("/api/categories")
async def get_categories():
    """Get all product categories"""
    return {"data": CATEGORIES}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)