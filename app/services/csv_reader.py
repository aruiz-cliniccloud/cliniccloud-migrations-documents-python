import csv
from pathlib import Path


class MissingColumnsError(Exception):
    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__(f"Missing required columns: {', '.join(missing)}")


_REQUIRED_COLUMNS = {"idImport", "Ruta"}


def read_manifest_csv(path: Path) -> list[dict[str, str]]:
    """Read a packaging manifest CSV. Raises MissingColumnsError if required columns are absent."""
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = set(reader.fieldnames or [])
        missing = sorted(_REQUIRED_COLUMNS - headers)
        if missing:
            raise MissingColumnsError(missing)
        return [
            row
            for row in reader
            if row.get("idImport", "").strip() and row.get("Ruta", "").strip()
        ]
