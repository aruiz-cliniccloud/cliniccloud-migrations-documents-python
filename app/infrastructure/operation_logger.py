import logging
import sys
from pathlib import Path

_FILE_FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
_CONSOLE_FORMAT = "%(asctime)s  %(levelname)-5s  %(name)s — %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_CONSOLE_DATE_FORMAT = "%H:%M:%S"


def configure_file_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_path, encoding="utf-8", mode="a")
    handler.setFormatter(logging.Formatter(_FILE_FORMAT, datefmt=_DATE_FORMAT))
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def configure_console_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT, datefmt=_CONSOLE_DATE_FORMAT))
    root = logging.getLogger()
    # Avoid adding a duplicate handler if already configured
    if not any(isinstance(h, logging.StreamHandler) and h.stream is sys.stdout
               for h in root.handlers):
        root.addHandler(handler)
    root.setLevel(logging.INFO)
    # Silence noisy third-party loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("openpyxl").setLevel(logging.WARNING)
