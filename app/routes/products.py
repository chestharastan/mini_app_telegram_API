from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.data.products import CATEGORIES
from app.db.database import get_db
from app.db.models import Category, Product

router = APIRouter()


def product_to_dict(product: Product):
    return {
        "id": product.id,
        "brand": product.brand,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "category": product.category,
        "imageUrl": product.image_url,
        "stock": product.stock,
    }


def category_to_dict(category: Category):
    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
    }


def product_sort_key(product: Product):
    prefix, _, suffix = product.id.rpartition("-")
    if suffix.isdigit():
        return (prefix, 0, int(suffix))

    return (product.id, 1, 0)


CATEGORY_ORDER = {
    category["id"]: index
    for index, category in enumerate(CATEGORIES)
}


@router.get("/products")
async def get_products(db: Session = Depends(get_db)):
    products = sorted(db.query(Product).all(), key=product_sort_key)
    return {"data": [product_to_dict(product) for product in products]}


@router.get("/products/{product_id}")
async def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"data": product_to_dict(product)}


@router.get("/products/category/{category}")
async def get_products_by_category(category: str, db: Session = Depends(get_db)):
    query = db.query(Product)

    if category != "all":
        query = query.filter(Product.category == category)

    products = sorted(query.all(), key=product_sort_key)
    return {"data": [product_to_dict(product) for product in products]}


@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    categories = sorted(
        db.query(Category).all(),
        key=lambda category: CATEGORY_ORDER.get(category.id, len(CATEGORY_ORDER)),
    )
    return {"data": [category_to_dict(category) for category in categories]}
