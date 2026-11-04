from datetime import datetime
from app.domain.document import Document, DocumentName


class TestDocumentName:
    def test_valid_name_is_accepted(self):
        name = DocumentName("migration_v1.sql")
        assert name.value == "migration_v1.sql"

    def test_empty_name_raises_value_error(self):
        import pytest
        with pytest.raises(ValueError):
            DocumentName("")

    def test_name_with_forward_slash_raises_value_error(self):
        import pytest
        with pytest.raises(ValueError):
            DocumentName("folder/file.sql")

    def test_name_with_backslash_raises_value_error(self):
        import pytest
        with pytest.raises(ValueError):
            DocumentName("folder\\file.sql")

    def test_stem_returns_name_without_extension(self):
        assert DocumentName("migration_v1.sql").stem == "migration_v1"

    def test_suffix_returns_extension_with_dot(self):
        assert DocumentName("migration_v1.sql").suffix == ".sql"

    def test_suffix_is_lowercase(self):
        assert DocumentName("REPORT.PDF").suffix == ".pdf"


class TestDocument:
    def _make_document(self, name="report.pdf", relative_path="report.pdf",
                       size_bytes=1024, modified_at=None):
        return Document(
            name=DocumentName(name),
            relative_path=relative_path,
            size_bytes=size_bytes,
            modified_at=modified_at or datetime(2024, 1, 15, 10, 30),
        )

    def test_extension_matches_document_name_suffix(self):
        doc = self._make_document(name="schema.sql")
        assert doc.extension == ".sql"

    def test_size_kb_converts_bytes_correctly(self):
        doc = self._make_document(size_bytes=2048)
        assert doc.size_kb == 2.0

    def test_size_kb_rounds_to_one_decimal(self):
        doc = self._make_document(size_bytes=1500)
        assert doc.size_kb == 1.5

    def test_document_is_immutable(self):
        import pytest
        doc = self._make_document()
        with pytest.raises((AttributeError, TypeError)):
            doc.size_bytes = 999
