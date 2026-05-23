import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "recommendations")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5001"))
