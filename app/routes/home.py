from flask import Blueprint, current_app, render_template

home_bp = Blueprint("home", __name__)


@home_bp.get("/")
def index():
    return render_template("home.html", input_dir=current_app.config.get("INPUT_DIR", ""))
