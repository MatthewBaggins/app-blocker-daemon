#!/usr/bin/env python3
"""
Standalone app blocker daemon.
Reads blocked apps from config.json and kills matching processes.
"""

import functools
import json
import logging
from logging.handlers import RotatingFileHandler
import pathlib
import signal
import time
import typing as typ

import psutil


DEFAULT_BLOCKED_APPS: list[str] = [
    "discord",
    "slack",
    "steam",
    "brave",
    "firefox",
    "signal",
]


def is_list_of_strings(x: object) -> typ.TypeGuard[list[str]]:
    return isinstance(x, list) and all(isinstance(el, str) for el in x)


BLOCKED_APPS_PATH = pathlib.Path(__file__).parent / "blocked_apps.json"
LOGS_DIR = pathlib.Path(__file__).parent / "logs"


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
        LOGS_DIR / "daemon.log",
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


class AppBlocker:
    """Blocker of apps."""

    __slots__ = (
        "blocked_apps",
        "blocked_apps_check_interval",
        "blocked_apps_reset_interval",
    )
    blocked_apps: set[str]
    blocked_apps_check_interval: float
    blocked_apps_reset_interval: float

    def __init__(self) -> None:
        self.blocked_apps = set()
        self.blocked_apps_check_interval = 0.5  # 500 ms
        self.blocked_apps_reset_interval = 60.0  # 1 minute
        self.reload(on_init=True)

    def reload(self, *, on_init: bool = False) -> None:
        """Reload the settings from `./blocked_apps.json`."""
        logger = get_logger()

        # TODO: separate this into a separate method?
        if not BLOCKED_APPS_PATH.exists():
            with open(BLOCKED_APPS_PATH, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_BLOCKED_APPS, f)

        with open(BLOCKED_APPS_PATH, "r", encoding="utf-8") as f:
            new_blocked_apps = json.load(f)
            assert is_list_of_strings(new_blocked_apps)
            new_blocked_apps = {x.lower() for x in new_blocked_apps}

        if not on_init:
            # Check for changes in blocked apps
            if new_blocked_apps != self.blocked_apps:
                added = new_blocked_apps - self.blocked_apps
                removed = self.blocked_apps - new_blocked_apps

                for app in added:
                    logger.info("Added to blocked apps: %s", f"{app!r}")
                for app in removed:
                    logger.info("Removed from blocked apps: %s", f"{app!r}")

        self.blocked_apps = new_blocked_apps

        logger.info("Blocked apps loaded. Apps: %s", self.blocked_apps)

    def kill_blocked_apps(self) -> None:
        """Kill any processes matching blocked app names."""
        logger = get_logger()
        if not self.blocked_apps:
            return
        for proc in psutil.process_iter(["name", "exe"]):
            try:
                proc_name = proc.info["name"]
                exe_name = proc.info["exe"].split("/")[-1] if proc.info["exe"] else ""

                if self.is_in_blocked_apps(
                    str(proc_name).lower()
                ) or self.is_in_blocked_apps(str(exe_name).lower()):
                    logger.warning("Killing %s (PID %d)", proc_name, proc.pid)
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    def is_in_blocked_apps(self, name: str) -> bool:
        """Check if this name is in blocked apps."""
        return any(x in self.blocked_apps for x in [name, *name.split("-")])


def main() -> None:
    logger = get_logger()
    logger.info("App Blocker started")
    logger.info("Config: %s", BLOCKED_APPS_PATH)
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

    while running:
        # no need to wrap it in try-except because the case of file not exisitng is handled in reload
        # Reload config if changed
        # try:
        mtime = BLOCKED_APPS_PATH.stat().st_mtime
        if mtime > last_mtime:
            app_blocker.reload()
            last_mtime = mtime
        # except FileNotFoundError:
        #     logger.error("Blockd apps file not found: %s", BLOCKED_APPS_PATH)

        # Kill blocked apps
        app_blocker.kill_blocked_apps()

        time.sleep(app_blocker.blocked_apps_check_interval)

    logger.info("Daemon stopped")


if __name__ == "__main__":
    main()
