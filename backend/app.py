"""Flask application entry point."""

import os

from flask import Flask
from flask_cors import CORS

from config import FLASK_DEBUG, FLASK_PORT
from routes.api import api_bp

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.register_blueprint(api_bp, url_prefix="/api")


def _ensure_seeded():
    """Load demo catalog when database is empty (local/docker first run)."""
    from services.database import products_collection

    if products_collection().count_documents({}) > 0:
        return
    from scripts.seed_data import seed

    seed()
    from routes.api import refresh_recommender

    refresh_recommender()


with app.app_context():
    try:
        _ensure_seeded()
    except Exception as exc:
        app.logger.warning("Auto-seed skipped: %s", exc)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=FLASK_DEBUG)
