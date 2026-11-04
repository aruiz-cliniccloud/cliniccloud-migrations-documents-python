class TestListingRoute:
    def test_listing_page_returns_200(self, client):
        response = client.get("/documents")
        assert response.status_code == 200

    def test_listing_page_contains_path_input(self, client):
        response = client.get("/documents")
        assert b'name="path"' in response.data

    def test_listing_with_nonexistent_path_shows_error(self, client):
        response = client.get("/documents?path=/nonexistent/xyz_abc_999")
        assert response.status_code == 200
        assert b"does not exist" in response.data.lower()

    def test_listing_with_valid_empty_directory_shows_empty_state(self, client, tmp_path):
        response = client.get(f"/documents?path={tmp_path}")
        assert response.status_code == 200
        assert b'data-testid="empty-state"' in response.data

    def test_listing_with_files_shows_document_names(self, client, tmp_path):
        (tmp_path / "migration_v1.sql").write_text("x")
        response = client.get(f"/documents?path={tmp_path}")
        assert b"migration_v1.sql" in response.data

    def test_listing_reads_files_in_subdirectories(self, client, tmp_path):
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "nested.pdf").write_text("x")
        response = client.get(f"/documents?path={tmp_path}")
        assert b"nested.pdf" in response.data

    def test_listing_shows_document_count(self, client, tmp_path):
        (tmp_path / "a.pdf").write_text("x")
        (tmp_path / "b.pdf").write_text("x")
        response = client.get(f"/documents?path={tmp_path}")
        assert b"2" in response.data
