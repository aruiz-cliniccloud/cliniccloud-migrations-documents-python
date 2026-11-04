class TestLanguageRoute:
    def test_set_language_to_en_redirects(self, client):
        response = client.get("/set-language?lang=en&next=/")
        assert response.status_code == 302

    def test_set_language_to_es_redirects(self, client):
        response = client.get("/set-language?lang=es&next=/")
        assert response.status_code == 302

    def test_set_language_stores_lang_in_session(self, client):
        client.get("/set-language?lang=en&next=/")
        with client.session_transaction() as sess:
            assert sess.get("lang") == "en"

    def test_set_language_redirects_to_next_param(self, client):
        response = client.get("/set-language?lang=en&next=/documents")
        assert "/documents" in response.headers["Location"]

    def test_invalid_language_defaults_to_es(self, client):
        client.get("/set-language?lang=fr&next=/")
        with client.session_transaction() as sess:
            assert sess.get("lang") == "es"

    def test_home_renders_in_spanish_by_default(self, client):
        response = client.get("/")
        assert "es" in response.data.decode()

    def test_home_renders_in_english_when_session_lang_is_en(self, client):
        with client.session_transaction() as sess:
            sess["lang"] = "en"
        response = client.get("/")
        assert b"Migration Document Manager" in response.data
