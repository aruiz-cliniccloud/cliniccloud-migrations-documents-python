from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PackageFile:
    id_import: str
    source_path: Path
    size_bytes: int


@dataclass
class Package:
    number: int
    files: list[PackageFile] = field(default_factory=list)

    @property
    def total_size_bytes(self) -> int:
        return sum(f.size_bytes for f in self.files)

    @property
    def file_count(self) -> int:
        return len(self.files)


def _get_file_size(path: Path) -> int:
    try:
        return path.stat().st_size if path.exists() else 0
    except OSError:
        return 0


def distribute_files(
    rows: list[dict[str, str]],
    base_dir: Path | None,
    max_size_bytes: int,
) -> list[Package]:
    """Distribute CSV rows into packages respecting max_size_bytes per package.

    A single file larger than max_size_bytes is placed alone in its own package.
    Files that do not exist on disk contribute 0 bytes to the size calculation.
    """
    packages: list[Package] = []
    current_files: list[PackageFile] = []
    current_size: int = 0
    pkg_num: int = 1

    for row in rows:
        path_str = row.get("Ruta", "").strip()
        id_import = row.get("idImport", "").strip()
        if not path_str or not id_import:
            continue

        source = Path(path_str)
        if base_dir is not None and not source.is_absolute():
            source = base_dir / source

        size = _get_file_size(source)

        if current_files and current_size + size > max_size_bytes:
            packages.append(Package(number=pkg_num, files=current_files))
            pkg_num += 1
            current_files = []
            current_size = 0

        current_files.append(PackageFile(id_import=id_import, source_path=source, size_bytes=size))
        current_size += size

    if current_files:
        packages.append(Package(number=pkg_num, files=current_files))

    return packages


def package_folder_name(company_id: str, number: int, total: int) -> str:
    """Return the folder name for a package, e.g. 'paquete_40826_01'."""
    digits = max(2, len(str(total)))
    return f"paquete_{company_id}_{number:0{digits}d}"
