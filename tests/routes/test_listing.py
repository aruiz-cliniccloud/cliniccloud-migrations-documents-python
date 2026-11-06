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

    def test_listing_shows_total_document_count(self, client, tmp_path):
        (tmp_path / "a.pdf").write_text("x")
        (tmp_path / "b.pdf").write_text("x")
        response = client.get(f"/documents?path={tmp_path}")
        assert b"2" in response.data

    def test_listing_shows_only_first_five_documents_by_default(self, client, tmp_path):
        for i in range(8):
            (tmp_path / f"file_{i:02d}.pdf").write_text("x")
        response = client.get(f"/documents?path={tmp_path}")
        assert b"file_00.pdf" in response.data
        assert b"file_04.pdf" in response.data
        assert b"file_05.pdf" not in response.data

    def test_listing_shows_all_documents_when_all_param_is_set(self, client, tmp_path):
        for i in range(8):
            (tmp_path / f"file_{i:02d}.pdf").write_text("x")
        response = client.get(f"/documents?path={tmp_path}&all=1")
        assert b"file_07.pdf" in response.data

    def test_listing_shows_show_all_link_when_results_are_limited(self, client, tmp_path):
        for i in range(8):
            (tmp_path / f"file_{i:02d}.pdf").write_text("x")
        response = client.get(f"/documents?path={tmp_path}")
        assert b"all=1" in response.data


class TestExportRoute:
    def test_export_redirects_to_listing_with_exported_param(self, client, tmp_path):
        (tmp_path / "migration.sql").write_text("x")
        response = client.get(f"/documents/export?path={tmp_path}")
        assert response.status_code in (302, 303)
        assert "exported=" in response.headers["Location"]

    def test_export_redirects_when_no_path_given(self, client):
        response = client.get("/documents/export")
        assert response.status_code in (302, 303)

    def test_export_redirects_when_path_does_not_exist(self, client):
        response = client.get("/documents/export?path=/nonexistent/xyz_abc")
        assert response.status_code in (302, 303)

    def test_export_saves_xlsx_file_to_output_directory(self, app, client, tmp_path):
        from pathlib import Path
        (tmp_path / "migration.sql").write_text("x")
        client.get(f"/documents/export?path={tmp_path}")

        output_dir = Path(app.config["OUTPUT_DIR"])
        xlsx_files = list(output_dir.glob("*.xlsx"))
        assert len(xlsx_files) == 1

    def test_export_saved_filename_ends_with_xlsx(self, app, client, tmp_path):
        from pathlib import Path
        (tmp_path / "migration.sql").write_text("x")
        client.get(f"/documents/export?path={tmp_path}")

        output_dir = Path(app.config["OUTPUT_DIR"])
        saved = list(output_dir.glob("*.xlsx"))[0]
        assert saved.suffix == ".xlsx"

    def test_export_saved_file_contains_document_data(self, app, client, tmp_path):
        from pathlib import Path
        from io import BytesIO
        import openpyxl

        (tmp_path / "migration.sql").write_text("x")
        client.get(f"/documents/export?path={tmp_path}")

        output_dir = Path(app.config["OUTPUT_DIR"])
        saved = list(output_dir.glob("*.xlsx"))[0]
        wb = openpyxl.load_workbook(BytesIO(saved.read_bytes()))
        ws = wb.active
        values = [ws.cell(r, 3).value for r in range(2, ws.max_row + 1)]
        assert "migration.sql" in values
