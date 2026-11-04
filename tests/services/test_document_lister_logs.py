import logging
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.domain.document import Document, DocumentName
from app.services.document_lister import DocumentLister


def _make_doc(name: str) -> Document:
    from datetime import datetime
    return Document(
        name=DocumentName(name),
        relative_path=name,
        size_bytes=100,
        modified_at=datetime(2024, 1, 1),
    )


class TestDocumentListerLogs:
    def test_logs_info_when_listing_starts(self, caplog):
        repo = MagicMock()
        repo.find_all.return_value = []
        lister = DocumentLister(repo)

        with caplog.at_level(logging.INFO, logger="app.services.document_lister"):
            lister.list_documents(Path("/my/docs"))

        assert any("/my/docs" in r.message for r in caplog.records)

    def test_logs_info_with_document_count_on_success(self, caplog):
        repo = MagicMock()
        repo.find_all.return_value = [_make_doc("a.pdf"), _make_doc("b.pdf")]
        lister = DocumentLister(repo)

        with caplog.at_level(logging.INFO, logger="app.services.document_lister"):
            lister.list_documents(Path("/my/docs"))

        assert any("2" in r.message for r in caplog.records)

    def test_logs_error_on_repository_failure(self, caplog):
        repo = MagicMock()
        repo.find_all.side_effect = ValueError("Path does not exist")
        lister = DocumentLister(repo)

        with caplog.at_level(logging.ERROR, logger="app.services.document_lister"):
            with pytest.raises(ValueError):
                lister.list_documents(Path("/bad/path"))

        assert any(r.levelno == logging.ERROR for r in caplog.records)
        assert any("does not exist" in r.message.lower() for r in caplog.records)
