from __future__ import annotations

import os
import typing as typ

from dotenv import load_dotenv
import psutil

from src.constants import (
    BLOCKED_APPS_PATH,
    DEFAULT_CHECK_TICK,
    DEFAULT_RESET_TICK,
    DEFAULT_BLOCKED_APPS_PATH,
    DEFAULT_DEFAULT_BLOCKED_APPS,
    LOGS_FILE_PATH,
)
from src.logger import logger
from src.utils import load_list_of_strings_from_txt, format_float


class State:
    """Represents the application state, including check and reset intervals, and blocked apps."""

    __slots__ = (
        "check_tick",
        "reset_tick",
        "blocked_apps",
    )

    def __init__(self) -> None:
        load_dotenv()
        self.check_tick: float = _load_check_tick()
        self.reset_tick: float = _load_reset_tick()
        self.blocked_apps: list[str] = _load_blocked_apps("user")
        self._log_init_info()
        self._log_state_info()

    def update(self) -> None:
        """Updates the state object's fields to new values and logs the changes."""
        any_changes: bool = False

        # Environmental variables
        load_dotenv(override=True)
        if self.check_tick != (new_check_tick := _load_check_tick()):
            logger.info(
                "CHECK_TICK changed from %s to %s",
                format_float(self.check_tick),
                format_float(new_check_tick),
            )
            self.check_tick = new_check_tick
            any_changes = True
        if self.reset_tick != (new_reset_tick := _load_reset_tick()):
            logger.info(
                "RESET_TICK changed from %s to %s",
                format_float(self.reset_tick),
                format_float(new_reset_tick),
            )
            self.reset_tick = new_reset_tick
            any_changes = True

        # Blocked apps
        new_blocked_apps = _load_blocked_apps("user")
        if added_apps := sorted(set(new_blocked_apps).difference(self.blocked_apps)):
            logger.info("Added to blocked apps: %s", added_apps)
        if removed_apps := sorted(set(self.blocked_apps).difference(new_blocked_apps)):
            logger.info("Removed from blocked apps: %s", removed_apps)
        if added_apps or removed_apps:
            logger.info(
                "Blocked apps changed from %s to %s",
                self.blocked_apps,
                new_blocked_apps,
            )
            self.blocked_apps.clear()
            self.blocked_apps.extend(new_blocked_apps)
            any_changes = True

        # Log changes if any
        if any_changes:
            self._log_state_info()

    def _log_init_info(self) -> None:
        logger.info("App Blocker started")
        logger.info("Default blocked apps file: %s", DEFAULT_BLOCKED_APPS_PATH)
        logger.info("\tdefault_blocked_apps=%s", _load_blocked_apps("default"))
        logger.info("Blocked apps file: %s", BLOCKED_APPS_PATH)
        logger.info("Logs file: %s", LOGS_FILE_PATH)

    def _log_state_info(self) -> None:
        logger.info("State:")
        logger.info("\tcheck_tick=%s", format_float(self.check_tick))
        logger.info("\treset_tick=%s", format_float(self.reset_tick))
        logger.info("\tblocked_apps=%s", self.blocked_apps)


def reset_blocked_apps() -> None:
    """Write inactive apps from `default_blocked_apps.txt` to `blocked_apps.txt`."""
    new_blocked_apps = sorted(
        set(_load_blocked_apps("user")).union(_load_blocked_apps("default"))
    )
    blocked_apps = _write_inactive_to_blocked_apps_file(new_blocked_apps)
    logger.info("blocked_apps.txt was reset to: %s", blocked_apps)


def kill_blocked_apps() -> None:
    """Kill any processes matching names of blocked apps.
    Also, every reset interval reset `blocked_apps.txt`.
    """
    if blocked_apps := _load_blocked_apps("user"):
        killed_apps = []
        for proc in psutil.process_iter(["name", "exe"]):
            try:
                proc_name = proc.info["name"]
                exe_name = proc.info["exe"].split("/")[-1] if proc.info["exe"] else ""
                if proc_name not in killed_apps and (
                    _is_in_blocked_apps(str(proc_name).lower().strip(), blocked_apps)
                    or _is_in_blocked_apps(str(exe_name).lower().strip(), blocked_apps)
                ):
                    logger.warning("Killing %r (PID %d)", proc_name, proc.pid)
                    proc.kill()
                    killed_apps.append(proc_name)
            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ):
                pass


#############################
#    "Private" functions    #
#############################

BlockedAppsFileType = typ.Literal["user", "default"]


