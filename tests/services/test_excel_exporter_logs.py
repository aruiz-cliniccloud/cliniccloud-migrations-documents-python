import logging
from pathlib import Path

from app.services.excel_exporter import generate_excel


class TestExcelExporterLogs:
    def test_logs_info_when_export_starts(self, caplog, tmp_path, sample_documents):
        with caplog.at_level(logging.INFO, logger="app.services.excel_exporter"):
            generate_excel(sample_documents, tmp_path)

        assert any(r.levelno == logging.INFO for r in caplog.records)

    def test_logs_document_count_on_export(self, caplog, tmp_path, sample_documents):
        with caplog.at_level(logging.INFO, logger="app.services.excel_exporter"):
            generate_excel(sample_documents, tmp_path)

        all_messages = " ".join(r.message for r in caplog.records)
        assert str(len(sample_documents)) in all_messages

    def test_logs_completion_with_size_info(self, caplog, tmp_path, sample_documents):
        with caplog.at_level(logging.INFO, logger="app.services.excel_exporter"):
            generate_excel(sample_documents, tmp_path)

        assert any("KB" in r.message or "bytes" in r.message.lower() for r in caplog.records)
