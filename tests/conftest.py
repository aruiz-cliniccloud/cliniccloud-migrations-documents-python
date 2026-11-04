from datetime import datetime

import pytest

from app import create_app
from app.domain.document import Document, DocumentName


@pytest.fixture()
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "OUTPUT_DIR": str(tmp_path / "output"),
    })
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def sample_document():
    return Document(
        name=DocumentName("migration_v1.sql"),
        relative_path="subdir/migration_v1.sql",
        size_bytes=1024,
        modified_at=datetime(2024, 6, 15, 10, 30),
    )


@pytest.fixture()
def sample_documents():
    return [
        Document(
            name=DocumentName(f"file_{i:02d}.sql"),
            relative_path=f"file_{i:02d}.sql",
            size_bytes=512,
            modified_at=datetime(2024, 1, i + 1),
        )
        for i in range(3)
    ]
