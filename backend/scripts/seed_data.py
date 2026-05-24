"""Demo users + sample likes (catalog comes from sync_catalog.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.database import interactions_collection, products_collection, users_collection

USERS = [
    {"user_id": "user_1", "name": "Alex (Tech lover)", "type": "demo"},
    {"user_id": "user_2", "name": "Jordan (Active lifestyle)", "type": "demo"},
    {"user_id": "user_3", "name": "Sam (Style & beauty)", "type": "demo"},
]

# Match DummyJSON category_slug values after sync
DEMO_LIKE_CATEGORIES = {
    "user_1": ["smartphones", "laptops", "mobile-accessories", "tablets"],
    "user_2": ["sports-accessories", "mens-shirts", "sunglasses", "mens-shoes"],
    "user_3": ["womens-dresses", "fragrances", "skincare", "jewellery"],
}


def _products_for_categories(slugs: list[str], per_category: int = 2) -> list[str]:
    ids: list[str] = []
    col = products_collection()
    for slug in slugs:
        cursor = col.find({"category_slug": slug}).limit(per_category)
        for doc in cursor:
            ids.append(str(doc["_id"]))
    return ids


def seed_demo_users():
    """Seed demo personas only — does not wipe products or session users."""
    interactions_collection().delete_many({"user_id": {"$in": [u["user_id"] for u in USERS]}})

    for user in USERS:
        users_collection().update_one(
            {"user_id": user["user_id"]},
            {"$set": user},
            upsert=True,
        )

    for user_id, slugs in DEMO_LIKE_CATEGORIES.items():
        product_ids = _products_for_categories(slugs)
        for pid in product_ids[:6]:
            interactions_collection().insert_one({
                "user_id": user_id,
                "product_id": pid,
                "type": "like",
            })

    print(f"Demo users seeded with likes from catalog ({products_collection().count_documents({})} products in DB)")


def seed():
    """Full reset: only for local dev when you want empty DB + manual seed list."""
    from services.database import get_db

    db = get_db()
    db.interactions.drop()
    db.users.drop()
    print("Dropped users and interactions. Run sync_catalog.py for products.")


if __name__ == "__main__":
    seed_demo_users()
