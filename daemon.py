#!/usr/bin/env python3
"""
Standalone app blocker daemon.
Reads blocked apps from blocked_apps.json and kills matching processes.
"""

from src.app_blocker import AppBlocker
from src.constants import BLOCKED_APPS_PATH, DOTENV_PATH
from src.register_shutdown_handling import register_shutdown_handling
from src.utils import Box


def main() -> None:
    app_blocker = AppBlocker()
    running: Box[bool] = register_shutdown_handling()
    last_blocked_apps_mtime: float = 0.0
    last_dotenv_mtime: float = 0.0

    while running:
        if (mtime := BLOCKED_APPS_PATH.stat().st_mtime) > last_blocked_apps_mtime:
            app_blocker.reload_blocked_apps(on_init=False)
            last_blocked_apps_mtime = mtime
        if (mtime := DOTENV_PATH.stat().st_mtime) > last_dotenv_mtime:
            app_blocker.reload_dotenv()
            last_dotenv_mtime = mtime
        app_blocker.act()


if __name__ == "__main__":
    main()
