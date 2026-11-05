import csv
import io
from pathlib import Path

import pytest


def _make_csv_bytes(headers: list[str], rows: list[list]) -> io.BytesIO:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    return io.BytesIO(buf.getvalue().encode("utf-8"))


def _set_session(client, data: dict) -> None:
    with client.session_transaction() as sess:
        sess["pkg"] = data


class TestPackageIndex:
    def test_returns_200(self, client):
        response = client.get("/package")
        assert response.status_code == 200

    def test_has_file_input(self, client):
        response = client.get("/package")
        assert b'type="file"' in response.data

    def test_has_company_id_input(self, client):
        response = client.get("/package")
        assert b'name="company_id"' in response.data

    def test_has_max_size_input(self, client):
        response = client.get("/package")
        assert b'name="max_size_mb"' in response.data


class TestPackageLoad:
    def test_redirects_to_map_on_valid_csv(self, client):
        buf = _make_csv_bytes(["idImport", "Ruta"], [["1", "file.pdf"]])
        response = client.post(
            "/package/load",
            data={"csv_file": (buf, "manifest.csv"), "company_id": "123", "max_size_mb": "480"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 302
        assert "map" in response.headers["Location"]

    def test_shows_error_when_no_file(self, client):
        response = client.post(
            "/package/load",
            data={"company_id": "123", "max_size_mb": "480"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200

    def test_shows_error_when_no_company_id(self, client):
        buf = _make_csv_bytes(["idImport", "Ruta"], [["1", "file.pdf"]])
        response = client.post(
            "/package/load",
            data={"csv_file": (buf, "manifest.csv"), "max_size_mb": "480"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200

    def test_shows_error_when_missing_columns(self, client):
        buf = _make_csv_bytes(["only_col"], [["value"]])
        response = client.post(
            "/package/load",
            data={"csv_file": (buf, "manifest.csv"), "company_id": "123", "max_size_mb": "480"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200


class TestPackageMap:
    def _session_data(self, tmp_path) -> dict:
        csv_path = tmp_path / "manifest.csv"
        with csv_path.open("w", newline="") as f:
            csv.writer(f).writerow(["idImport", "Ruta"])
        return {
            "csv_tmp_path": str(csv_path),
            "csv_filename": "manifest.csv",
            "company_id": "123",
            "max_size_mb": 480,
        }

    def test_map_get_returns_200(self, client, tmp_path):
        _set_session(client, self._session_data(tmp_path))
        response = client.get("/package/map")
        assert response.status_code == 200

    def test_map_get_redirects_to_index_without_session(self, client):
        response = client.get("/package/map")
        assert response.status_code == 302
        assert "/package" in response.headers["Location"]

    def test_map_post_redirects_back_to_map(self, client, tmp_path):
        _set_session(client, self._session_data(tmp_path))
        response = client.post("/package/map", data={"base_dir": str(tmp_path)})
        assert response.status_code == 302
        assert "map" in response.headers["Location"]


class TestPackagePreview:
    def _full_session(self, tmp_path) -> dict:
        csv_path = tmp_path / "manifest.csv"
        f = tmp_path / "file.pdf"
        f.write_bytes(b"x" * 100)
        with csv_path.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["idImport", "Ruta"])
            writer.writerow(["1", str(f)])
        return {
            "csv_tmp_path": str(csv_path),
            "csv_filename": "manifest.csv",
            "company_id": "123",
            "max_size_mb": 480,
            "base_dir": str(tmp_path),
        }

    def test_preview_returns_200(self, client, tmp_path):
        _set_session(client, self._full_session(tmp_path))
        response = client.get("/package/preview")
        assert response.status_code == 200

    def test_preview_redirects_to_index_without_session(self, client):
        response = client.get("/package/preview")
        assert response.status_code == 302


class TestPackageApply:
    def _full_session(self, tmp_path) -> dict:
        csv_path = tmp_path / "manifest.csv"
        f = tmp_path / "file.pdf"
        f.write_bytes(b"x" * 100)
        with csv_path.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["idImport", "Ruta"])
            writer.writerow(["1", str(f)])
        return {
            "csv_tmp_path": str(csv_path),
            "csv_filename": "manifest.csv",
            "company_id": "123",
            "max_size_mb": 480,
            "base_dir": str(tmp_path),
        }

    def test_apply_redirects_to_result(self, client, tmp_path):
        _set_session(client, self._full_session(tmp_path))
        response = client.post("/package/apply")
        assert response.status_code == 302
        assert "result" in response.headers["Location"]

    def test_apply_creates_package_folder(self, client, app, tmp_path):
        _set_session(client, self._full_session(tmp_path))
        client.post("/package/apply")
        output_base = Path(app.config["OUTPUT_DIR"]) / "paquetes_123"
        assert any(output_base.iterdir())

    def test_apply_creates_manifest_csv(self, client, app, tmp_path):
        _set_session(client, self._full_session(tmp_path))
        client.post("/package/apply")
        output_base = Path(app.config["OUTPUT_DIR"]) / "paquetes_123"
        assert (output_base / "manifest_123.csv").exists()

    def test_apply_creates_zip_file(self, client, app, tmp_path):
        _set_session(client, self._full_session(tmp_path))
        client.post("/package/apply")
        output_base = Path(app.config["OUTPUT_DIR"]) / "paquetes_123"
        zips = list(output_base.glob("*.zip"))
        assert len(zips) == 1


class TestPackageResult:
    def test_result_redirects_to_index_without_session(self, client):
        response = client.get("/package/result")
        assert response.status_code == 302

    def test_result_returns_200_with_session(self, client):
        _set_session(client, {
            "csv_tmp_path": "/tmp/x.csv",
            "csv_filename": "manifest.csv",
            "company_id": "123",
            "max_size_mb": 480,
            "result": {
                "packages_created": 1,
                "files_total": 5,
                "files_copied": 5,
                "files_error": 0,
                "output_dir": "/tmp/out",
                "manifest_path": "/tmp/out/manifest_123.csv",
                "package_names": ["paquete_123_01"],
                "errors": [],
            },
        })
        response = client.get("/package/result")
        assert response.status_code == 200
