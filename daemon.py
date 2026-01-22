#!/usr/bin/env python3
"""
Standalone app blocker daemon.
Reads blocked apps from config.json and kills matching processes.
"""

import copy
import functools
import json
import logging
from logging.handlers import RotatingFileHandler
import pathlib
import signal
import time
import typing as typ

import psutil


class Config(typ.TypedDict):
    blocked_apps: list[str]
    check_interval: float


def is_config(x: object) -> typ.TypeGuard[Config]:
    if not isinstance(x, dict):
        return False
    if set(x) != {"blocked_apps", "check_interval"}:
        return False
    if not isinstance(bas := x["blocked_apps"], list) and all(
        isinstance(ba, str) for ba in bas
    ):
        return False
    if not isinstance(x["check_interval"], float):
        return False
    return True


DEFAULT_CONFIG: Config = {
    "blocked_apps": ["discord", "slack", "steam", "brave", "firefox", "signal"],
    "check_interval": 0.5,
}


CONFIG_PATH = pathlib.Path(__file__).parent / "config.json"
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

    __slots__ = ("blocked_apps", "check_interval")
    blocked_apps: set[str]
    check_interval: float

    def __init__(self) -> None:
        self.blocked_apps = set()
        self.check_interval = DEFAULT_CONFIG["check_interval"]
        self.reload(on_init=True)

    def reload(self, *, on_init: bool = False) -> None:
        """Reload the settings from `./config.json`."""
        logger = get_logger()
        if not CONFIG_PATH.exists():
            config = copy.deepcopy(DEFAULT_CONFIG)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f)
        else:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                assert is_config(config)

        new_blocked_apps = {x.lower() for x in config["blocked_apps"]}
        new_check_interval = config["check_interval"]

        if not on_init:
            # Check for changes in blocked apps
            if new_blocked_apps != self.blocked_apps:
                added = new_blocked_apps - self.blocked_apps
                removed = self.blocked_apps - new_blocked_apps

                for app in added:
                    logger.info("Added to blocked apps: %s", f"{app!r}")
                for app in removed:
                    logger.info("Removed from blocked apps: %s", f"{app!r}")

            # Check for changes in check interval
            if new_check_interval != self.check_interval:
                logger.info(
                    "Check interval changed from %f to %f",
                    self.check_interval,
                    new_check_interval,
                )

        self.blocked_apps = new_blocked_apps
        self.check_interval = new_check_interval

        logger.info(
            "Config loaded. Apps: %s, Interval: %fs",
            self.blocked_apps,
            self.check_interval,
        )

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
    logger.info("Config: %s", CONFIG_PATH)
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
        # Reload config if changed
        try:
            mtime = CONFIG_PATH.stat().st_mtime
            if mtime > last_mtime:
                app_blocker.reload()
                last_mtime = mtime
        except FileNotFoundError:
            logger.error("Config file not found: %s", CONFIG_PATH)

        # Kill blocked apps
        app_blocker.kill_blocked_apps()

        time.sleep(app_blocker.check_interval)

    logger.info("Daemon stopped")


if __name__ == "__main__":
    main()
