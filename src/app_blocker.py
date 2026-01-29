import json
import os
import time

from dotenv import load_dotenv
import psutil

from src.constants import BLOCKED_APPS_PATH, LOGS_DIR
from src.get_logger import get_logger
from src.utils import is_list_of_strings, load_default_blocked_apps


class AppBlocker:
    """Blocker of apps."""

    __slots__ = (
        "blocked_apps",
        "blocked_apps_check_interval",
        "blocked_apps_reset_interval",
        "checks_since_last_reset",
    )

    def __init__(self) -> None:
        load_dotenv()
        logger = get_logger()

        self.blocked_apps: set[str] = set()
        self.blocked_apps_check_interval: float = float(
            os.environ["BLOCKED_APPS_CHECK_INTERVAL"]
        )
        self.blocked_apps_reset_interval: float = float(
            os.environ["BLOCKED_APPS_RESET_INTERVAL"]
        )
        self.checks_since_last_reset: int = 0

        logger.info("App Blocker started")
        logger.info("Blocked apps file: %r", BLOCKED_APPS_PATH)
        logger.info("Logs: %r", LOGS_DIR / "daemon.log")

        self.reload(on_init=True)

    def reload(self, *, on_init: bool) -> None:
        """Reload the settings from `./blocked_apps.json`."""
        logger = get_logger()

        if not BLOCKED_APPS_PATH.exists():
            self._write_to_blocked_apps_file(
                [
                    app.lower()
                    for app in load_default_blocked_apps()
                    if not self._is_active_app(app.lower())
                ]
            )

        with open(BLOCKED_APPS_PATH, "r", encoding="utf-8") as f:
            blocked_apps_from_file = json.load(f)
            assert is_list_of_strings(blocked_apps_from_file)
            blocked_apps_from_file = {
                app.lower()
                for app in blocked_apps_from_file
                if not self._is_active_app(app.lower())
            }

        if not on_init:
            # Check for changes in blocked apps
            if blocked_apps_from_file != self.blocked_apps:
                logger.info(
                    "Added to blocked apps: %s",
                    blocked_apps_from_file - self.blocked_apps,
                )
                logger.info(
                    "Removed from blocked apps: %s",
                    self.blocked_apps - blocked_apps_from_file,
                )

        self.blocked_apps = blocked_apps_from_file

        logger.info(
            "Blocked apps %sloaded. Apps: %s",
            "" if on_init else "re",
            self.blocked_apps,
        )

    @property
    def n_checks_for_reset(self) -> int:
        return int(self.blocked_apps_reset_interval // self.blocked_apps_check_interval)

    def act(self) -> None:
        """Kill any processes matching blocked app names and (every reset interval)
        reset `blocked_apps.json`.
        """
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
                    logger.warning("Killing %r (PID %d)", proc_name, proc.pid)
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        time.sleep(self.blocked_apps_check_interval)
        self.checks_since_last_reset += 1
        if self.checks_since_last_reset >= self.n_checks_for_reset:
            self._write_inactive_default_blocked_apps_to_file()
            self.checks_since_last_reset = 0

    def _write_inactive_default_blocked_apps_to_file(self) -> None:
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
                if app.lower() in (
                    str(proc_name).lower().split("-") + str(exe_name).lower().split("-")
                ):
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
