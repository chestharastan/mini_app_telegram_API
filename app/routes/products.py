from fastapi import APIRouter, HTTPException
from app.data.products import PRODUCTS, CATEGORIES

router = APIRouter()


@router.get("/products")
async def get_products():
    return {"data": PRODUCTS}


@router.get("/products/{product_id}")
async def get_product(product_id: str):
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"data": product}


@router.get("/products/category/{category}")
async def get_products_by_category(category: str):
    filtered = [p for p in PRODUCTS if p["category"] == category]
    return {"data": filtered}


@router.get("/categories")
async def get_categories():
    return {"data": CATEGORIES}