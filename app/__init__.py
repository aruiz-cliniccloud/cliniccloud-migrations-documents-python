from flask import Flask
from app.routes.home import home_bp


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev"

    if config:
        app.config.update(config)

    app.register_blueprint(home_bp)

    return app
