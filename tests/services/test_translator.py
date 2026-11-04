from app.services.translator import JsonTranslator, load_translator


class TestJsonTranslator:
    def test_returns_translation_for_known_key(self):
        translator = JsonTranslator({"home.title": "Gestor"})
        assert translator.translate("home.title") == "Gestor"

    def test_returns_key_itself_when_key_not_found(self):
        translator = JsonTranslator({})
        assert translator.translate("missing.key") == "missing.key"

    def test_different_keys_return_different_values(self):
        translator = JsonTranslator({"a": "Alpha", "b": "Beta"})
        assert translator.translate("a") != translator.translate("b")


class TestLoadTranslator:
    def test_loads_spanish_translations(self):
        translator = load_translator("es")
        result = translator.translate("home.title")
        assert result != "home.title"

    def test_loads_english_translations(self):
        translator = load_translator("en")
        result = translator.translate("home.title")
        assert result != "home.title"

    def test_spanish_and_english_home_title_differ(self):
        es = load_translator("es").translate("home.title")
        en = load_translator("en").translate("home.title")
        assert es != en

    def test_unknown_language_falls_back_to_spanish(self):
        translator = load_translator("fr")
        es_translator = load_translator("es")
        assert translator.translate("home.title") == es_translator.translate("home.title")
