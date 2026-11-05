import pytest
from pathlib import Path

from app.domain.rename_rule import RenameRule
from app.services.document_renamer import RenamePreview, build_previews, apply_renames, copy_renames_to_folder


class TestRenamePreview:
    def test_new_path_is_sibling_of_original(self, tmp_path):
        orig = tmp_path / "old.pdf"
        orig.write_text("content")
        preview = RenamePreview(original_path=orig, new_name="new.pdf")
        assert preview.new_path == tmp_path / "new.pdf"

    def test_has_conflict_when_target_exists_and_differs(self, tmp_path):
        orig = tmp_path / "old.pdf"
        orig.write_text("content")
        (tmp_path / "new.pdf").write_text("other")
        preview = RenamePreview(original_path=orig, new_name="new.pdf")
        assert preview.has_conflict is True

    def test_has_no_conflict_when_target_is_self(self, tmp_path):
        orig = tmp_path / "old.pdf"
        orig.write_text("content")
        preview = RenamePreview(original_path=orig, new_name="old.pdf")
        assert preview.has_conflict is False

    def test_has_no_conflict_when_target_does_not_exist(self, tmp_path):
        orig = tmp_path / "old.pdf"
        orig.write_text("content")
        preview = RenamePreview(original_path=orig, new_name="new.pdf")
        assert preview.has_conflict is False

    def test_is_unchanged_when_name_matches_original(self):
        preview = RenamePreview(original_path=Path("/files/doc.pdf"), new_name="doc.pdf")
        assert preview.is_unchanged is True

    def test_is_not_unchanged_when_name_differs(self):
        preview = RenamePreview(original_path=Path("/files/old.pdf"), new_name="new.pdf")
        assert preview.is_unchanged is False


class TestBuildPreviews:
    def test_returns_one_preview_per_valid_row(self):
        rule = RenameRule(path_column="path", name_columns=("id",), separator="_")
        rows = [
            {"path": "/files/doc.pdf", "id": "1"},
            {"path": "/files/other.pdf", "id": "2"},
        ]
        previews = build_previews(rows, rule)
        assert len(previews) == 2

    def test_skips_rows_with_empty_path(self):
        rule = RenameRule(path_column="path", name_columns=("id",), separator="_")
        rows = [
            {"path": "", "id": "1"},
            {"path": "/files/doc.pdf", "id": "2"},
        ]
        previews = build_previews(rows, rule)
        assert len(previews) == 1
        assert previews[0].original_path == Path("/files/doc.pdf")

    def test_builds_new_name_from_rule(self):
        rule = RenameRule(path_column="path", name_columns=("id", "patient"), separator="_")
        rows = [{"path": "/files/doc.pdf", "id": "25", "patient": "jones"}]
        previews = build_previews(rows, rule)
        assert previews[0].new_name == "25_jones.pdf"

    def test_empty_rows_returns_empty_list(self):
        rule = RenameRule(path_column="path", name_columns=("id",), separator="_")
        assert build_previews([], rule) == []

    def test_resolves_relative_path_against_base_dir(self, tmp_path):
        base = tmp_path / "base"
        base.mkdir()
        rule = RenameRule(path_column="path", name_columns=("id",), separator="_")
        rows = [{"path": "subdir/doc.pdf", "id": "1"}]
        previews = build_previews(rows, rule, base_dir=base)
        assert previews[0].original_path == base / "subdir" / "doc.pdf"

    def test_absolute_path_ignores_base_dir(self, tmp_path):
        base = tmp_path / "base"
        base.mkdir()
        abs_path = tmp_path / "abs" / "doc.pdf"
        rule = RenameRule(path_column="path", name_columns=("id",), separator="_")
        rows = [{"path": str(abs_path), "id": "1"}]
        previews = build_previews(rows, rule, base_dir=base)
        assert previews[0].original_path == abs_path

    def test_without_base_dir_relative_path_stays_relative(self):
        rule = RenameRule(path_column="path", name_columns=("id",), separator="_")
        rows = [{"path": "relative/doc.pdf", "id": "1"}]
        previews = build_previews(rows, rule)
        assert previews[0].original_path == Path("relative/doc.pdf")

    def test_skips_rows_where_filename_starts_with_underscore(self):
        rule = RenameRule(path_column="path", name_columns=("id",), separator="_")
        rows = [
            {"path": "/files/_rename_log_20261105.txt", "id": "1"},
            {"path": "/files/doc.pdf", "id": "2"},
            {"path": "/files/_internal.csv", "id": "3"},
        ]
        previews = build_previews(rows, rule)
        assert len(previews) == 1
        assert previews[0].original_path == Path("/files/doc.pdf")

    def test_skips_underscore_filename_inside_subdirectory(self):
        rule = RenameRule(path_column="path", name_columns=("id",), separator="_")
        rows = [{"path": "subdir/_hidden.pdf", "id": "1"}]
        previews = build_previews(rows, rule)
        assert previews == []


