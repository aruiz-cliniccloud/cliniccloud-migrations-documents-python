from app.domain.rename_rule import RenameRule
from app.services.rename_rule_builder import build_new_name


def test_build_new_name_joins_columns_with_separator():
    rule = RenameRule(path_column="path", name_columns=("id", "patient", "nombre"), separator="_")
    row = {
        "path": "/files/doc.pdf",
        "id": "25",
        "patient": "patien",
        "nombre": "nombre_archivo.pdf",
    }
    assert build_new_name(row, rule) == "25_patien_nombre_archivo.pdf"


def test_build_new_name_skips_empty_column_values():
    rule = RenameRule(path_column="path", name_columns=("id", "patient"), separator="_")
    row = {"path": "/files/doc.pdf", "id": "25", "patient": ""}
    assert build_new_name(row, rule) == "25.pdf"


def test_build_new_name_uses_original_extension_when_no_extension_in_parts():
    rule = RenameRule(path_column="path", name_columns=("id", "patient"), separator="_")
    row = {"path": "/files/original.pdf", "id": "25", "patient": "jones"}
    assert build_new_name(row, rule) == "25_jones.pdf"


def test_build_new_name_does_not_duplicate_extension():
    rule = RenameRule(path_column="path", name_columns=("nombre",), separator="_")
    row = {"path": "/files/original.pdf", "nombre": "doc.pdf"}
    assert build_new_name(row, rule) == "doc.pdf"


def test_build_new_name_uses_missing_column_as_empty_string():
    rule = RenameRule(path_column="path", name_columns=("id", "nonexistent"), separator="-")
    row = {"path": "/files/doc.pdf", "id": "10"}
    assert build_new_name(row, rule) == "10.pdf"


def test_build_new_name_with_no_extension_in_path_either():
    rule = RenameRule(path_column="path", name_columns=("id",), separator="_")
    row = {"path": "/files/document", "id": "5"}
    assert build_new_name(row, rule) == "5"


def test_build_new_name_with_custom_separator():
    rule = RenameRule(path_column="path", name_columns=("a", "b", "c"), separator="-")
    row = {"path": "/f/x.txt", "a": "foo", "b": "bar", "c": "baz.txt"}
    assert build_new_name(row, rule) == "foo-bar-baz.txt"


def test_build_new_name_with_empty_separator():
    rule = RenameRule(path_column="path", name_columns=("id", "patient"), separator="")
    row = {"path": "/files/doc.pdf", "id": "25", "patient": "jones"}
    assert build_new_name(row, rule) == "25jones.pdf"
