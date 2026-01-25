import json

import psutil

from src.constants import BLOCKED_APPS_PATH, DEFAULT_BLOCKED_APPS
from src.get_logger import get_logger
from src.utils import is_list_of_strings


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
