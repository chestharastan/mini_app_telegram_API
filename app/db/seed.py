from sqlalchemy.orm import Session

from app.data.products import CATEGORIES, PRODUCTS
from app.db.models import Category, Product


def seed_initial_data(db: Session):
    for category in CATEGORIES:
        existing_category = db.get(Category, category["id"])
        if existing_category:
            continue

        db.add(
            Category(
                id=category["id"],
                name=category["name"],
                slug=category["slug"],
            )
        )

    for product in PRODUCTS:
        existing_product = db.get(Product, product["id"])
        if existing_product:
            continue

        db.add(
            Product(
                id=product["id"],
                brand=product.get("brand"),
                name=product["name"],
                description=product["description"],
                price=float(product["price"]),
                category=product["category"],
                image_url=product["imageUrl"],
                stock=int(product["stock"]),
            )
        )

    db.commit()
