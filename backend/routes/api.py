"""Flask REST API routes."""

from flask import Blueprint, jsonify, request

from models.recommender import ProductRecommender
from services.database import get_db, interactions_collection, products_collection, users_collection
from services.search import search_products as rank_search_results
from services.search import suggest_queries

api_bp = Blueprint("api", __name__)

# In-memory recommender refreshed when products load
_recommender: ProductRecommender | None = None


def _serialize_product(doc: dict) -> dict:
    out = {k: v for k, v in doc.items() if k != "_id"}
    out["id"] = str(doc["_id"])
    return out


def _get_recommender() -> ProductRecommender:
    global _recommender
    if _recommender is None:
        products = list(products_collection().find())
        _recommender = ProductRecommender(use_engineered_features=True)
        _recommender.fit(products)
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


@api_bp.route("/products")
def list_products():
    sort = request.args.get("sort")
    cursor = products_collection().find()
    products = [_serialize_product(p) for p in cursor]
    if sort == "rating":
        products.sort(key=lambda p: (p.get("rating", 0), p.get("review_count", 0)), reverse=True)
    return jsonify({"products": products, "count": len(products)})


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
    return jsonify({"products": results, "query": q, "count": len(results)})


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


@api_bp.route("/recommendations/user/<user_id>")
def user_recommendations(user_id):
    k = int(request.args.get("k", 8))
    interactions = interactions_collection().find(
        {"user_id": user_id, "type": {"$in": ["like", "purchase", "view"]}}
    )
    liked_ids = []
    for row in interactions:
        liked_ids.append(str(row["product_id"]))

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
        "algorithm": "knn_cosine_profile",
    })


@api_bp.route("/interactions", methods=["POST"])
def record_interaction():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    product_id = data.get("product_id")
    interaction_type = data.get("type", "like")

    if not user_id or not product_id:
        return jsonify({"error": "user_id and product_id required"}), 400

    interactions_collection().insert_one({
        "user_id": str(user_id),
        "product_id": str(product_id),
        "type": interaction_type,
    })
    refresh_recommender()
    return jsonify({"ok": True, "message": "Interaction recorded"}), 201


@api_bp.route("/users")
def list_users():
    users = list(users_collection().find())
    return jsonify({
        "users": [
            {"id": u["user_id"], "name": u.get("name", u["user_id"])}
            for u in users
        ]
    })
