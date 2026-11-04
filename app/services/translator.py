import json
from pathlib import Path

TRANSLATIONS_DIR = Path(__file__).parent.parent / "translations"
SUPPORTED_LANGS = {"es", "en"}
DEFAULT_LANG = "es"


class JsonTranslator:
    def __init__(self, translations: dict[str, str]) -> None:
        self._translations = translations

    def translate(self, key: str) -> str:
        return self._translations.get(key, key)


def load_translator(lang: str) -> JsonTranslator:
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    path = TRANSLATIONS_DIR / f"{lang}.json"
    with path.open(encoding="utf-8") as f:
        return JsonTranslator(json.load(f))
