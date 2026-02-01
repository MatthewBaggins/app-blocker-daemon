import logging
from logging.handlers import RotatingFileHandler

from src.constants import LOGS_DIR_PATH, LOGS_FILE_PATH


def _get_logger() -> logging.Logger:
    """Get the logger."""
    # Create logs directory if it doesn't exist
    LOGS_DIR_PATH.mkdir(exist_ok=True)

    # Set up logging
    logger = logging.getLogger("AppBlocker")
    logger.setLevel(logging.DEBUG)

    # Rotating file handler (max 5MB per file, keep 5 backups)
    handler = RotatingFileHandler(
        LOGS_FILE_PATH,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
    )

    # Formatting: [<date> <time> - <level> - <message>]
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)

    return logger


logger = _get_logger()
