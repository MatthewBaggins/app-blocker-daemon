import signal

from src.logger import logger
from src.utils import Box


def register_shutdown_handling() -> Box[bool]:
    running_box = Box(True)

    def handler(_sig, _frame) -> None:
        logger.info("Shutdown signal received")
        running_box.value = False
        logger.info("Daemon stopped")

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    return running_box
