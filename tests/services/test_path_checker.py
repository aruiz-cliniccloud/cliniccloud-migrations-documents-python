from pathlib import Path

import pytest

from app.domain.rename_rule import RenameRule
from app.services.document_renamer import RenamePreview
from app.services.path_checker import check_path_mapping, check_paths_sample


def _preview(path: Path, new_name: str = "new.pdf") -> RenamePreview:
    return RenamePreview(original_path=path, new_name=new_name)


class TestCheckPathsSample:
    def test_empty_previews_returns_empty_list(self):
        assert check_paths_sample([]) == []

    def test_returns_up_to_n_items(self, tmp_path):
        previews = [_preview(tmp_path / f"f{i}.pdf") for i in range(10)]
        result = check_paths_sample(previews, n=5)
        assert len(result) == 5

    def test_returns_all_when_fewer_than_n(self, tmp_path):
        previews = [_preview(tmp_path / f"f{i}.pdf") for i in range(3)]
        result = check_paths_sample(previews, n=5)
        assert len(result) == 3

    def test_exists_true_when_file_on_disk(self, tmp_path):
        f = tmp_path / "real.pdf"
        f.write_text("x")
        result = check_paths_sample([_preview(f)])
        assert result[0]["exists"] is True

    def test_exists_false_when_file_missing(self, tmp_path):
        result = check_paths_sample([_preview(tmp_path / "ghost.pdf")])
        assert result[0]["exists"] is False

    def test_result_includes_path_and_name_keys(self, tmp_path):
        result = check_paths_sample([_preview(tmp_path / "file.pdf")])
        assert "path" in result[0]
        assert "name" in result[0]

    def test_name_is_filename_only(self, tmp_path):
        result = check_paths_sample([_preview(tmp_path / "sub" / "file.pdf")])
        assert result[0]["name"] == "file.pdf"

    def test_path_is_string(self, tmp_path):
        result = check_paths_sample([_preview(tmp_path / "file.pdf")])
        assert isinstance(result[0]["path"], str)

    def test_prefers_changed_files_over_unchanged(self, tmp_path):
        unchanged = _preview(tmp_path / "same.pdf", new_name="same.pdf")
        changed = _preview(tmp_path / "old.pdf", new_name="new.pdf")
        result = check_paths_sample([unchanged, changed], n=1)
        assert result[0]["name"] == "old.pdf"

    def test_falls_back_to_unchanged_when_no_changed(self, tmp_path):
        unchanged = _preview(tmp_path / "same.pdf", new_name="same.pdf")
        result = check_paths_sample([unchanged], n=5)
        assert len(result) == 1
        assert result[0]["name"] == "same.pdf"


class TestCheckPathMapping:
    def test_empty_list_returns_empty(self, tmp_path):
        assert check_path_mapping([], tmp_path) == []

    def test_exists_true_when_file_found(self, tmp_path):
        f = tmp_path / "sub" / "file.pdf"
        f.parent.mkdir()
        f.write_text("x")
        result = check_path_mapping(["sub/file.pdf"], tmp_path)
        assert result[0]["exists"] is True

    def test_exists_false_when_file_missing(self, tmp_path):
        result = check_path_mapping(["sub/ghost.pdf"], tmp_path)
        assert result[0]["exists"] is False

    def test_raw_path_preserved_in_result(self, tmp_path):
        result = check_path_mapping(["a/b.pdf"], tmp_path)
        assert result[0]["raw"] == "a/b.pdf"

    def test_resolved_path_joins_base_and_raw(self, tmp_path):
        result = check_path_mapping(["a/b.pdf"], tmp_path)
        assert result[0]["resolved"] == str(tmp_path / "a" / "b.pdf")

    def test_multiple_paths_mixed_existence(self, tmp_path):
        (tmp_path / "real.pdf").write_text("x")
        result = check_path_mapping(["real.pdf", "ghost.pdf"], tmp_path)
        assert result[0]["exists"] is True
        assert result[1]["exists"] is False
