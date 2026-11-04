from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class DocumentName:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Document name cannot be empty.")
        if "/" in self.value or "\\" in self.value:
            raise ValueError(f"Document name must not contain path separators: {self.value!r}")

    @property
    def stem(self) -> str:
        return Path(self.value).stem

    @property
    def suffix(self) -> str:
        return Path(self.value).suffix.lower()


@dataclass(frozen=True)
class Document:
    name: DocumentName
    relative_path: str
    size_bytes: int
    modified_at: datetime

    @property
    def extension(self) -> str:
        return self.name.suffix

    @property
    def size_kb(self) -> float:
        return round(self.size_bytes / 1024, 1)
