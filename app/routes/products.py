from fastapi import APIRouter, HTTPException

from app.data.products import CATEGORIES
from app.db.supabase import get_supabase

router = APIRouter()


def get_supabase_or_500():
    try:
        return get_supabase()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def product_to_dict(product: dict):
    return {
        "id": product["id"],
        "brand": product.get("brand"),
        "name": product["name"],
        "description": product["description"],
        "price": product["price"],
        "category": product["category"],
        "imageUrl": product["image_url"],
        "stock": product["stock"],
    }


def category_to_dict(category: dict):
    return {
        "id": category["id"],
        "name": category["name"],
        "slug": category["slug"],
    }


def product_sort_key(product: dict):
    prefix, _, suffix = product["id"].rpartition("-")
    if suffix.isdigit():
        return (prefix, 0, int(suffix))

    return (product["id"], 1, 0)


CATEGORY_ORDER = {
    category["id"]: index
    for index, category in enumerate(CATEGORIES)
}


@router.get("/products")
async def get_products():
    supabase = get_supabase_or_500()

    try:
        response = supabase.table("products").select("*").execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase request failed: {e}") from e

    products = sorted(response.data or [], key=product_sort_key)
    return {"data": [product_to_dict(product) for product in products]}


@router.get("/products/{product_id}")
async def get_product(product_id: str):
    supabase = get_supabase_or_500()

    try:
        response = (
            supabase.table("products")
            .select("*")
            .eq("id", product_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase request failed: {e}") from e

    if not response.data:
        raise HTTPException(status_code=404, detail="Product not found")

    product = response.data[0]
    return {"data": product_to_dict(product)}


@router.get("/products/category/{category}")
async def get_products_by_category(category: str):
    supabase = get_supabase_or_500()

    try:
        query = supabase.table("products").select("*")
        if category != "all":
            query = query.eq("category", category)
        response = query.execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase request failed: {e}") from e

    products = sorted(response.data or [], key=product_sort_key)
    return {"data": [product_to_dict(product) for product in products]}


@router.get("/categories")
async def get_categories():
    supabase = get_supabase_or_500()

    try:
        response = supabase.table("categories").select("*").execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase request failed: {e}") from e

    categories = sorted(
        response.data or [],
        key=lambda category: CATEGORY_ORDER.get(category["id"], len(CATEGORY_ORDER)),
    )
    return {"data": [category_to_dict(category) for category in categories]}
