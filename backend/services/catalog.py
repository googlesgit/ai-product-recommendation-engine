"""Catalog health checks and migration helpers."""

from services.database import products_collection


def catalog_needs_sync() -> bool:
    """True when DB is empty or still on legacy / partial DummyJSON sync."""
    col = products_collection()
    total = col.count_documents({})
    if total == 0:
        return True
    with_images = col.count_documents({"image_url": {"$exists": True, "$ne": ""}})
    dummyjson_count = col.count_documents({"source": "dummyjson"})
    if dummyjson_count < 150 or with_images < min(total, 80):
        return True
    return False
