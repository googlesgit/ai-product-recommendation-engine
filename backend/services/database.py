"""MongoDB access layer — stores products and user interactions."""

from pymongo import MongoClient

from config import MONGO_DB, MONGO_URI

_client = None
_db = None


def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI)
        _db = _client[MONGO_DB]
    return _db


def products_collection():
    return get_db()["products"]


def interactions_collection():
    return get_db()["interactions"]


def users_collection():
    return get_db()["users"]
