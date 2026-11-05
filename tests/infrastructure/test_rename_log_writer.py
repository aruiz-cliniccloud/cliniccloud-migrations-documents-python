from pathlib import Path

import pytest

from app.infrastructure.rename_log_writer import write_rename_log


def _rows(successes: int = 2, unchanged: int = 1, errors: int = 1) -> list[dict]:
    rows = []
    for i in range(successes):
        rows.append({"original_name": f"old_{i}.pdf", "new_name": f"new_{i}.pdf",
                     "is_unchanged": False, "error": None})
    for i in range(unchanged):
        rows.append({"original_name": f"same_{i}.pdf", "new_name": f"same_{i}.pdf",
                     "is_unchanged": True, "error": None})
    for i in range(errors):
        rows.append({"original_name": f"bad_{i}.pdf", "new_name": f"bad_{i}.pdf",
                     "is_unchanged": False, "error": "File not found: bad_0.pdf"})
    return rows


class TestWriteRenameLog:
    def test_creates_txt_file_in_output_dir(self, tmp_path):
        log_path = write_rename_log(tmp_path, "data.xlsx", "123", _rows())
        assert log_path.exists()
        assert log_path.suffix == ".txt"
        assert log_path.parent == tmp_path

    def test_filename_starts_with_rename_log(self, tmp_path):
        log_path = write_rename_log(tmp_path, "data.xlsx", "123", _rows())
        assert log_path.name.startswith("_rename_log_")

    def test_content_includes_company_id(self, tmp_path):
        log_path = write_rename_log(tmp_path, "data.xlsx", "ACME", _rows())
        content = log_path.read_text(encoding="utf-8")
        assert "ACME" in content

    def test_content_includes_excel_filename(self, tmp_path):
        log_path = write_rename_log(tmp_path, "migration.xlsx", "1", _rows())
        content = log_path.read_text(encoding="utf-8")
        assert "migration.xlsx" in content

    def test_content_includes_success_count(self, tmp_path):
        log_path = write_rename_log(tmp_path, "data.xlsx", "1", _rows(successes=3))
        content = log_path.read_text(encoding="utf-8")
        assert "3" in content

    def test_content_includes_error_count(self, tmp_path):
        log_path = write_rename_log(tmp_path, "data.xlsx", "1", _rows(errors=2))
        content = log_path.read_text(encoding="utf-8")
        assert "2" in content

    def test_content_lists_successful_rename(self, tmp_path):
        rows = [{"original_name": "orig.pdf", "new_name": "renamed.pdf",
                 "is_unchanged": False, "error": None}]
        log_path = write_rename_log(tmp_path, "data.xlsx", "1", rows)
        content = log_path.read_text(encoding="utf-8")
        assert "orig.pdf" in content
        assert "renamed.pdf" in content

    def test_content_lists_error_with_reason(self, tmp_path):
        rows = [{"original_name": "bad.pdf", "new_name": "new.pdf",
                 "is_unchanged": False, "error": "File not found: bad.pdf"}]
        log_path = write_rename_log(tmp_path, "data.xlsx", "1", rows)
        content = log_path.read_text(encoding="utf-8")
        assert "ERROR" in content
        assert "File not found: bad.pdf" in content

    def test_content_marks_unchanged_files(self, tmp_path):
        rows = [{"original_name": "same.pdf", "new_name": "same.pdf",
                 "is_unchanged": True, "error": None}]
        log_path = write_rename_log(tmp_path, "data.xlsx", "1", rows)
        content = log_path.read_text(encoding="utf-8")
        assert "same.pdf" in content

    def test_works_with_empty_rows(self, tmp_path):
        log_path = write_rename_log(tmp_path, "data.xlsx", "1", [])
        assert log_path.exists()
        content = log_path.read_text(encoding="utf-8")
        assert "Total:     0" in content
