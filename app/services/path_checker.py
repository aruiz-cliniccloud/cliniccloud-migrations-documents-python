from pathlib import Path

from app.services.document_renamer import RenamePreview


def check_path_mapping(
    path_strings: list[str],
    base_dir: Path,
) -> list[dict]:
    """Resolve relative path strings against base_dir and check existence.

    Returns a list of dicts with keys: raw (str), resolved (str), exists (bool).
    """
    return [
        {
            "raw": path_str,
            "resolved": str(base_dir / path_str),
            "exists": (base_dir / path_str).exists(),
        }
        for path_str in path_strings
    ]


def check_paths_sample(
    previews: list[RenamePreview],
    n: int = 5,
) -> list[dict]:
    """Check whether source files exist for a sample of previews.

    Prefers files that will be renamed over unchanged ones.
    Returns a list of dicts with keys: path (str), name (str), exists (bool).
    """
    if not previews:
        return []

    candidates = [p for p in previews if not p.is_unchanged] or previews
    sample = candidates[:n]

    return [
        {
            "path": str(preview.original_path),
            "name": preview.original_path.name,
            "exists": preview.original_path.exists(),
        }
        for preview in sample
    ]
