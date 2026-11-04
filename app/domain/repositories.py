from pathlib import Path
from typing import Protocol
from app.domain.document import Document


class DocumentRepository(Protocol):
    def find_all(self, directory: Path) -> list[Document]: ...
