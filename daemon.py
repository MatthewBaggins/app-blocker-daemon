#!/usr/bin/env python3
"""
Standalone app blocker daemon.
Reads blocked apps from blocked_apps.json and kills matching processes.
"""

import signal
import time

from src.app_blocker import AppBlocker
from src.constants import BLOCKED_APPS_PATH, LOGS_DIR
from src.get_logger import get_logger


def main() -> None:
    logger = get_logger()
    logger.info("App Blocker started")
    logger.info("Blocked apps file: %s", BLOCKED_APPS_PATH)
    logger.info("Logs: %s", LOGS_DIR / "daemon.log")

    # Handle graceful shutdown
    running: bool = True

    def _shutdown(_sig, _frame) -> None:
        nonlocal running
        logger.info("Shutdown signal received")
        running = False

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    last_mtime: float = 0
    app_blocker = AppBlocker()
    n_turns_for_reset: int = int(
        app_blocker.blocked_apps_reset_interval
        // app_blocker.blocked_apps_check_interval
    )
    n_turns: int = 0

    while running:
        mtime = BLOCKED_APPS_PATH.stat().st_mtime
        if mtime > last_mtime:
            app_blocker.reload()
            last_mtime = mtime

        # Kill blocked apps
        app_blocker.kill_blocked_apps()

        time.sleep(app_blocker.blocked_apps_check_interval)
        n_turns += 1
        if n_turns >= n_turns_for_reset:
            app_blocker.write_inactive_blocked_apps_to_file()
            n_turns = 0

    logger.info("Daemon stopped")


if __name__ == "__main__":
    main()
