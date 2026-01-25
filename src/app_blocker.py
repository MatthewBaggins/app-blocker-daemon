import json

import psutil

from src.constants import (
    BLOCKED_APPS_PATH,
    BLOCKED_APPS_CHECK_INTERVAL,
    BLOCKED_APPS_RESET_INTERVAL,
)
from src.get_logger import get_logger
from src.utils import is_list_of_strings, load_default_blocked_apps


class AppBlocker:
    """Blocker of apps."""

    __slots__ = (
        "blocked_apps",
        "blocked_apps_check_interval",
        "blocked_apps_reset_interval",
    )

    def __init__(self) -> None:
        self.blocked_apps: set[str] = set()
        self.blocked_apps_check_interval: float = BLOCKED_APPS_CHECK_INTERVAL
        self.blocked_apps_reset_interval: float = BLOCKED_APPS_RESET_INTERVAL
        self.reload(on_init=True)

    def reload(self, *, on_init: bool = False) -> None:
        """Reload the settings from `./blocked_apps.json`."""
        logger = get_logger()

        if not BLOCKED_APPS_PATH.exists():
            self._write_to_blocked_apps_file(load_default_blocked_apps())

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
                    logger.info("Added to blocked apps: %r", app)
                for app in removed:
                    logger.info("Removed from blocked apps: %r", app)

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

                if self._is_in_blocked_apps(
                    str(proc_name).lower()
                ) or self._is_in_blocked_apps(str(exe_name).lower()):
                    logger.warning("Killing %s (PID %d)", proc_name, proc.pid)
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    def write_inactive_blocked_apps_to_file(self) -> None:
        """Reset `blocked_app.json`, except for the apps that are currently active."""
        logger = get_logger()
        inactive_default_blocked_apps = [
            app for app in load_default_blocked_apps() if not self._is_active_app(app)
        ]
        new_blocked_apps: list[str] = sorted(
            self.blocked_apps.union(inactive_default_blocked_apps)
        )
        self._write_to_blocked_apps_file(new_blocked_apps)
        logger.info("Reset blocked_apps.json to: %s", new_blocked_apps)

    def _is_in_blocked_apps(self, name: str) -> bool:
        """Check if this name is in blocked apps."""
        return any(x in self.blocked_apps for x in [name, *name.split("-")])

    @staticmethod
    def _write_to_blocked_apps_file(blocked_apps: list[str]) -> None:
        with open(BLOCKED_APPS_PATH, "w", encoding="utf-8") as f:
            json.dump(blocked_apps, f, indent=4)

    @staticmethod
    def _is_active_app(app: str) -> bool:
        """Check if the app is currently active."""
        logger = get_logger()
        logger.info("Checking if app %r is active", app)

        for proc in psutil.process_iter(["name", "exe"]):
            try:
                proc_name = proc.info["name"]
                exe_name = proc.info["exe"].split("/")[-1] if proc.info["exe"] else ""

                if app.lower() in [str(proc_name).lower(), str(exe_name).lower()]:
                    logger.info(
                        "Found exact match: %r (proc_name=%r, exe_name=%r)",
                        app,
                        proc_name,
                        exe_name,
                    )
                    return True

                # Check if app is a substring (e.g., "signal" in "signal-desktop")
                if app.lower() in str(proc_name).lower().split(
                    "-"
                ) or app.lower() in str(exe_name).lower().split("-"):
                    logger.info(
                        "Found substring match: %r (proc_name=%r, exe_name=%r)",
                        app,
                        proc_name,
                        exe_name,
                    )
                    return True

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        logger.info("App %r is not active", app)
        return False
