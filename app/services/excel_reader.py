import logging
from pathlib import Path

import openpyxl

logger = logging.getLogger(__name__)


class DuplicateColumnsError(ValueError):
    def __init__(self, duplicates: list[str]) -> None:
        self.duplicates = duplicates
        super().__init__(f"Duplicate column names: {', '.join(duplicates)}")


def _cell_to_str(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value)


def read_excel(file_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read an Excel file and return (column_headers, rows).

    Each row is a dict mapping header name to string cell value.
    Raises FileNotFoundError when the path does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    logger.info("Reading Excel file: %s", file_path)
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    ws = wb.active
    all_rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not all_rows:
        return [], []

    headers = [_cell_to_str(cell) for cell in all_rows[0]]

    seen: set[str] = set()
    duplicates: list[str] = []
    for h in headers:
        if h and h in seen and h not in duplicates:
            duplicates.append(h)
        seen.add(h)
    if duplicates:
        raise DuplicateColumnsError(duplicates)

    rows = [
        {headers[i]: _cell_to_str(cell) for i, cell in enumerate(row)}
        for row in all_rows[1:]
    ]
    logger.info("Read %d rows with %d columns from %s", len(rows), len(headers), file_path)
    return headers, rows
