from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock
from app.services.document_lister import DocumentLister
from app.domain.document import Document, DocumentName


def _make_doc(name: str, relative_path: str = "") -> Document:
    return Document(
        name=DocumentName(name),
        relative_path=relative_path or name,
        size_bytes=100,
        modified_at=datetime(2024, 1, 1),
    )


class TestDocumentLister:
    def test_returns_documents_from_repository(self):
        repo = MagicMock()
        repo.find_all.return_value = [_make_doc("a.pdf")]
        lister = DocumentLister(repo)

        result = lister.list_documents(Path("/some/dir"))

        assert len(result) == 1
        assert result[0].name.value == "a.pdf"

    def test_delegates_directory_to_repository(self):
        repo = MagicMock()
        repo.find_all.return_value = []
        lister = DocumentLister(repo)
        directory = Path("/my/docs")

        lister.list_documents(directory)

        repo.find_all.assert_called_once_with(directory)

    def test_returns_empty_list_when_directory_is_empty(self):
        repo = MagicMock()
        repo.find_all.return_value = []
        lister = DocumentLister(repo)

        result = lister.list_documents(Path("/empty"))

        assert result == []

    def test_propagates_repository_errors(self):
        import pytest
        repo = MagicMock()
        repo.find_all.side_effect = ValueError("does not exist")
        lister = DocumentLister(repo)

        with pytest.raises(ValueError):
            lister.list_documents(Path("/bad/path"))
