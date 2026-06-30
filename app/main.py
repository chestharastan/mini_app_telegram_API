from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import FRONTEND_URL
from app.db.database import SessionLocal, init_db
from app.db.seed import seed_initial_data
from app.routes import products, auth, orders, webhook


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()

    yield


app = FastAPI(title="Telegram Ecomus API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL] if FRONTEND_URL else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix="/api", tags=["Products"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(orders.router, prefix="/api", tags=["Orders"])
app.include_router(webhook.router, prefix="/api", tags=["Telegram Webhook"])


@app.get("/")
def home():
    return {"message": "API is running"}
