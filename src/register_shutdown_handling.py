import signal
import typing as typ
import types

from src.get_logger import get_logger
from src.utils import Box


def register_shutdown_handling() -> Box[bool]:
    handler = _make_shutdown_handler(running_box := Box(True))
    signal.signal(signal.SIGINT, handler)  # pyright: ignore[reportArgumentType]
    signal.signal(signal.SIGTERM, handler)  # pyright: ignore[reportArgumentType]
    return running_box


def _make_shutdown_handler(
    running_box: Box,
) -> typ.Callable[[int, types.FrameType], None]:

    def handler(_sig: int, _frame: types.FrameType) -> None:
        logger = get_logger()
        logger.info("Shutdown signal received")
        running_box.value = False
        logger.info("Daemon stopped")

    return handler
