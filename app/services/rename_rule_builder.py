from pathlib import Path

from app.domain.rename_rule import RenameRule


def build_new_name(row: dict[str, str], rule: RenameRule) -> str:
    """Build a new filename from a row of Excel data using the given rule.

    Joins non-empty column values with the separator.
    If the result has no file extension, appends the extension from the path column value.
    """
    parts = [row.get(col, "") for col in rule.name_columns]
    non_empty = [p for p in parts if p]
    new_name = rule.separator.join(non_empty)

    if not Path(new_name).suffix:
        original = row.get(rule.path_column, "")
        ext = Path(original).suffix
        if ext:
            new_name += ext

    return new_name
