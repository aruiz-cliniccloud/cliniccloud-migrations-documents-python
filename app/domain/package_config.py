from dataclasses import dataclass


@dataclass(frozen=True)
class PackageConfig:
    company_id: str
    max_size_bytes: int

    def __post_init__(self) -> None:
        if not self.company_id:
            raise ValueError("company_id cannot be empty")
        if self.max_size_bytes <= 0:
            raise ValueError(f"max_size_bytes must be positive, got {self.max_size_bytes}")
