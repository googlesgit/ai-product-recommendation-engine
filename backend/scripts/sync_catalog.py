"""Sync product catalog from DummyJSON into MongoDB (upsert)."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.database import products_collection

DUMMYJSON_URL = "https://dummyjson.com/products?limit=100"


def _format_category(slug: str) -> tuple[str, str]:
    slug = (slug or "general").strip().lower()
    display = slug.replace("-", " ").title()
    return slug, display


def map_dummyjson_product(raw: dict) -> dict:
    slug, display = _format_category(raw.get("category", "general"))
    images = raw.get("images") or []
    thumb = raw.get("thumbnail") or (images[0] if images else "")
    brand = raw.get("brand") or ""
    stock = int(raw.get("stock") or 0)

    return {
        "source": "dummyjson",
        "source_id": str(raw["id"]),
        "name": raw.get("title", "Product"),
        "description": raw.get("description") or "",
        "price": float(raw.get("price") or 0),
        "rating": round(min(5.0, float(raw.get("rating") or 4.0)), 1),
        "review_count": max(stock * 8, 50),
        "category": display,
        "category_slug": slug,
        "image_url": thumb,
        "brand": brand,
        "tags": [t for t in [brand, slug] if t],
    }


def fetch_products(url: str = DUMMYJSON_URL) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "recommendation-engine/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode())
    return payload.get("products") or []


def sync_catalog(drop_legacy: bool = False) -> int:
    """
    Upsert products from DummyJSON.
    If drop_legacy=True, removes old products without source=dummyjson before sync.
    """
    col = products_collection()
    if drop_legacy:
        col.delete_many({"source": {"$ne": "dummyjson"}})

    raw_items = fetch_products()
    count = 0
    for raw in raw_items:
        doc = map_dummyjson_product(raw)
        col.update_one(
            {"source": "dummyjson", "source_id": doc["source_id"]},
            {"$set": doc},
            upsert=True,
        )
        count += 1

    # Remove dummyjson items no longer in feed
    valid_ids = {str(p["id"]) for p in raw_items}
    col.delete_many({
        "source": "dummyjson",
        "source_id": {"$nin": list(valid_ids)},
    })

    total = col.count_documents({})
    print(f"Synced {count} products from DummyJSON (catalog total: {total})")
    return count


if __name__ == "__main__":
    sync_catalog()
