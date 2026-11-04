import logging
from pathlib import Path

from app.infrastructure.operation_logger import configure_file_logging


class TestConfigureFileLogging:
    def test_creates_log_file_on_first_write(self, tmp_path):
        log_path = tmp_path / "logs" / "operations.txt"
        configure_file_logging(log_path)

        logging.getLogger("test.create").info("hello")
        _flush_handlers()

        assert log_path.exists()

    def test_log_file_contains_written_message(self, tmp_path):
        log_path = tmp_path / "ops.txt"
        configure_file_logging(log_path)

        logging.getLogger("test.msg").info("operation completed")
        _flush_handlers()

        assert "operation completed" in log_path.read_text(encoding="utf-8")

    def test_log_file_contains_level_label(self, tmp_path):
        log_path = tmp_path / "ops.txt"
        configure_file_logging(log_path)

        logging.getLogger("test.level").error("something failed")
        _flush_handlers()

        content = log_path.read_text(encoding="utf-8")
        assert "ERROR" in content

    def test_creates_parent_directories_if_missing(self, tmp_path):
        log_path = tmp_path / "deep" / "nested" / "operations.txt"
        configure_file_logging(log_path)

        logging.getLogger("test.dirs").info("ok")
        _flush_handlers()

        assert log_path.exists()

    def test_appends_to_existing_log(self, tmp_path):
        log_path = tmp_path / "ops.txt"
        log_path.write_text("existing line\n", encoding="utf-8")
        configure_file_logging(log_path)

        logging.getLogger("test.append").info("new line")
        _flush_handlers()

        content = log_path.read_text(encoding="utf-8")
        assert "existing line" in content
        assert "new line" in content


def _flush_handlers() -> None:
    for handler in logging.root.handlers:
        handler.flush()
