#!/usr/bin/env python3
"""
Standalone app blocker daemon.
Reads blocked apps from blocked_apps.json and kills matching processes.
"""

import signal

from src.app_blocker import AppBlocker
from src.constants import BLOCKED_APPS_PATH
from src.get_logger import get_logger


def main() -> None:
    running: bool = True

    def _shutdown(_sig, _frame) -> None:
        logger = get_logger()
        nonlocal running
        logger.info("Shutdown signal received")
        running = False
        logger.info("Daemon stopped")

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    last_mtime: float = 0
    app_blocker = AppBlocker()

    while running:
        if (mtime := BLOCKED_APPS_PATH.stat().st_mtime) > last_mtime:
            app_blocker.reload(on_init=False)
            last_mtime = mtime
        app_blocker.act()


if __name__ == "__main__":
    main()
