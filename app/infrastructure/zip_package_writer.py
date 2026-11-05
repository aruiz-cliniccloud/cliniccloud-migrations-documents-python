import zipfile
from pathlib import Path


def zip_folder(folder: Path) -> Path:
    """Compress a folder into a ZIP archive placed next to it. Returns the zip path.

    Internal ZIP paths always use '/' as separator (ZIP standard), regardless of OS.
    The original folder is left untouched.
    """
    zip_path = folder.parent / f"{folder.name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(folder.rglob("*")):
            if file.is_file():
                # Use POSIX-style relative path as the archive name
                arc_name = file.relative_to(folder).as_posix()
                zf.write(file, arc_name)
    return zip_path
