import functools
import logging
from logging.handlers import RotatingFileHandler

from src.constants import LOGS_DIR, LOGS_FILE


@functools.lru_cache(maxsize=1)
def get_logger() -> logging.Logger:
    """Get the logger."""
    # Create logs directory if it doesn't exist
    LOGS_DIR.mkdir(exist_ok=True)

    # Set up logging
    logger = logging.getLogger("AppBlocker")
    logger.setLevel(logging.DEBUG)

    # Rotating file handler (max 5MB per file, keep 5 backups)
    handler = RotatingFileHandler(
        LOGS_FILE,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
    )
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    return logger
