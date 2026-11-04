import logging
from pathlib import Path

from app.domain.document import Document
from app.domain.repositories import DocumentRepository

logger = logging.getLogger(__name__)


class DocumentLister:
    def __init__(self, repository: DocumentRepository) -> None:
        self._repository = repository

    def list_documents(self, directory: Path) -> list[Document]:
        logger.info("Listing documents: %s", directory)
        try:
            documents = self._repository.find_all(directory)
        except ValueError as exc:
            logger.error("Failed to list documents in %s: %s", directory, exc)
            raise
        logger.info("Found %d documents in %s", len(documents), directory)
        return documents
