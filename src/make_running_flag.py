import signal

from src.logger import logger
from src.utils import Box


def make_running_flag() -> Box[bool]:
    """
    Creates a running flag wrapped in a Box object and sets up signal handlers.

    The signal handlers listen for SIGINT and SIGTERM signals to update the
    running flag to False, indicating that the daemon should stop running.
    """
    running_flag = Box(True)

    def handler(_sig, _frame) -> None:
        logger.info("Shutdown signal received")
        running_flag.value = False
        logger.info("Daemon stopped")

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    return running_flag
