#!/usr/bin/env python3
"""
Standalone app blocker daemon.
Reads blocked apps from blocked_apps.json and kills matching processes.
"""

from src.app_blocker import AppBlocker
from src.constants import BLOCKED_APPS_PATH
from src.register_shutdown_handling import register_shutdown_handling
from src.utils import Box


def main() -> None:
    app_blocker = AppBlocker()
    running: Box[bool] = register_shutdown_handling()
    last_mtime: float = 0

    while running:
        # TODO: figure out whether this checking and stuff is actually necessary (and in what way/shape/form)
        if (mtime := BLOCKED_APPS_PATH.stat().st_mtime) > last_mtime:
            app_blocker.reload(on_init=False)
            last_mtime = mtime
        app_blocker.act()


if __name__ == "__main__":
    main()
