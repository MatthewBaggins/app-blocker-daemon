from __future__ import annotations

import json
import os
import pathlib

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
from src.utils import load_json_list_of_strings, format_float


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
        self.blocked_apps: list[str] = _load_blocked_apps()
        self._log_init_info()
        self._log_state_info()

    def update(self) -> None:
        load_dotenv(override=True)
        new_check_tick = _load_check_tick()
        new_reset_tick = _load_reset_tick()
        new_blocked_apps = _load_blocked_apps()
        any_changes = self._log_state_changes(
            new_check_tick, new_reset_tick, new_blocked_apps
        )
        if any_changes:
            self.check_tick = new_check_tick
            self.reset_tick = new_reset_tick
            self.blocked_apps = new_blocked_apps
            self._log_state_info()

    def _log_state_changes(
        self, new_check_tick: float, new_reset_tick: float, new_blocked_apps: list[str]
    ) -> bool:
        """Logs the changes in state between the last and the new state.

        This function compares two `State` objects and logs any differences
        in their attributes. Specifically, it logs changes in `check_tick`,
        `reset_tick`, and the differences in the `blocked_apps` list.

        Returns `True` if any changes were found, `False` otherwise.
        """
        any_changes: bool = False
        if self.check_tick != new_check_tick:
            logger.info(
                "CHECK_TICK changed from %s to %s",
                format_float(self.check_tick),
                format_float(new_check_tick),
            )
            any_changes = True
        if self.reset_tick != new_reset_tick:
            logger.info(
                "RESET_TICK changed from %s to %s",
                format_float(self.reset_tick),
                format_float(new_reset_tick),
            )
            any_changes = True
        if added_apps := sorted(set(new_blocked_apps).difference(self.blocked_apps)):
            logger.info("Added to blocked apps: %s", added_apps)
            any_changes = True
        if removed_apps := sorted(set(self.blocked_apps).difference(new_blocked_apps)):
            logger.info("Removed from blocked apps: %s", removed_apps)
            any_changes = True
        return any_changes

    def _log_init_info(self) -> None:
        logger.info("App Blocker started")
        logger.info("Default blocked apps file: %s", DEFAULT_BLOCKED_APPS_PATH)
        logger.info("\tdefault_blocked_apps=%s", _load_blocked_apps(default=True))
        logger.info("Blocked apps file: %s", BLOCKED_APPS_PATH)
        logger.info("Logs file: %s", LOGS_FILE_PATH)

    def _log_state_info(self) -> None:
        logger.info("State:")
        logger.info("\tcheck_tick=%s", format_float(self.check_tick))
        logger.info("\treset_tick=%s", format_float(self.reset_tick))
        logger.info("\tblocked_apps=%s", self.blocked_apps)


def reset_blocked_apps() -> None:
    """Write inactive apps from `default_blocked_apps.json` to `blocked_apps.json`."""
    new_blocked_apps = sorted(
        set(_load_blocked_apps()).union(_load_blocked_apps(default=True))
    )
    blocked_apps = _write_inactive_to_blocked_apps_file(new_blocked_apps)
    logger.info("blocked_apps.json was reset to: %s", blocked_apps)


def kill_blocked_apps() -> None:
    """Kill any processes matching names of blocked apps.
    Also, every reset interval reset `blocked_apps.json`.
    """
    if blocked_apps := _load_blocked_apps():
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


def _load_blocked_apps(*, default: bool = False) -> list[str]:
    """Load and return a sorted list of blocked apps from the appropriate file.
    Handles file not found, JSON decode errors, and format errors gracefully.
    """
    # Always load default blocked apps first
    default_blocked_apps = _load_default_blocked_apps_with_fallback()

    if default:
        return default_blocked_apps

    # Load user blocked apps
    return _load_user_blocked_apps_with_fallback(default_blocked_apps)


def _load_default_blocked_apps_with_fallback() -> list[str]:
    """Load default blocked apps, with fallback to hardcoded defaults if file is corrupt."""
    try:
        return sorted(
            app.lower() for app in load_json_list_of_strings(DEFAULT_BLOCKED_APPS_PATH)
        )
    except (json.JSONDecodeError, AssertionError, FileNotFoundError) as e:
        logger.error("Error loading default_blocked_apps.json: %s", e)
        logger.info("Using hardcoded defaults")
        logger.info("Writing default_blocked_apps.json using hardcoded defaults")
        with open(DEFAULT_BLOCKED_APPS_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DEFAULT_BLOCKED_APPS, f)
        return sorted(app.lower() for app in DEFAULT_DEFAULT_BLOCKED_APPS)


def _load_user_blocked_apps_with_fallback(default_blocked_apps: list[str]) -> list[str]:
    """Load user blocked apps, creating from defaults if missing or resetting if corrupt."""
    # File doesn't exist: create from defaults
    if not BLOCKED_APPS_PATH.exists():
        logger.warning(
            "blocked_apps.json not found; creating from default_blocked_apps.json"
        )
        return _write_inactive_to_blocked_apps_file(default_blocked_apps)

    # File exists: try to load it
    try:
        return _load_from_file(BLOCKED_APPS_PATH)
    except (json.JSONDecodeError, AssertionError) as e:
        logger.error("Error reading blocked_apps.json: %s", e)
        logger.warning("Resetting blocked_apps.json to default settings")
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
    Writes a list of inactive blocked applications to a JSON file.

    This function filters the provided list of applications to include only those
    that are not currently active. The filtered list is then sorted and written
    to a JSON file specified by the `BLOCKED_APPS_PATH` constant.

    Returns the apps that were written.
    """
    inactive_new_blocked_apps = sorted(
        app for app in new_blocked_apps if not _is_active_app(app)
    )
    with open(BLOCKED_APPS_PATH, "w", encoding="utf-8") as f:
        json.dump(inactive_new_blocked_apps, f, indent=4)
    return inactive_new_blocked_apps


def _is_active_app(app: str) -> bool:
    """Check if the app is currently active."""
    for proc in psutil.process_iter(["name", "exe"]):
        try:
            proc_name = proc.info["name"]
            exe_name = proc.info["exe"].split("/")[-1] if proc.info["exe"] else ""

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


def _load_from_file(file_path: pathlib.Path) -> list[str]:
    """Load and sort apps from a JSON file."""
    return sorted(app.lower() for app in load_json_list_of_strings(file_path))
