class TestHomeRoute:
    def test_home_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_home_contains_list_documents_section(self, client):
        response = client.get("/")
        assert b"list" in response.data.lower()

    def test_home_contains_rename_documents_section(self, client):
        response = client.get("/")
        assert b"rename" in response.data.lower()

    def test_home_contains_package_documents_section(self, client):
        response = client.get("/")
        assert b"package" in response.data.lower()

    def test_home_links_to_listing_page(self, client):
        response = client.get("/")
        assert b'href="/documents"' in response.data

    def test_home_links_to_rename_page(self, client):
        response = client.get("/")
        assert b'href="/rename"' in response.data

    def test_home_links_to_package_page(self, client):
        response = client.get("/")
        assert b'href="/package"' in response.data
