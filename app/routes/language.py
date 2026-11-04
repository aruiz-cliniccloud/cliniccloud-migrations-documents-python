from flask import Blueprint, redirect, request, session
from app.services.translator import SUPPORTED_LANGS, DEFAULT_LANG

language_bp = Blueprint("language", __name__)


@language_bp.get("/set-language")
def set_language():
    lang = request.args.get("lang", DEFAULT_LANG)
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    session["lang"] = lang
    next_url = request.args.get("next", "/")
    return redirect(next_url)
