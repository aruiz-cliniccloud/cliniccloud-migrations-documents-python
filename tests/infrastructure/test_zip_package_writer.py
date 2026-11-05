import zipfile
from pathlib import Path

from app.infrastructure.zip_package_writer import zip_folder


class TestZipFolder:
    def test_creates_zip_next_to_folder(self, tmp_path):
        folder = tmp_path / "pkg"
        folder.mkdir()
        (folder / "file.txt").write_text("hello")
        zip_path = zip_folder(folder)
        assert zip_path == tmp_path / "pkg.zip"
        assert zip_path.exists()

    def test_zip_contains_all_files(self, tmp_path):
        folder = tmp_path / "pkg"
        folder.mkdir()
        (folder / "a.pdf").write_bytes(b"content_a")
        (folder / "b.pdf").write_bytes(b"content_b")
        zip_path = zip_folder(folder)
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        assert "a.pdf" in names
        assert "b.pdf" in names

    def test_zip_internal_paths_use_forward_slash(self, tmp_path):
        folder = tmp_path / "pkg"
        sub = folder / "sub"
        sub.mkdir(parents=True)
        (sub / "doc.pdf").write_bytes(b"x")
        zip_path = zip_folder(folder)
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        assert all("/" in n or not n.endswith(".pdf") for n in names)
        assert any("sub/doc.pdf" in n for n in names)

    def test_original_folder_is_preserved(self, tmp_path):
        folder = tmp_path / "pkg"
        folder.mkdir()
        (folder / "file.txt").write_text("x")
        zip_folder(folder)
        assert folder.exists()
        assert (folder / "file.txt").exists()

    def test_returns_zip_path(self, tmp_path):
        folder = tmp_path / "mypkg"
        folder.mkdir()
        (folder / "f.txt").write_text("x")
        result = zip_folder(folder)
        assert result.suffix == ".zip"
        assert result.stem == "mypkg"

    def test_zip_file_contents_match_originals(self, tmp_path):
        folder = tmp_path / "pkg"
        folder.mkdir()
        (folder / "data.txt").write_text("hello world")
        zip_path = zip_folder(folder)
        with zipfile.ZipFile(zip_path) as zf:
            assert zf.read("data.txt") == b"hello world"
