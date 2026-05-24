"""Anonymous browser sessions — each visitor gets a persistent user_id."""

from datetime import datetime, timezone

from services.database import interactions_collection, users_collection

SESSION_PREFIX = "sess_"
DEMO_PREFIX = "user_"


def is_session_id(user_id: str) -> bool:
    return bool(user_id) and str(user_id).startswith(SESSION_PREFIX)


def ensure_session_user(session_id: str) -> dict:
    """Create a users document for new browser sessions."""
    session_id = str(session_id).strip()
    if not is_session_id(session_id):
        raise ValueError("Invalid session id")

    existing = users_collection().find_one({"user_id": session_id})
    if existing:
        return existing

    doc = {
        "user_id": session_id,
        "name": "You",
        "type": "session",
        "created_at": datetime.now(timezone.utc),
    }
    users_collection().insert_one(doc)
    return doc


def interaction_stats(user_id: str) -> dict:
    col = interactions_collection()
    likes = col.count_documents({"user_id": user_id, "type": "like"})
    views = col.count_documents({"user_id": user_id, "type": "view"})
    return {"likes": likes, "views": views}


def liked_product_ids(user_id: str) -> list[str]:
    rows = interactions_collection().find({"user_id": user_id, "type": "like"})
    return [str(r["product_id"]) for r in rows]


def resolve_user_id_from_request() -> str | None:
    """Prefer JSON body, then X-Session-Id header."""
    from flask import request

    data = request.get_json(silent=True) or {}
    uid = data.get("user_id") or request.headers.get("X-Session-Id")
    return str(uid).strip() if uid else None
