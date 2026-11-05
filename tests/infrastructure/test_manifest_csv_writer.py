import csv
from pathlib import Path

from app.infrastructure.manifest_csv_writer import write_package_manifest


class TestWritePackageManifest:
    def test_creates_csv_in_output_dir(self, tmp_path):
        rows = [{"idImport": "1", "paquete": "paquete_123_01"}]
        path = write_package_manifest(tmp_path, "123", rows)
        assert path == tmp_path / "manifest_123.csv"
        assert path.exists()

    def test_csv_has_correct_headers(self, tmp_path):
        write_package_manifest(tmp_path, "123", [])
        with (tmp_path / "manifest_123.csv").open(newline="") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == ["idImport", "paquete"]

    def test_csv_contains_all_rows(self, tmp_path):
        rows = [
            {"idImport": "1", "paquete": "paquete_123_01"},
            {"idImport": "2", "paquete": "paquete_123_01"},
            {"idImport": "3", "paquete": "paquete_123_02"},
        ]
        write_package_manifest(tmp_path, "123", rows)
        with (tmp_path / "manifest_123.csv").open(newline="") as f:
            written = list(csv.DictReader(f))
        assert len(written) == 3
        assert written[2]["paquete"] == "paquete_123_02"

    def test_creates_output_dir_if_missing(self, tmp_path):
        new_dir = tmp_path / "sub" / "output"
        write_package_manifest(new_dir, "456", [])
        assert new_dir.exists()

    def test_empty_rows_produces_header_only_csv(self, tmp_path):
        write_package_manifest(tmp_path, "789", [])
        with (tmp_path / "manifest_789.csv").open(newline="") as f:
            content = f.read()
        lines = [l for l in content.splitlines() if l]
        assert len(lines) == 1
        assert "idImport" in lines[0]
