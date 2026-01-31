import json
import os
import time

from dotenv import load_dotenv
import psutil

from src.constants import (
    BLOCKED_APPS_PATH,
    DEFAULT_BLOCKED_APPS_PATH,
    DEFAULT_CHECK_TICK,
    DEFAULT_RESET_TICK,
    LOGS_DIR,
)
from src.get_logger import get_logger
from src.utils import load_json_list_of_strings, format_float


class AppBlocker:
    """Blocker of apps."""

    __slots__ = (
        "blocked_apps",
        "check_tick",
        "reset_tick",
        "check_ticks_since_last_reset",
    )

    def __init__(self) -> None:
        load_dotenv()
        logger = get_logger()

        self.blocked_apps: set[str] = set()
        self.check_tick: float = _load_check_tick()
        self.reset_tick: float = _load_reset_tick()
        self.check_ticks_since_last_reset: int = 0

        logger.info("App Blocker started")
        logger.info("Blocked apps file: %r", BLOCKED_APPS_PATH)
        logger.info("Logs: %r", LOGS_DIR / "daemon.log")

        self.reload_blocked_apps(on_init=True)

    def reload_blocked_apps(self, *, on_init: bool) -> None:
        """Reload the settings from `./blocked_apps.json`.

        Considers three branches. (1) The file doesn't exist. (2) The file exists and is wellf-formatted.
        (3) The file exists but is malformatted.
        """
        logger = get_logger()
        default_blocked_apps: list[str] = _load_default_blocked_apps()

        # Branch 1: The file doesn't exist
        if not BLOCKED_APPS_PATH.exists():
            self._write_to_blocked_apps_file(
                default_blocked_apps,
            )
            blocked_apps_from_file: set[str] = _load_inactive_blocked_apps_as_set()
        else:
            # Branch 2: The file exists and is wellf-formatted.
            try:
                blocked_apps_from_file: set[str] = _load_inactive_blocked_apps_as_set()
            # Branch 3: The file exists but is malformatted.
            except (json.JSONDecodeError, AssertionError) as e:
                logger.error("Error reading blocked_apps.json: %s", e)
                logger.info("Resetting blocked_apps.json to default settings.")
                self._write_to_blocked_apps_file(default_blocked_apps)
                blocked_apps_from_file: set[str] = _load_inactive_blocked_apps_as_set()

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

    def reload_dotenv(self) -> None:
        """Reload the changes in the `.env` file."""
        if not load_dotenv(override=True):
            return
        logger = get_logger()

        if self.check_tick != (new_check_tick := _load_check_tick()):
            logger.info(
                "check_tick changed from %s to %s",
                format_float(self.check_tick),
                format_float(new_check_tick),
            )
            self.check_tick = new_check_tick

        if self.reset_tick != (new_reset_tick := _load_reset_tick()):
            logger.info(
                "reset_tick changed from %s to %s",
                format_float(self.reset_tick),
                format_float(new_reset_tick),
            )
            self.reset_tick = new_reset_tick

    @property
    def n_checks_for_reset(self) -> int:
        return int(self.reset_tick // self.check_tick)

    def act(self) -> None:
        """Kill any processes matching blocked app names and (every reset interval)
        reset `blocked_apps.json`.
        """
        if not self.blocked_apps:
            return
        logger = get_logger()

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

        time.sleep(self.check_tick)

        self.check_ticks_since_last_reset += 1
        if self.check_ticks_since_last_reset >= self.n_checks_for_reset:
            self._write_inactive_default_blocked_apps_to_file()
            self.check_ticks_since_last_reset = 0

    def _write_inactive_default_blocked_apps_to_file(self) -> None:
        """Reset `blocked_app.json`, except for the apps that are currently active."""
        logger = get_logger()
        # Note: we don't have to filter for inactive apps here because this will be done in _write_to_blocked_apps_file
        new_blocked_apps: list[str] = sorted(
            self.blocked_apps.union(_load_default_blocked_apps())
        )
        self._write_to_blocked_apps_file(new_blocked_apps)
        logger.info("Reset blocked_apps.json to: %s", set(_load_blocked_apps()))

    def _is_in_blocked_apps(self, name: str) -> bool:
        """Check if this name is in blocked apps."""
        return any(x in self.blocked_apps for x in [name, *name.split("-")])

    def _write_to_blocked_apps_file(self, blocked_apps: list[str]) -> None:
        blocked_apps = sorted(app for app in blocked_apps if not _is_active_app(app))
        with open(BLOCKED_APPS_PATH, "w", encoding="utf-8") as f:
            json.dump(blocked_apps, f, indent=4)


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
            if app.lower() in (str(proc_name) + "-" + str(exe_name)).lower().split("-"):
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


def _load_default_blocked_apps() -> list[str]:
    """Returns all lowercase."""
    return [app.lower() for app in load_json_list_of_strings(DEFAULT_BLOCKED_APPS_PATH)]


def _load_blocked_apps() -> list[str]:
    return [app.lower() for app in load_json_list_of_strings(BLOCKED_APPS_PATH)]


def _load_inactive_blocked_apps_as_set() -> set[str]:
    return {app for app in _load_blocked_apps() if not _is_active_app(app)}


def _load_check_tick() -> float:
    return float(os.environ.get("CHECK_TICK", DEFAULT_CHECK_TICK))


def _load_reset_tick() -> float:
    return float(os.environ.get("RESET_TICK", DEFAULT_RESET_TICK))
