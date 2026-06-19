"""
logger.py
---------
Centralised logging configuration for the Data Quality Framework.

Usage in any module:
    from src.logger import get_logger
    log = get_logger(__name__)
    log.info("message")

Outputs:
  - Console (INFO and above)
  - logs/pipeline.log (DEBUG and above, rotating, max 5MB × 3 files)

Log format:
  2026-06-08 22:00:00,000 | INFO     | ingestion  | Loaded events: 199,930 rows
"""

import logging
import logging.handlers
from pathlib import Path

_LOG_DIR  = Path(__file__).parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "pipeline.log"
_FMT      = "%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure():
    global _configured
    if _configured:
        return

    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger("dqf")   # all framework loggers are children of "dqf"
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter(_FMT, datefmt=_DATE_FMT)

    # Console handler — INFO and above
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    # File handler — DEBUG and above, rotating
    file_handler = logging.handlers.RotatingFileHandler(
        _LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root.addHandler(console)
    root.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger namespaced under 'dqf'.
    Call once at module level: log = get_logger(__name__)
    """
    _configure()
    # Strip the package prefix so names are short in the log (e.g. "ingestion" not "src.ingestion")
    short_name = name.split(".")[-1]
    return logging.getLogger(f"dqf.{short_name}")
