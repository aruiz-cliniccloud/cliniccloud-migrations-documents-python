import io
from pathlib import Path

import openpyxl
import pytest


def _make_excel(directory: Path, headers: list, rows: list[list]) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    path = directory / "data.xlsx"
    wb.save(path)
    return path


def _make_excel_bytes(headers: list, rows: list[list]) -> io.BytesIO:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def _set_session(client, data: dict) -> None:
    with client.session_transaction() as sess:
        sess["rnm"] = data


class TestRenameIndex:
    def test_rename_page_returns_200(self, client):
        response = client.get("/rename")
        assert response.status_code == 200

    def test_rename_page_has_file_input(self, client):
        response = client.get("/rename")
        assert b'type="file"' in response.data

    def test_rename_page_has_company_id_input(self, client):
        response = client.get("/rename")
        assert b'name="company_id"' in response.data


class TestLoadColumns:
    def test_load_columns_redirects_to_configure_on_success(self, client):
        buf = _make_excel_bytes(["path", "id", "patient"], [])
        response = client.post(
            "/rename/columns",
            data={"excel_file": (buf, "data.xlsx"), "company_id": "123"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 302
        assert "configure" in response.headers["Location"]

    def test_load_columns_configure_shows_column_names(self, client):
        buf = _make_excel_bytes(["path", "id", "patient"], [])
        response = client.post(
            "/rename/columns",
            data={"excel_file": (buf, "data.xlsx"), "company_id": "123"},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"patient" in response.data
        assert b"path" in response.data

    def test_load_columns_shows_error_for_missing_file(self, client):
        response = client.post(
            "/rename/columns",
            data={"company_id": "123"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert b'type="file"' in response.data

    def test_load_columns_shows_error_for_missing_company_id(self, client):
        buf = _make_excel_bytes(["path", "id"], [])
        response = client.post(
            "/rename/columns",
            data={"excel_file": (buf, "data.xlsx"), "company_id": ""},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert b'type="file"' in response.data


class TestConfigure:
    def test_configure_get_redirects_to_index_without_session(self, client):
        response = client.get("/rename/configure")
        assert response.status_code == 302

    def test_configure_get_shows_columns_from_session(self, client):
        _set_session(client, {
            "excel_tmp_path": "/tmp/x.xlsx",
            "excel_filename": "data.xlsx",
            "company_id": "99",
            "columns": ["ruta", "id", "nombre"],
        })
        response = client.get("/rename/configure")
        assert response.status_code == 200
        assert b"nombre" in response.data


class TestPreview:
    def _setup(self, client, excel_path: Path, columns: list[str]) -> None:
        _set_session(client, {
            "excel_tmp_path": str(excel_path),
            "excel_filename": "data.xlsx",
            "company_id": "123",
            "columns": columns,
        })

    def test_preview_post_redirects_on_success(self, client, tmp_path):
        excel = _make_excel(tmp_path, ["ruta", "id"], [])
        self._setup(client, excel, ["ruta", "id"])
        response = client.post(
            "/rename/preview",
            data={"path_column": "ruta", "name_col": ["id"], "separator": "_"},
        )
        assert response.status_code == 302

    def test_preview_get_shows_original_and_new_names(self, client, tmp_path):
        (tmp_path / "doc.pdf").write_text("content")
        excel = _make_excel(
            tmp_path, ["ruta", "id", "patient"], [[str(tmp_path / "doc.pdf"), "1", "jones"]]
        )
        self._setup(client, excel, ["ruta", "id", "patient"])
        client.post(
            "/rename/preview",
            data={"path_column": "ruta", "name_col": ["id", "patient"], "separator": "_"},
        )
        response = client.get("/rename/preview")
        assert b"doc.pdf" in response.data
        assert b"1_jones.pdf" in response.data

    def test_preview_post_shows_error_when_no_name_cols(self, client, tmp_path):
        excel = _make_excel(tmp_path, ["ruta", "id"], [])
        self._setup(client, excel, ["ruta", "id"])
        response = client.post(
            "/rename/preview",
            data={"path_column": "ruta", "separator": "_"},
        )
        assert response.status_code == 200
        assert b"name_col" in response.data or b'type="file"' in response.data

    def test_preview_get_redirects_without_session(self, client):
        response = client.get("/rename/preview")
        assert response.status_code == 302


class TestApply:
    def _setup(self, client, excel_path: Path) -> None:
        _set_session(client, {
            "excel_tmp_path": str(excel_path),
            "excel_filename": "data.xlsx",
            "company_id": "123",
            "columns": ["ruta", "id", "patient"],
            "path_column": "ruta",
            "name_cols": ["id", "patient"],
            "separator": "_",
        })

    def test_apply_copies_files_to_output_folder(self, client, app, tmp_path):
        orig = tmp_path / "doc.pdf"
        orig.write_text("content")
        excel = _make_excel(
            tmp_path, ["ruta", "id", "patient"], [[str(orig), "1", "jones"]]
        )
        self._setup(client, excel)
        client.post("/rename/apply")
        output_dir = Path(app.config["OUTPUT_DIR"]) / "documentos123_renombrado"
        assert (output_dir / "1_jones.pdf").exists()

    def test_apply_does_not_remove_original(self, client, app, tmp_path):
        orig = tmp_path / "doc.pdf"
        orig.write_text("content")
        excel = _make_excel(tmp_path, ["ruta", "id", "patient"], [[str(orig), "1", "jones"]])
        self._setup(client, excel)
        client.post("/rename/apply")
        assert orig.exists()

    def test_apply_redirects_to_result(self, client, tmp_path):
        orig = tmp_path / "doc.pdf"
        orig.write_text("content")
        excel = _make_excel(tmp_path, ["ruta", "id", "patient"], [[str(orig), "1", "jones"]])
        self._setup(client, excel)
        response = client.post("/rename/apply")
        assert response.status_code == 302
        assert "result" in response.headers["Location"]

    def test_apply_result_page_shows_new_name(self, client, tmp_path):
        orig = tmp_path / "doc.pdf"
        orig.write_text("content")
        excel = _make_excel(tmp_path, ["ruta", "id", "patient"], [[str(orig), "1", "jones"]])
        self._setup(client, excel)
        client.post("/rename/apply")
        response = client.get("/rename/result")
        assert b"1_jones.pdf" in response.data

    def test_apply_creates_output_folder_named_with_company_id(self, client, app, tmp_path):
        orig = tmp_path / "file.pdf"
        orig.write_text("x")
        excel = _make_excel(tmp_path, ["ruta", "id", "patient"], [[str(orig), "5", "x"]])
        _set_session(client, {
            "excel_tmp_path": str(excel),
            "excel_filename": "data.xlsx",
            "company_id": "ACME",
            "columns": ["ruta", "id", "patient"],
            "path_column": "ruta",
            "name_cols": ["id"],
            "separator": "_",
        })
        client.post("/rename/apply")
        expected_folder = Path(app.config["OUTPUT_DIR"]) / "documentosACME_renombrado"
        assert expected_folder.exists()

    def test_result_get_redirects_without_session(self, client):
        response = client.get("/rename/result")
        assert response.status_code == 302
