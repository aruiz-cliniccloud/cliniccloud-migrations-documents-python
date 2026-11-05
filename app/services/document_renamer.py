import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from app.domain.rename_rule import RenameRule
from app.services.rename_rule_builder import build_new_name

logger = logging.getLogger(__name__)


@dataclass
class RenamePreview:
    original_path: Path
    new_name: str

    @property
    def new_path(self) -> Path:
        return self.original_path.parent / self.new_name

    @property
    def has_conflict(self) -> bool:
        return self.new_path.exists() and self.new_path != self.original_path

    @property
    def is_unchanged(self) -> bool:
        return self.original_path.name == self.new_name


def build_previews(
    rows: list[dict[str, str]],
    rule: RenameRule,
    base_dir: Path | None = None,
) -> list[RenamePreview]:
    previews = []
    for row in rows:
        path_str = row.get(rule.path_column, "")
        if not path_str:
            continue
        new_name = build_new_name(row, rule)
        path = Path(path_str)
        if base_dir is not None and not path.is_absolute():
            path = base_dir / path
        if path.name.startswith("_"):
            continue
        previews.append(RenamePreview(original_path=path, new_name=new_name))
    return previews


def copy_renames_to_folder(
    previews: list[RenamePreview],
    output_dir: Path,
) -> list[tuple[Path, Path, str | None]]:
    """Copy source files into output_dir using the new name from each preview.

    Original files are never moved or deleted.
    Returns list of (original_path, dest_path, error_message).
    """
    results = []
    for preview in previews:
        dest = output_dir / preview.new_name
        try:
            if not preview.original_path.exists():
                raise FileNotFoundError(f"File not found: {preview.original_path}")
            shutil.copy2(preview.original_path, dest)
            logger.info("Copied: %s → %s", preview.original_path.name, dest)
            results.append((preview.original_path, dest, None))
        except (FileNotFoundError, OSError) as exc:
            logger.error("Copy failed %s → %s: %s", preview.original_path, dest, exc)
            results.append((preview.original_path, dest, str(exc)))
    return results


def apply_renames(
    previews: list[RenamePreview],
) -> list[tuple[Path, Path, str | None]]:
    """Rename files on disk.

    Returns list of (original_path, new_path, error_message).
    error_message is None on success (including unchanged files).
    """
    results = []
    for preview in previews:
        if preview.is_unchanged:
            logger.info("Unchanged: %s", preview.original_path)
            results.append((preview.original_path, preview.new_path, None))
            continue
        try:
            if not preview.original_path.exists():
                raise FileNotFoundError(f"File not found: {preview.original_path}")
            if preview.has_conflict:
                raise FileExistsError(f"Target already exists: {preview.new_path}")
            preview.original_path.rename(preview.new_path)
            logger.info("Renamed: %s → %s", preview.original_path.name, preview.new_name)
            results.append((preview.original_path, preview.new_path, None))
        except (FileNotFoundError, FileExistsError, OSError) as exc:
            logger.error("Rename failed %s → %s: %s", preview.original_path, preview.new_name, exc)
            results.append((preview.original_path, preview.new_path, str(exc)))
    return results
