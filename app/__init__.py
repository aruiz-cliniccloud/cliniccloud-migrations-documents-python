import os
from pathlib import Path
from flask import Flask, session
from app.routes.home import home_bp
from app.routes.listing import listing_bp
from app.routes.language import language_bp
from app.routes.folder_picker import folder_picker_bp
from app.routes.health import health_bp
from app.routes.rename import rename_bp
from app.routes.packaging import packaging_bp
from app.services.translator import load_translator, DEFAULT_LANG
from app.infrastructure.operation_logger import configure_console_logging, configure_file_logging


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, static_folder=str(Path(__file__).parent.parent / "static"))
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")
    app.config["FLASK_ENV"] = os.getenv("FLASK_ENV", "development")
    app.config["INPUT_DIR"] = os.getenv("INPUT_DIR", "")
    app.config["OUTPUT_DIR"] = os.getenv("OUTPUT_DIR", "")
    app.config["LOG_DIR"] = os.getenv("LOG_DIR", "output")

    if config:
        app.config.update(config)

    if not app.config.get("TESTING"):
        log_path = Path(app.config["LOG_DIR"]) / "operations.txt"
        configure_file_logging(log_path)
        if app.config["FLASK_ENV"] == "development":
            configure_console_logging()

    app.register_blueprint(home_bp)
    app.register_blueprint(listing_bp)
    app.register_blueprint(language_bp)
    app.register_blueprint(folder_picker_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(rename_bp)
    app.register_blueprint(packaging_bp)

    @app.context_processor
    def inject_translator():
        lang = session.get("lang", DEFAULT_LANG)
        translator = load_translator(lang)
        return {"t": translator.translate, "lang": lang}

    return app
