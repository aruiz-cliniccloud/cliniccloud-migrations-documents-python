import csv
from pathlib import Path

import pytest

from app.services.csv_reader import MissingColumnsError, read_manifest_csv


def _write_csv(path: Path, headers: list[str], rows: list[list]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


class TestReadManifestCsv:
    def test_reads_valid_csv(self, tmp_path):
        csv_path = tmp_path / "manifest.csv"
        _write_csv(csv_path, ["idImport", "Ruta"], [["1", "file1.pdf"], ["2", "file2.pdf"]])
        rows = read_manifest_csv(csv_path)
        assert len(rows) == 2
        assert rows[0]["idImport"] == "1"
        assert rows[0]["Ruta"] == "file1.pdf"

    def test_raises_missing_columns_error_when_idImport_absent(self, tmp_path):
        csv_path = tmp_path / "manifest.csv"
        _write_csv(csv_path, ["Ruta"], [["file.pdf"]])
        with pytest.raises(MissingColumnsError) as exc_info:
            read_manifest_csv(csv_path)
        assert "idImport" in exc_info.value.missing

    def test_raises_missing_columns_error_when_ruta_absent(self, tmp_path):
        csv_path = tmp_path / "manifest.csv"
        _write_csv(csv_path, ["idImport"], [["1"]])
        with pytest.raises(MissingColumnsError) as exc_info:
            read_manifest_csv(csv_path)
        assert "Ruta" in exc_info.value.missing

    def test_skips_rows_with_empty_id_import(self, tmp_path):
        csv_path = tmp_path / "manifest.csv"
        _write_csv(csv_path, ["idImport", "Ruta"], [["", "file.pdf"], ["1", "other.pdf"]])
        rows = read_manifest_csv(csv_path)
        assert len(rows) == 1
        assert rows[0]["idImport"] == "1"

    def test_skips_rows_with_empty_ruta(self, tmp_path):
        csv_path = tmp_path / "manifest.csv"
        _write_csv(csv_path, ["idImport", "Ruta"], [["1", ""], ["2", "file.pdf"]])
        rows = read_manifest_csv(csv_path)
        assert len(rows) == 1
        assert rows[0]["idImport"] == "2"

    def test_handles_bom_encoding(self, tmp_path):
        csv_path = tmp_path / "manifest.csv"
        with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["idImport", "Ruta"])
            writer.writerow(["1", "file.pdf"])
        rows = read_manifest_csv(csv_path)
        assert len(rows) == 1
        assert rows[0]["idImport"] == "1"

    def test_returns_empty_list_for_csv_with_only_headers(self, tmp_path):
        csv_path = tmp_path / "manifest.csv"
        _write_csv(csv_path, ["idImport", "Ruta"], [])
        rows = read_manifest_csv(csv_path)
        assert rows == []

    def test_extra_columns_are_allowed(self, tmp_path):
        csv_path = tmp_path / "manifest.csv"
        _write_csv(csv_path, ["idImport", "Ruta", "extra"], [["1", "file.pdf", "data"]])
        rows = read_manifest_csv(csv_path)
        assert len(rows) == 1
        assert rows[0]["extra"] == "data"
