import os
from flask import Flask
from app.routes.home import home_bp
from app.routes.listing import listing_bp


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")
    app.config["FLASK_ENV"] = os.getenv("FLASK_ENV", "development")
    app.config["INPUT_DIR"] = os.getenv("INPUT_DIR", "")
    app.config["OUTPUT_DIR"] = os.getenv("OUTPUT_DIR", "")

    if config:
        app.config.update(config)

    app.register_blueprint(home_bp)
    app.register_blueprint(listing_bp)

    return app
