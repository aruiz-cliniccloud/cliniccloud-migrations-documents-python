import logging
from pathlib import Path

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_file_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_path, encoding="utf-8", mode="a")
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
