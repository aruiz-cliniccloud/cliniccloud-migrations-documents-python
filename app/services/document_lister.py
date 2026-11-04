from pathlib import Path
from app.domain.document import Document
from app.domain.repositories import DocumentRepository


class DocumentLister:
    def __init__(self, repository: DocumentRepository) -> None:
        self._repository = repository

    def list_documents(self, directory: Path) -> list[Document]:
        return self._repository.find_all(directory)
