#!/usr/bin/env python3
"""
Standalone app blocker daemon.
Reads blocked apps from blocked_apps.json and kills matching processes.
"""
import time


from src.app_blocker import AppBlocker
from src.constants import BLOCKED_APPS_PATH, DOTENV_PATH
from src.register_shutdown_handling import register_shutdown_handling
from src.utils import Box


def main() -> None:
    app_blocker = AppBlocker()
    running: Box[bool] = register_shutdown_handling()

    last_blocked_apps_modification_time: float = 0.0
    last_dotenv_modification_time: float = 0.0
    last_blocked_apps_reset_time: float = 0.0

    while running:
        if (
            mtime := BLOCKED_APPS_PATH.stat().st_mtime
        ) > last_blocked_apps_modification_time:
            app_blocker.check_blocked_apps_file_and_log_changes()
            last_blocked_apps_modification_time = mtime

        if (mtime := DOTENV_PATH.stat().st_mtime) > last_dotenv_modification_time:
            app_blocker.reload_dotenv()
            last_dotenv_modification_time = mtime

        if (
            (now := time.time()) - last_blocked_apps_reset_time
        ) >= app_blocker.reset_tick:
            app_blocker.reset_blocked_apps()
            last_blocked_apps_reset_time = now

        app_blocker.kill_blocked_apps()
        time.sleep(app_blocker.check_tick)


if __name__ == "__main__":
    main()
