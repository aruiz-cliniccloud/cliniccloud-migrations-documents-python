from datetime import datetime
from pathlib import Path
from app.domain.document import Document, DocumentName


class FileSystemDocumentRepository:
    def find_all(self, directory: Path) -> list[Document]:
        if not directory.exists():
            raise ValueError(f"Path does not exist: {directory}")
        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        files = sorted(
            (p for p in directory.rglob("*") if p.is_file()),
            key=lambda p: str(p.relative_to(directory)),
        )
        return [self._to_document(path, directory) for path in files]

    def _to_document(self, path: Path, root: Path) -> Document:
        stat = path.stat()
        return Document(
            name=DocumentName(path.name),
            relative_path=str(path.relative_to(root)),
            size_bytes=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
        )
