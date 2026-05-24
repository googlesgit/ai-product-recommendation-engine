"""Flask REST API routes."""

import math
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, jsonify, request

from models.recommender import ProductRecommender
from services.database import get_db, interactions_collection, products_collection, users_collection
from services.search import search_products as rank_search_results
from services.search import suggest_queries
from services.session import (
    ensure_session_user,
    interaction_stats,
    is_session_id,
    liked_product_ids,
)

api_bp = Blueprint("api", __name__)

# In-memory recommender refreshed when products load
_recommender: ProductRecommender | None = None


def _serialize_product(doc: dict) -> dict:
    out = {k: v for k, v in doc.items() if k != "_id"}
    out["id"] = str(doc["_id"])
    return out


def _load_interactions() -> list[dict]:
    return list(interactions_collection().find({"type": "like"}))


def _get_recommender() -> ProductRecommender:
    global _recommender
    if _recommender is None:
        products = list(products_collection().find())
        _recommender = ProductRecommender(use_engineered_features=True)
        _recommender.fit(products)
        _recommender.fit_collaborative(_load_interactions())
    return _recommender


def refresh_recommender():
    global _recommender
    _recommender = None
    return _get_recommender()


@api_bp.route("/health")
def health():
    db_ok = False
    product_count = 0
    try:
        get_db().command("ping")
        db_ok = True
        product_count = products_collection().count_documents({})
    except Exception:
        pass
    return jsonify({
        "status": "ok" if db_ok else "degraded",
        "service": "recommendation-api",
        "database": "connected" if db_ok else "unavailable",
        "product_count": product_count,
    })


@api_bp.route("/seed", methods=["GET", "POST"])
def bootstrap_seed():
    """Load or upgrade catalog from DummyJSON."""
    from services.catalog import catalog_needs_sync

    existing = products_collection().count_documents({})
    force = request.args.get("force", "false").lower() in ("1", "true", "yes")

    if existing > 0 and not force and not catalog_needs_sync():
        return jsonify({
            "ok": True,
            "already_seeded": True,
            "product_count": existing,
            "message": "Catalog already loaded",
        })

    from scripts.seed_data import seed_demo_users
    from scripts.sync_catalog import sync_catalog

    upgraded = existing > 0
    sync_catalog(drop_legacy=upgraded or force)
    seed_demo_users()
    refresh_recommender()
    count = products_collection().count_documents({})
    return jsonify({
        "ok": True,
        "already_seeded": False,
        "upgraded": upgraded,
        "product_count": count,
        "message": f"Loaded {count} products from catalog API",
    }), 201


@api_bp.route("/catalog/sync", methods=["POST"])
def sync_catalog_endpoint():
    """Refresh product catalog from DummyJSON (upsert)."""
    from scripts.seed_data import seed_demo_users
    from scripts.sync_catalog import sync_catalog

    drop_legacy = request.args.get("drop_legacy", "false").lower() in ("1", "true", "yes")
    synced = sync_catalog(drop_legacy=drop_legacy)
    seed_demo_users()
    refresh_recommender()
    total = products_collection().count_documents({})
    return jsonify({
        "ok": True,
        "synced": synced,
        "product_count": total,
        "message": "Catalog synced; recommender refreshed",
    })


@api_bp.route("/products/categories")
def list_categories():
    items = []
    seen = set()
    for doc in products_collection().find({}, {"category": 1, "category_slug": 1}):
        slug = doc.get("category_slug") or doc.get("category", "").lower()
        display = doc.get("category") or slug
        if slug in seen:
            continue
        seen.add(slug)
        items.append({"slug": slug, "name": display})
    items.sort(key=lambda x: x["name"])
    return jsonify({"categories": items, "count": len(items)})


@api_bp.route("/products")
def list_products():
    sort = request.args.get("sort")
    category = (request.args.get("category") or "").strip()
    page = max(int(request.args.get("page", 1)), 1)
    limit = min(max(int(request.args.get("limit", 24)), 1), 48)

    query: dict = {}
    if category:
        query["category_slug"] = category.lower()

    total = products_collection().count_documents(query)
    cursor = products_collection().find(query)

    if sort == "rating":
        cursor = cursor.sort([("rating", -1), ("review_count", -1)])
    else:
        cursor = cursor.sort([("name", 1)])

    skip = (page - 1) * limit
    products = [_serialize_product(p) for p in cursor.skip(skip).limit(limit)]
    pages = max(1, math.ceil(total / limit)) if total else 1

    return jsonify({
        "products": products,
        "count": len(products),
        "total": total,
        "page": page,
        "pages": pages,
        "limit": limit,
        "category": category or None,
    })


@api_bp.route("/products/search")
def search_products():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"products": [], "query": q, "count": 0})

    docs = list(products_collection().find())
    ranked = rank_search_results(docs, q)
    results = []
    for doc in ranked:
        item = _serialize_product(doc)
        if "relevance_score" in doc:
            item["relevance_score"] = doc["relevance_score"]
        results.append(item)
    payload = {"products": results, "query": q, "count": len(results)}
    if len(results) == 0:
        payload["message"] = (
            "No products in our catalog match that search. "
            "Try a category like electronics or books, or browse the full catalog below."
        )
    return jsonify(payload)


