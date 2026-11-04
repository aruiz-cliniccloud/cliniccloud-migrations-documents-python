from io import BytesIO
from pathlib import Path

import openpyxl
import pytest

from app.services.excel_exporter import generate_excel


class TestGenerateExcel:
    def test_returns_bytes(self, tmp_path):
        result = generate_excel([], tmp_path)
        assert isinstance(result, bytes)

    def test_bytes_are_valid_xlsx(self, tmp_path):
        result = generate_excel([], tmp_path)
        wb = openpyxl.load_workbook(BytesIO(result))
        assert wb is not None

    def test_header_row_has_four_columns(self, tmp_path):
        result = generate_excel([], tmp_path)
        ws = openpyxl.load_workbook(BytesIO(result)).active
        headers = [ws.cell(1, c).value for c in range(1, 5)]
        assert headers == ["ruta", "ruta_relativa", "nombre_fichero", "extension"]

    def test_data_row_contains_full_path(self, tmp_path, sample_document):
        result = generate_excel([sample_document], tmp_path)
        ws = openpyxl.load_workbook(BytesIO(result)).active
        expected = str(tmp_path / sample_document.relative_path)
        assert ws.cell(2, 1).value == expected

    def test_data_row_contains_relative_path(self, tmp_path, sample_document):
        result = generate_excel([sample_document], tmp_path)
        ws = openpyxl.load_workbook(BytesIO(result)).active
        assert ws.cell(2, 2).value == sample_document.relative_path

    def test_data_row_contains_filename(self, tmp_path, sample_document):
        result = generate_excel([sample_document], tmp_path)
        ws = openpyxl.load_workbook(BytesIO(result)).active
        assert ws.cell(2, 3).value == sample_document.name.value

    def test_data_row_contains_extension(self, tmp_path, sample_document):
        result = generate_excel([sample_document], tmp_path)
        ws = openpyxl.load_workbook(BytesIO(result)).active
        assert ws.cell(2, 4).value == sample_document.extension

    def test_multiple_documents_produce_multiple_rows(self, tmp_path, sample_documents):
        result = generate_excel(sample_documents, tmp_path)
        ws = openpyxl.load_workbook(BytesIO(result)).active
        assert ws.max_row == 1 + len(sample_documents)


class TestRelativePathWithUploadedFilesAnchor:
    def test_path_outside_uploaded_files_uses_document_relative_path(self, tmp_path, sample_document):
        result = generate_excel([sample_document], tmp_path)
        ws = openpyxl.load_workbook(BytesIO(result)).active
        assert ws.cell(2, 2).value == sample_document.relative_path

    def test_path_inside_uploaded_files_starts_from_uploaded_files(self, tmp_path):
        from datetime import datetime
        from app.domain.document import Document, DocumentName

        uploaded_root = tmp_path / "cliniccloud-migrations-app" / "app" / "public" / "uploaded_files"
        uploaded_root.mkdir(parents=True)
        file_path = uploaded_root / "sub" / "migration.sql"
        file_path.parent.mkdir()
        file_path.write_text("x")

        doc = Document(
            name=DocumentName("migration.sql"),
            relative_path=str(
                (uploaded_root / "sub" / "migration.sql").relative_to(tmp_path)
            ),
            size_bytes=1,
            modified_at=datetime(2024, 1, 1),
        )

        result = generate_excel([doc], tmp_path)
        ws = openpyxl.load_workbook(BytesIO(result)).active
        expected = str(Path("uploaded_files") / "sub" / "migration.sql")
        assert ws.cell(2, 2).value == expected

    def test_root_is_uploaded_files_itself(self, tmp_path):
        from datetime import datetime
        from app.domain.document import Document, DocumentName

        uploaded_root = tmp_path / "uploaded_files"
        uploaded_root.mkdir()
        (uploaded_root / "migration.sql").write_text("x")

        doc = Document(
            name=DocumentName("migration.sql"),
            relative_path="migration.sql",
            size_bytes=1,
            modified_at=datetime(2024, 1, 1),
        )

        result = generate_excel([doc], uploaded_root)
        ws = openpyxl.load_workbook(BytesIO(result)).active
        expected = str(Path("uploaded_files") / "migration.sql")
        assert ws.cell(2, 2).value == expected
