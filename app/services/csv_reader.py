import csv
from pathlib import Path


class MissingColumnsError(Exception):
    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__(f"Missing required columns: {', '.join(missing)}")


_REQUIRED_COLUMNS = {"idImport", "Ruta"}
# Tried in order; latin-1 accepts any byte so it always succeeds → keep it last
_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")


def _detect_encoding(path: Path) -> str:
    """Return the first encoding from _ENCODINGS that can decode the file without error."""
    for enc in _ENCODINGS:
        try:
            with path.open(encoding=enc) as f:
                f.read(8192)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"


def read_manifest_csv(path: Path) -> list[dict[str, str]]:
    """Read a packaging manifest CSV. Raises MissingColumnsError if required columns are absent.

    Handles common Excel CSV exports: semicolon delimiter, BOM, cp1252/latin-1 encoding,
    Windows line endings, and column names with extra whitespace.
    """
    encoding = _detect_encoding(path)
    with path.open(newline="", encoding=encoding) as f:
        sample = f.read(8192)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel  # fallback: comma + standard quoting

        reader = csv.DictReader(f, dialect=dialect)
        # Access fieldnames first so the header row is consumed, then strip whitespace
        raw_fieldnames = reader.fieldnames or []
        reader.fieldnames = [h.strip() for h in raw_fieldnames]

        headers = set(reader.fieldnames)
        missing = sorted(_REQUIRED_COLUMNS - headers)
        if missing:
            raise MissingColumnsError(missing)

        return [
            row
            for row in reader
            if row.get("idImport", "").strip() and row.get("Ruta", "").strip()
        ]
