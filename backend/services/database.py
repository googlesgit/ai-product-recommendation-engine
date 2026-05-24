"""MongoDB access layer — stores products and user interactions."""

import certifi
from pymongo import MongoClient

from config import MONGO_DB, MONGO_URI

_client = None
_db = None


def _client_kwargs() -> dict:
    """Atlas on Render needs explicit CA bundle for TLS handshakes."""
    kwargs = {
        "serverSelectionTimeoutMS": 15000,
        "connectTimeoutMS": 15000,
    }
    if MONGO_URI.startswith("mongodb+srv://") or "mongodb.net" in MONGO_URI:
        kwargs["tlsCAFile"] = certifi.where()
    return kwargs


def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI, **_client_kwargs())
        _db = _client[MONGO_DB]
    return _db


def products_collection():
    return get_db()["products"]


def interactions_collection():
    return get_db()["interactions"]


def users_collection():
    return get_db()["users"]
