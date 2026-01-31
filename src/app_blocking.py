from __future__ import annotations

import json
import os
import pathlib
import typing as typ

from dotenv import load_dotenv
import psutil

from src.constants import (
    BLOCKED_APPS_PATH,
    DEFAULT_CHECK_TICK,
    DEFAULT_RESET_TICK,
    DEFAULT_BLOCKED_APPS_PATH,
    DEFAULT_DEFAULT_BLOCKED_APPS,
    LOGS_FILE,
)
from src.logger import logger
from src.utils import load_json_list_of_strings, format_float


class State(typ.NamedTuple):
    """Represents the application state, including check and reset intervals, and blocked apps."""

    check_tick: float
    reset_tick: float
    blocked_apps: list[str]

    @classmethod
    def make(cls, *, last_state: State | None) -> State:
        load_dotenv(override=True)
        new_state = State(
            check_tick=_load_check_tick(),
            reset_tick=_load_reset_tick(),
            blocked_apps=_load_blocked_apps(),
        )
        if last_state is not None and last_state != new_state:
            _log_state_changes(last_state=last_state, new_state=new_state)
        if last_state is None:
            logger.info("App Blocker started")
            logger.info("Default blocked apps file: %s", DEFAULT_BLOCKED_APPS_PATH)
            logger.info("Blocked apps file: %s", BLOCKED_APPS_PATH)
            logger.info("Logs file: %s", LOGS_FILE)
            logger.info("State: %s", new_state)
        return new_state


def reset_blocked_apps() -> None:
    """Write inactive apps from `default_blocked_apps.json` to `blocked_apps.json`."""
    new_blocked_apps = sorted(
        set(_load_blocked_apps()).union(_load_blocked_apps(default=True))
    )
    _write_inactive_to_blocked_apps_file(new_blocked_apps)
    logger.info("Reset blocked_apps.json to: %s", _load_blocked_apps())


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


def _log_state_changes(last_state: State, new_state: State) -> None:
    """
    Logs the changes in state between the last and the new state.

    This function compares two `State` objects and logs any differences
    in their attributes. Specifically, it logs changes in `check_tick`,
    `reset_tick`, and the differences in the `blocked_apps` list.
    """
    if last_state.check_tick != new_state.check_tick:
        logger.info(
            "CHECK_TICK changed from %s to %s",
            format_float(last_state.check_tick),
            format_float(new_state.check_tick),
        )
    if last_state.reset_tick != new_state.reset_tick:
        logger.info(
            "RESET_TICK changed from %s to %s",
            format_float(last_state.reset_tick),
            format_float(new_state.reset_tick),
        )
    if added_apps := sorted(
        set(new_state.blocked_apps).difference(last_state.blocked_apps)
    ):
        logger.info("Added to blocked apps: %s", added_apps)
    if removed_apps := sorted(
        set(last_state.blocked_apps).difference(new_state.blocked_apps)
    ):
        logger.info("Removed from blocked apps: %s", removed_apps)


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
        logger.error(
            "Error loading default_blocked_apps.json: %s.",
            e,
        )
        logger.info("Using hardcoded defaults.")
        logger.info("Writing default_blocked_apps.json using hardcoded defaults.")
        default_blocked_apps = DEFAULT_DEFAULT_BLOCKED_APPS.copy()
        with open(DEFAULT_BLOCKED_APPS_PATH, "w", encoding="utf-8") as f:
            json.dump(default_blocked_apps, f)
        return sorted(app.lower() for app in default_blocked_apps)


def _load_user_blocked_apps_with_fallback(default_blocked_apps: list[str]) -> list[str]:
    """Load user blocked apps, creating from defaults if missing or resetting if corrupt."""
    # File doesn't exist: create from defaults
    if not BLOCKED_APPS_PATH.exists():
        logger.warning(
            "blocked_apps.json not found; creating from default_blocked_apps.json"
        )
        _write_inactive_to_blocked_apps_file(default_blocked_apps)
        return _load_from_file(BLOCKED_APPS_PATH)

    # File exists: try to load it
    try:
        return _load_from_file(BLOCKED_APPS_PATH)
    except (json.JSONDecodeError, AssertionError) as e:
        logger.error("Error reading blocked_apps.json: %s", e)
        logger.warning("Resetting blocked_apps.json to default settings.")
        _write_inactive_to_blocked_apps_file(default_blocked_apps)
        return _load_from_file(BLOCKED_APPS_PATH)


def _is_in_blocked_apps(app: str, blocked_apps: list[str]) -> bool:
    """Check if this name is in blocked apps."""
    if not app:
        return False
    app_substrings = app.split("-")
    for blocked_app in blocked_apps:
        if blocked_app == app:
            logger.info("App %r: found exact match: %r", app, blocked_app)
            return True
        for app_substring in app_substrings:
            if blocked_app == app_substring:
                logger.info("App %r: found substring match: %r", app, blocked_app)
                return True
    return False


def _write_inactive_to_blocked_apps_file(new_blocked_apps: list[str]) -> None:
    """
    Writes a list of inactive blocked applications to a JSON file.

    This function filters the provided list of applications to include only those
    that are not currently active. The filtered list is then sorted and written
    to a JSON file specified by the `BLOCKED_APPS_PATH` constant.
    """
    inactive_new_blocked_apps = sorted(
        app for app in new_blocked_apps if not _is_active_app(app)
    )
    with open(BLOCKED_APPS_PATH, "w", encoding="utf-8") as f:
        json.dump(inactive_new_blocked_apps, f, indent=4)


def _is_active_app(app: str) -> bool:
    """Check if the app is currently active."""
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
            if app.lower() in f"{proc_name}-{exe_name}".lower().strip().split("-"):
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


def _load_check_tick() -> float:
    """Load CHECK_TICK from `.env`. If not found, return the `DEFAULT_CHECK_TICK` constant."""
    return float(os.environ.get("CHECK_TICK", DEFAULT_CHECK_TICK))


def _load_reset_tick() -> float:
    """Load RESET_TICK from `.env`. If not found, return the `DEFAULT_RESET_TICK` constant."""
    return float(os.environ.get("RESET_TICK", DEFAULT_RESET_TICK))


def _load_from_file(file_path: pathlib.Path) -> list[str]:
    """Load and sort apps from a JSON file."""
    return sorted(app.lower() for app in load_json_list_of_strings(file_path))
