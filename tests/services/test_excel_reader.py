import pytest
import openpyxl
from pathlib import Path

from app.services.excel_reader import read_excel, DuplicateColumnsError


def _make_excel(tmp_path: Path, headers: list, rows: list[list]) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    if headers:
        ws.append(headers)
    for row in rows:
        ws.append(row)
    path = tmp_path / "test.xlsx"
    wb.save(path)
    return path


def test_read_excel_returns_headers_and_rows(tmp_path):
    path = _make_excel(tmp_path, ["name", "id"], [["doc.pdf", "1"], ["other.pdf", "2"]])
    headers, rows = read_excel(path)
    assert headers == ["name", "id"]
    assert len(rows) == 2
    assert rows[0] == {"name": "doc.pdf", "id": "1"}
    assert rows[1] == {"name": "other.pdf", "id": "2"}


def test_read_excel_empty_file_returns_empty(tmp_path):
    path = _make_excel(tmp_path, [], [])
    headers, rows = read_excel(path)
    assert headers == []
    assert rows == []


def test_read_excel_header_only_returns_no_rows(tmp_path):
    path = _make_excel(tmp_path, ["name", "id"], [])
    headers, rows = read_excel(path)
    assert headers == ["name", "id"]
    assert rows == []


def test_read_excel_raises_for_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_excel(tmp_path / "nonexistent.xlsx")


def test_read_excel_converts_int_cell_values_to_strings(tmp_path):
    path = _make_excel(tmp_path, ["id", "count"], [[42, 10]])
    _, rows = read_excel(path)
    assert rows[0]["id"] == "42"
    assert rows[0]["count"] == "10"


def test_read_excel_converts_float_cell_values_to_strings(tmp_path):
    path = _make_excel(tmp_path, ["value"], [[3.14]])
    _, rows = read_excel(path)
    assert rows[0]["value"] == "3.14"


def test_read_excel_converts_none_cells_to_empty_string(tmp_path):
    path = _make_excel(tmp_path, ["name", "id"], [[None, "1"]])
    _, rows = read_excel(path)
    assert rows[0]["name"] == ""
    assert rows[0]["id"] == "1"


def test_read_excel_header_none_cells_become_empty_string(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["col_a", None, "col_c"])
    ws.append(["v1", "v2", "v3"])
    path = tmp_path / "test.xlsx"
    wb.save(path)
    headers, rows = read_excel(path)
    assert headers == ["col_a", "", "col_c"]


def test_read_excel_raises_for_duplicate_column_names(tmp_path):
    path = _make_excel(tmp_path, ["id", "name", "id"], [["1", "doc.pdf", "2"]])
    with pytest.raises(DuplicateColumnsError) as exc_info:
        read_excel(path)
    assert "id" in exc_info.value.duplicates


def test_read_excel_raises_listing_all_duplicate_names(tmp_path):
    path = _make_excel(tmp_path, ["id", "name", "id", "name", "extra"], [])
    with pytest.raises(DuplicateColumnsError) as exc_info:
        read_excel(path)
    assert set(exc_info.value.duplicates) == {"id", "name"}


def test_read_excel_does_not_raise_for_duplicate_empty_headers(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["col_a", None, None, "col_b"])
    path = tmp_path / "test.xlsx"
    wb.save(path)
    headers, _ = read_excel(path)
    assert headers == ["col_a", "", "", "col_b"]


def test_duplicate_columns_error_is_value_error(tmp_path):
    path = _make_excel(tmp_path, ["col", "col"], [])
    with pytest.raises(ValueError):
        read_excel(path)
