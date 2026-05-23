import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "recommendations")
# Render sets PORT; local Docker uses FLASK_PORT
FLASK_PORT = int(os.getenv("PORT", os.getenv("FLASK_PORT", "5001")))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")
