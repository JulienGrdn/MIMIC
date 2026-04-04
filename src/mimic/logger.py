import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "mimic.log"

_MAX_BYTES = 5 * 1024 * 1024   # 5 MB per file
_BACKUP_COUNT = 3               # keep mimic.log, mimic.log.1, mimic.log.2

_FMT = "%(asctime)s  %(levelname)-8s  %(name)s — %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def configure_logging(level: int = logging.DEBUG) -> None:
    """Call once, at application startup (in app.main())."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(_FMT, datefmt=_DATE_FMT)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    rotating = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8"
    )
    rotating.setLevel(logging.DEBUG)
    rotating.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(console)
    root.addHandler(rotating)