def _load_blocked_apps(filetype: BlockedAppsFileType, /) -> list[str]:
    """Load and return a sorted list of blocked apps from the appropriate file.
    Handles file not found and format errors gracefully.
    """
    # Always load default blocked apps first
    default_blocked_apps = _load_default_blocked_apps_with_fallback()
    match filetype:
        case "default":
            return default_blocked_apps
        case "user":
            # Load user blocked apps
            return _load_user_blocked_apps_with_fallback(default_blocked_apps)


def _load_default_blocked_apps_with_fallback() -> list[str]:
    """Load default blocked apps, with fallback to hardcoded defaults if file is corrupt."""
    try:
        return _load_blocked_apps_from_file("default")
    except (AssertionError, FileNotFoundError) as e:
        logger.error("Error loading default_blocked_apps.txt: %s", e)
        logger.info("Using hardcoded defaults")
        logger.info("Writing default_blocked_apps.txt using hardcoded defaults")
        with open(DEFAULT_BLOCKED_APPS_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(DEFAULT_DEFAULT_BLOCKED_APPS))
        return _load_blocked_apps_from_file("default")


def _load_user_blocked_apps_with_fallback(default_blocked_apps: list[str]) -> list[str]:
    """Load user blocked apps, creating from defaults if missing or resetting if corrupt."""
    # File doesn't exist: create from defaults
    if not BLOCKED_APPS_PATH.exists():
        logger.warning(
            "blocked_apps.txt not found; creating from default_blocked_apps.txt"
        )
        return _write_inactive_to_blocked_apps_file(default_blocked_apps)
    # File exists: try to load it
    try:
        return _load_blocked_apps_from_file("user")
    except AssertionError as e:
        logger.error("Error reading blocked_apps.txt: %s", e)
        logger.warning("Resetting blocked_apps.txt to default settings")
        return _write_inactive_to_blocked_apps_file(default_blocked_apps)


def _is_in_blocked_apps(app: str, blocked_apps: list[str]) -> bool:
    """Check if this name is in blocked apps."""
    if not app:
        return False
    app_substrings = app.split("-")
    for blocked_app in blocked_apps:
        if blocked_app == app:
            logger.info("App %r: found exact match", app)
            return True
        for app_substring in app_substrings:
            if blocked_app == app_substring:
                logger.info("App %r: found substring match (%r)", app, blocked_app)
                return True
    return False


def _write_inactive_to_blocked_apps_file(new_blocked_apps: list[str]) -> list[str]:
    """
    Writes a list of inactive blocked applications to a text file.

    This function filters the provided list of applications to include only those
    that are not currently active. The filtered list is then sorted and written
    to a text file specified by the `BLOCKED_APPS_PATH` constant.

    Returns the apps that were written.
    """
    inactive_new_blocked_apps = sorted(
        app for app in new_blocked_apps if not _is_active_app(app)
    )
    with open(BLOCKED_APPS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(inactive_new_blocked_apps))
    return inactive_new_blocked_apps


def _is_active_app(app: str) -> bool:
    """Check if the app is currently active."""
    for proc in psutil.process_iter(["name", "exe"]):
        try:
            proc_name = proc.info["name"]
            exe_name = proc.info["exe"].split("/")[-1] if proc.info["exe"] else ""
            # Check if app is perfect match
            if app.lower() in [str(proc_name).lower(), str(exe_name).lower()]:
                logger.info(
                    "Found exact match: %r is active (proc_name=%r, exe_name=%r)",
                    app,
                    proc_name,
                    exe_name,
                )
                return True
            # Check if app is a substring (e.g., "signal" in "signal-desktop")
            if app.lower() in f"{proc_name}-{exe_name}".lower().strip().split("-"):
                logger.info(
                    "Found substring match: %r is active (proc_name=%r, exe_name=%r)",
                    app,
                    proc_name,
                    exe_name,
                )
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def _load_check_tick() -> float:
    """Load CHECK_TICK from `.env`. If not found, return the `DEFAULT_CHECK_TICK` constant."""
    return float(os.environ.get("CHECK_TICK", DEFAULT_CHECK_TICK))


def _load_reset_tick() -> float:
    """Load RESET_TICK from `.env`. If not found, return the `DEFAULT_RESET_TICK` constant."""
    return float(os.environ.get("RESET_TICK", DEFAULT_RESET_TICK))


def _load_blocked_apps_from_file(mode: BlockedAppsFileType, /) -> list[str]:
    """Load and sort apps from a text file."""
    match mode:
        case "default":
            file_path = DEFAULT_BLOCKED_APPS_PATH
        case "user":
            file_path = BLOCKED_APPS_PATH
    return sorted(app.lower() for app in load_list_of_strings_from_txt(file_path))
