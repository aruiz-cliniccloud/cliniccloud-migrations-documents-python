import pytest
from pathlib import Path
from app.infrastructure.fs_document_repository import FileSystemDocumentRepository


@pytest.fixture()
def repo():
    return FileSystemDocumentRepository()


class TestFileSystemDocumentRepository:
    def test_returns_empty_list_for_empty_directory(self, repo, tmp_path):
        assert repo.find_all(tmp_path) == []

    def test_returns_files_in_flat_directory(self, repo, tmp_path):
        (tmp_path / "a.pdf").write_text("x")
        (tmp_path / "b.sql").write_text("x")
        docs = repo.find_all(tmp_path)
        assert len(docs) == 2

    def test_reads_files_recursively_from_subdirectories(self, repo, tmp_path):
        (tmp_path / "sub").mkdir()
        (tmp_path / "root.pdf").write_text("x")
        (tmp_path / "sub" / "nested.pdf").write_text("x")
        docs = repo.find_all(tmp_path)
        assert len(docs) == 2

    def test_excludes_directories_from_results(self, repo, tmp_path):
        (tmp_path / "subdir").mkdir()
        (tmp_path / "file.pdf").write_text("x")
        docs = repo.find_all(tmp_path)
        assert len(docs) == 1

    def test_document_relative_path_reflects_subdirectory(self, repo, tmp_path):
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "nested.pdf").write_text("x")
        docs = repo.find_all(tmp_path)
        assert docs[0].relative_path == str(Path("sub") / "nested.pdf")

    def test_document_name_matches_filename(self, repo, tmp_path):
        (tmp_path / "migration.sql").write_text("x")
        docs = repo.find_all(tmp_path)
        assert docs[0].name.value == "migration.sql"

    def test_document_size_bytes_matches_file_size(self, repo, tmp_path):
        (tmp_path / "file.txt").write_bytes(b"hello")
        docs = repo.find_all(tmp_path)
        assert docs[0].size_bytes == 5

    def test_results_are_sorted_by_relative_path(self, repo, tmp_path):
        (tmp_path / "b.pdf").write_text("x")
        (tmp_path / "a.pdf").write_text("x")
        docs = repo.find_all(tmp_path)
        assert docs[0].relative_path < docs[1].relative_path

    def test_raises_value_error_for_nonexistent_path(self, repo):
        with pytest.raises(ValueError, match="does not exist"):
            repo.find_all(Path("/nonexistent/path/xyz_abc_123"))

    def test_raises_value_error_when_path_is_a_file(self, repo, tmp_path):
        file_path = tmp_path / "file.txt"
        file_path.write_text("x")
        with pytest.raises(ValueError, match="not a directory"):
            repo.find_all(file_path)