class TestApplyRenames:
    def test_renames_file_on_disk(self, tmp_path):
        orig = tmp_path / "old.pdf"
        orig.write_text("content")
        preview = RenamePreview(original_path=orig, new_name="new.pdf")
        results = apply_renames([preview])
        assert results[0][2] is None
        assert (tmp_path / "new.pdf").exists()
        assert not orig.exists()

    def test_returns_error_for_missing_source_file(self, tmp_path):
        preview = RenamePreview(original_path=tmp_path / "ghost.pdf", new_name="new.pdf")
        results = apply_renames([preview])
        assert results[0][2] is not None

    def test_returns_error_for_conflict(self, tmp_path):
        orig = tmp_path / "old.pdf"
        orig.write_text("content")
        (tmp_path / "new.pdf").write_text("other")
        preview = RenamePreview(original_path=orig, new_name="new.pdf")
        results = apply_renames([preview])
        assert results[0][2] is not None

    def test_unchanged_rename_returns_no_error(self, tmp_path):
        orig = tmp_path / "doc.pdf"
        orig.write_text("content")
        preview = RenamePreview(original_path=orig, new_name="doc.pdf")
        results = apply_renames([preview])
        assert results[0][2] is None
        assert orig.exists()

    def test_returns_tuple_with_original_and_new_path(self, tmp_path):
        orig = tmp_path / "old.pdf"
        orig.write_text("content")
        preview = RenamePreview(original_path=orig, new_name="new.pdf")
        results = apply_renames([preview])
        old_path, new_path, error = results[0]
        assert old_path == orig
        assert new_path == tmp_path / "new.pdf"

    def test_processes_multiple_previews(self, tmp_path):
        for i in range(3):
            (tmp_path / f"file_{i}.pdf").write_text("x")
        previews = [
            RenamePreview(original_path=tmp_path / f"file_{i}.pdf", new_name=f"renamed_{i}.pdf")
            for i in range(3)
        ]
        results = apply_renames(previews)
        assert len(results) == 3
        assert all(r[2] is None for r in results)


class TestCopyRenamesToFolder:
    def test_copies_file_to_output_dir_with_new_name(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "out"
        out.mkdir()
        orig = src / "old.pdf"
        orig.write_text("content")
        preview = RenamePreview(original_path=orig, new_name="new.pdf")
        results = copy_renames_to_folder([preview], out)
        assert results[0][2] is None
        assert (out / "new.pdf").exists()
        assert orig.exists()  # original must stay

    def test_original_is_not_removed(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "out"
        out.mkdir()
        orig = src / "doc.pdf"
        orig.write_text("hello")
        preview = RenamePreview(original_path=orig, new_name="renamed.pdf")
        copy_renames_to_folder([preview], out)
        assert orig.exists()

    def test_returns_error_for_missing_source(self, tmp_path):
        out = tmp_path / "out"
        out.mkdir()
        preview = RenamePreview(original_path=tmp_path / "ghost.pdf", new_name="new.pdf")
        results = copy_renames_to_folder([preview], out)
        assert results[0][2] is not None

    def test_copies_multiple_files(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "out"
        out.mkdir()
        for i in range(3):
            (src / f"file_{i}.pdf").write_text("x")
        previews = [
            RenamePreview(original_path=src / f"file_{i}.pdf", new_name=f"renamed_{i}.pdf")
            for i in range(3)
        ]
        results = copy_renames_to_folder(previews, out)
        assert len(results) == 3
        assert all(r[2] is None for r in results)
        assert all((out / f"renamed_{i}.pdf").exists() for i in range(3))

    def test_copies_unchanged_file_to_output_dir(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "out"
        out.mkdir()
        orig = src / "doc.pdf"
        orig.write_text("content")
        preview = RenamePreview(original_path=orig, new_name="doc.pdf")
        results = copy_renames_to_folder([preview], out)
        assert results[0][2] is None
        assert (out / "doc.pdf").exists()

    def test_dest_path_uses_output_dir(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "out"
        out.mkdir()
        orig = src / "old.pdf"
        orig.write_text("x")
        preview = RenamePreview(original_path=orig, new_name="new.pdf")
        results = copy_renames_to_folder([preview], out)
        _, dest, _ = results[0]
        assert dest == out / "new.pdf"
