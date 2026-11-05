from dataclasses import dataclass


@dataclass(frozen=True)
class RenameRule:
    path_column: str
    name_columns: tuple[str, ...]
    separator: str

    def __post_init__(self) -> None:
        if not self.path_column.strip():
            raise ValueError("path_column cannot be empty")
        if not self.name_columns:
            raise ValueError("name_columns cannot be empty")
        if any(not col.strip() for col in self.name_columns):
            raise ValueError("name_columns cannot contain empty strings")