@api_bp.route("/products/search/suggestions")
def search_suggestions():
    partial = (request.args.get("q") or "").strip()
    docs = list(products_collection().find())
    suggestions = suggest_queries(docs, partial)
    return jsonify({"suggestions": suggestions, "query": partial})


@api_bp.route("/products/<product_id>")
def get_product(product_id):
    from bson import ObjectId
    from bson.errors import InvalidId

    try:
        doc = products_collection().find_one({"_id": ObjectId(product_id)})
    except InvalidId:
        doc = None
    if not doc:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(_serialize_product(doc))


@api_bp.route("/similar/<product_id>")
def similar_products(product_id):
    k = int(request.args.get("k", 5))
    rec = _get_recommender()
    raw = rec.similar_products(product_id, k=k)
    items = []
    for p in raw:
        item = _serialize_product(p) if "_id" in p else p
        if "similarity_score" in p:
            item["similarity_score"] = p["similarity_score"]
        items.append(item)
    return jsonify({
        "product_id": product_id,
        "similar_products": items,
        "algorithm": "cosine_similarity",
    })


@api_bp.route("/session", methods=["GET", "POST"])
def session_info():
    """Register anonymous session and return activity summary."""
    session_id = request.headers.get("X-Session-Id") or request.args.get("session_id")
    if not session_id or not is_session_id(session_id):
        return jsonify({"error": "Valid X-Session-Id header required (sess_...)"}), 400
    ensure_session_user(session_id)
    stats = interaction_stats(session_id)
    return jsonify({
        "session_id": session_id,
        "name": "You",
        "type": "session",
        "stats": stats,
    })


@api_bp.route("/recommendations/user/<user_id>")
def user_recommendations(user_id):
    k = int(request.args.get("k", 8))
    # Profile is built from explicit likes — views power "Recently viewed" only
    liked_ids = liked_product_ids(user_id)

    rec = _get_recommender()
    raw = rec.recommend_for_user(liked_ids, k=k, exclude_ids=set(liked_ids))
    items = []
    for p in raw:
        item = _serialize_product(p) if "_id" in p else dict(p)
        if "id" not in item and "_id" in p:
            item["id"] = str(p["_id"])
        items.append(item)

    return jsonify({
        "user_id": user_id,
        "recommendations": items,
        "liked_count": len(liked_ids),
        "algorithm": "hybrid_content_collaborative",
    })


@api_bp.route("/interactions", methods=["POST"])
def record_interaction():
    data = request.get_json() or {}
    user_id = data.get("user_id") or request.headers.get("X-Session-Id")
    product_id = data.get("product_id")
    interaction_type = data.get("type", "like")

    if not user_id or not product_id:
        return jsonify({"error": "user_id and product_id required"}), 400

    user_id = str(user_id)
    product_id = str(product_id)
    allowed = {"like", "view", "click", "purchase"}
    if interaction_type not in allowed:
        return jsonify({"error": f"type must be one of {sorted(allowed)}"}), 400

    if is_session_id(user_id):
        ensure_session_user(user_id)

    col = interactions_collection()
    if interaction_type == "like":
        existing = col.find_one({
            "user_id": user_id,
            "product_id": product_id,
            "type": "like",
        })
        if existing:
            return jsonify({"ok": True, "message": "Already liked", "duplicate": True})

    col.insert_one({
        "user_id": user_id,
        "product_id": product_id,
        "type": interaction_type,
        "created_at": datetime.now(timezone.utc),
    })
    if interaction_type == "like":
        refresh_recommender()
    return jsonify({"ok": True, "message": "Interaction recorded", "type": interaction_type}), 201


@api_bp.route("/interactions/recent")
def recent_views():
    user_id = request.args.get("user_id") or request.headers.get("X-Session-Id")
    k = int(request.args.get("k", 6))
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    cursor = interactions_collection().find(
        {"user_id": str(user_id), "type": "view"},
    ).sort("created_at", -1).limit(k * 3)

    seen = set()
    products = []
    for row in cursor:
        pid = str(row["product_id"])
        if pid in seen:
            continue
        seen.add(pid)
        try:
            doc = products_collection().find_one({"_id": ObjectId(pid)})
        except InvalidId:
            doc = None
        if doc:
            products.append(_serialize_product(doc))
        if len(products) >= k:
            break

    return jsonify({"user_id": user_id, "products": products, "count": len(products)})


@api_bp.route("/users/demo")
def list_demo_users():
    users = list(users_collection().find({"type": "demo"}))
    if not users:
        users = list(users_collection().find({"user_id": {"$regex": "^user_"}}))
    return jsonify({
        "users": [
            {"id": u["user_id"], "name": u.get("name", u["user_id"]), "type": "demo"}
            for u in users
        ]
    })
