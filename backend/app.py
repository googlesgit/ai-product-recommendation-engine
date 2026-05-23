"""Flask application entry point."""

from flask import Flask
from flask_cors import CORS

from config import FLASK_PORT
from routes.api import api_bp

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.register_blueprint(api_bp, url_prefix="/api")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=True)
