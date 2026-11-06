import csv
from pathlib import Path


def write_package_manifest(
    output_dir: Path,
    company_id: str,
    rows: list[dict[str, str]],
) -> Path:
    """Write manifest_{company_id}.csv with idImport and Ruta columns."""
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"manifest_{company_id}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["idImport", "Ruta"], delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    return csv_path
