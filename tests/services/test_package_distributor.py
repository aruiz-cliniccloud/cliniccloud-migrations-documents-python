from pathlib import Path

import pytest

from app.services.package_distributor import (
    Package,
    PackageFile,
    distribute_files,
    package_folder_name,
)


def _rows(*paths: str) -> list[dict[str, str]]:
    return [{"idImport": str(i + 1), "Ruta": p} for i, p in enumerate(paths)]


class TestDistributeFiles:
    def test_all_files_fit_in_one_package(self, tmp_path):
        f = tmp_path / "a.pdf"
        f.write_bytes(b"x" * 100)
        rows = _rows(str(f))
        packages = distribute_files(rows, base_dir=None, max_size_bytes=1000)
        assert len(packages) == 1
        assert packages[0].file_count == 1

    def test_creates_new_package_when_limit_exceeded(self, tmp_path):
        # max=450: a(200)+b(200)=400 ≤ 450 → pkg1; c(200): 400+200=600 > 450 → pkg2
        for name in ("a.pdf", "b.pdf", "c.pdf"):
            (tmp_path / name).write_bytes(b"x" * 200)
        rows = _rows(str(tmp_path / "a.pdf"), str(tmp_path / "b.pdf"), str(tmp_path / "c.pdf"))
        packages = distribute_files(rows, base_dir=None, max_size_bytes=450)
        assert len(packages) == 2
        assert packages[0].file_count == 2  # a + b
        assert packages[1].file_count == 1  # c

    def test_three_packages_when_each_pair_exceeds_limit(self, tmp_path):
        for name in ("a.pdf", "b.pdf", "c.pdf"):
            (tmp_path / name).write_bytes(b"x" * 200)
        rows = _rows(str(tmp_path / "a.pdf"), str(tmp_path / "b.pdf"), str(tmp_path / "c.pdf"))
        packages = distribute_files(rows, base_dir=None, max_size_bytes=350)
        assert len(packages) == 3

    def test_single_file_larger_than_limit_goes_in_own_package(self, tmp_path):
        f = tmp_path / "big.pdf"
        f.write_bytes(b"x" * 1000)
        rows = _rows(str(f))
        packages = distribute_files(rows, base_dir=None, max_size_bytes=100)
        assert len(packages) == 1
        assert packages[0].file_count == 1

    def test_resolves_relative_paths_against_base_dir(self, tmp_path):
        f = tmp_path / "sub" / "file.pdf"
        f.parent.mkdir()
        f.write_bytes(b"x" * 50)
        rows = [{"idImport": "1", "Ruta": "sub/file.pdf"}]
        packages = distribute_files(rows, base_dir=tmp_path, max_size_bytes=10000)
        assert packages[0].files[0].source_path == f

    def test_absolute_path_ignores_base_dir(self, tmp_path):
        f = tmp_path / "file.pdf"
        f.write_bytes(b"x" * 50)
        rows = [{"idImport": "1", "Ruta": str(f)}]
        other_base = tmp_path / "other"
        packages = distribute_files(rows, base_dir=other_base, max_size_bytes=10000)
        assert packages[0].files[0].source_path == f

    def test_missing_file_contributes_zero_size(self, tmp_path):
        rows = [{"idImport": "1", "Ruta": str(tmp_path / "ghost.pdf")}]
        packages = distribute_files(rows, base_dir=None, max_size_bytes=100)
        assert len(packages) == 1
        assert packages[0].files[0].size_bytes == 0

    def test_skips_rows_with_empty_path(self):
        rows = [{"idImport": "1", "Ruta": ""}, {"idImport": "2", "Ruta": "/files/a.pdf"}]
        packages = distribute_files(rows, base_dir=None, max_size_bytes=10000)
        assert packages[0].file_count == 1

    def test_empty_rows_returns_empty_list(self):
        packages = distribute_files([], base_dir=None, max_size_bytes=10000)
        assert packages == []

    def test_package_numbers_are_sequential(self, tmp_path):
        for i in range(3):
            (tmp_path / f"f{i}.pdf").write_bytes(b"x" * 200)
        rows = _rows(*(str(tmp_path / f"f{i}.pdf") for i in range(3)))
        packages = distribute_files(rows, base_dir=None, max_size_bytes=350)
        assert [p.number for p in packages] == [1, 2, 3]

    def test_total_size_bytes_sums_files(self, tmp_path):
        (tmp_path / "a.pdf").write_bytes(b"x" * 100)
        (tmp_path / "b.pdf").write_bytes(b"x" * 150)
        rows = _rows(str(tmp_path / "a.pdf"), str(tmp_path / "b.pdf"))
        packages = distribute_files(rows, base_dir=None, max_size_bytes=10000)
        assert packages[0].total_size_bytes == 250


class TestPackageFolderName:
    def test_two_digit_padding_for_small_counts(self):
        assert package_folder_name("40826", 1, 9) == "paquete_40826_01"
        assert package_folder_name("40826", 9, 9) == "paquete_40826_09"

    def test_three_digit_padding_for_larger_counts(self):
        assert package_folder_name("40826", 1, 100) == "paquete_40826_001"
        assert package_folder_name("40826", 100, 100) == "paquete_40826_100"

    def test_always_at_least_two_digits(self):
        name = package_folder_name("123", 1, 1)
        assert name == "paquete_123_01"
