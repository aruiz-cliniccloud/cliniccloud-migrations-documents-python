import pytest

from app.domain.rename_rule import RenameRule


def test_rename_rule_stores_all_fields():
    rule = RenameRule(path_column="ruta", name_columns=("id", "patient"), separator="_")
    assert rule.path_column == "ruta"
    assert rule.name_columns == ("id", "patient")
    assert rule.separator == "_"


def test_rename_rule_empty_path_column_raises_value_error():
    with pytest.raises(ValueError, match="path_column"):
        RenameRule(path_column="", name_columns=("id",), separator="_")


def test_rename_rule_whitespace_path_column_raises_value_error():
    with pytest.raises(ValueError, match="path_column"):
        RenameRule(path_column="   ", name_columns=("id",), separator="_")


def test_rename_rule_empty_name_columns_raises_value_error():
    with pytest.raises(ValueError, match="name_columns"):
        RenameRule(path_column="ruta", name_columns=(), separator="_")


def test_rename_rule_blank_entry_in_name_columns_raises_value_error():
    with pytest.raises(ValueError, match="name_columns"):
        RenameRule(path_column="ruta", name_columns=("id", ""), separator="_")


def test_rename_rule_whitespace_entry_in_name_columns_raises_value_error():
    with pytest.raises(ValueError, match="name_columns"):
        RenameRule(path_column="ruta", name_columns=("id", "  "), separator="_")


def test_rename_rule_is_immutable():
    rule = RenameRule(path_column="ruta", name_columns=("id",), separator="_")
    with pytest.raises((AttributeError, TypeError)):
        rule.path_column = "other"  # type: ignore


def test_rename_rule_accepts_empty_separator():
    rule = RenameRule(path_column="ruta", name_columns=("id",), separator="")
    assert rule.separator == ""
