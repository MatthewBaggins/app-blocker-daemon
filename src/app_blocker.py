import json
import logging
import os

from dotenv import load_dotenv
import psutil

from src.constants import (
    BLOCKED_APPS_PATH,
    DEFAULT_BLOCKED_APPS_PATH,
    DEFAULT_CHECK_TICK,
    DEFAULT_RESET_TICK,
    LOGS_DIR,
    DEFAULT_DEFAULT_BLOCKED_APPS,
)
from src.get_logger import get_logger
from src.utils import load_json_list_of_strings, format_float


class AppBlocker:
    """Blocker of apps."""

    __slots__ = (
        "logger",
        "check_tick",
        "reset_tick",
        "previous_check_tick_blocked_apps",
    )

    def __init__(self) -> None:
        load_dotenv()
        self.logger: logging.Logger = get_logger()
        self.check_tick: float = _load_check_tick()
        self.reset_tick: float = _load_reset_tick()
        self.previous_check_tick_blocked_apps: list[str] = []

        self.logger.info("App Blocker started")
        self.logger.info("Default blocked apps file: %s", DEFAULT_BLOCKED_APPS_PATH)
        self.logger.info("Blocked apps file: %s", BLOCKED_APPS_PATH)
        self.logger.info("Logs file: %s", LOGS_DIR / "daemon.log")

    def check_blocked_apps_file_and_log_changes(self) -> None:
        """Check whether the file `blocked_apps.json` has changed and log changes.
        Also handles a few errors.
        """
        try:
            default_blocked_apps = _load_blocked_apps(default=True)
        except (
            json.JSONDecodeError,
            AssertionError,
            FileExistsError,
            FileNotFoundError,
        ) as e:
            default_blocked_apps = DEFAULT_DEFAULT_BLOCKED_APPS.copy()
            with open(DEFAULT_BLOCKED_APPS_PATH, "w", encoding="utf-8") as f:
                json.dump(default_blocked_apps, f)
            self.logger.error(
                "Encountered problems when trying to load default_blocked_app.json: %s. The file was reset.",
                e,
            )

        if not BLOCKED_APPS_PATH.exists():
            self._write_inactive_to_blocked_apps_file(default_blocked_apps)
            blocked_apps = _load_blocked_apps()
            self.logger.error(
                "blocked_apps.json not found; created from default_blocked_apps.json"
            )
        else:
            try:
                blocked_apps = _load_blocked_apps()
            except (json.JSONDecodeError, AssertionError) as e:
                self.logger.error("Error reading blocked_apps.json: %s", e)
                self.logger.info("Resetting blocked_apps.json to default settings.")
                self._write_inactive_to_blocked_apps_file(default_blocked_apps)
                blocked_apps = _load_blocked_apps()

        if self.previous_check_tick_blocked_apps:
            if added_apps := sorted(
                set(blocked_apps).difference(self.previous_check_tick_blocked_apps)
            ):
                self.logger.info("Added to blocked apps: %s", added_apps)
            if removed_apps := sorted(
                set(self.previous_check_tick_blocked_apps).difference(blocked_apps)
            ):
                self.logger.info("Removed from blocked apps: %s", removed_apps)

        self.previous_check_tick_blocked_apps = blocked_apps

        self.logger.info("Current blocked apps: %s", blocked_apps)

    def reload_dotenv(self) -> None:
        """Reload the changes in the `.env` file."""
        if not load_dotenv(override=True):
            return
        if self.check_tick != (new_check_tick := _load_check_tick()):
            self.logger.info(
                "CHECK_TICK changed from %s to %s",
                format_float(self.check_tick),
                format_float(new_check_tick),
            )
            self.check_tick = new_check_tick
        if self.reset_tick != (new_reset_tick := _load_reset_tick()):
            self.logger.info(
                "RESET_TICK changed from %s to %s",
                format_float(self.reset_tick),
                format_float(new_reset_tick),
            )
            self.reset_tick = new_reset_tick

    def kill_blocked_apps(self) -> None:
        """Kill any processes matching names of blocked apps.
        Also, every reset interval reset `blocked_apps.json`.
        """
        if blocked_apps := _load_blocked_apps():
            killed_apps = []
            for proc in psutil.process_iter(["name", "exe"]):
                try:
                    proc_name = proc.info["name"]
                    exe_name = (
                        proc.info["exe"].split("/")[-1] if proc.info["exe"] else ""
                    )
                    if proc_name not in killed_apps and (
                        self._is_in_blocked_apps(
                            str(proc_name).lower().strip(), blocked_apps
                        )
                        or self._is_in_blocked_apps(
                            str(exe_name).lower().strip(), blocked_apps
                        )
                    ):
                        self.logger.warning("Killing %r (PID %d)", proc_name, proc.pid)
                        proc.kill()
                        killed_apps.append(proc_name)

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    pass

    def reset_blocked_apps(self) -> None:
        """Write inactive apps from `default_blocked_apps.json` to `blocked_apps.json`."""
        new_blocked_apps = sorted(
            set(_load_blocked_apps()).union(_load_blocked_apps(default=True))
        )
        self._write_inactive_to_blocked_apps_file(new_blocked_apps)
        self.logger.info("Reset blocked_apps.json to: %s", _load_blocked_apps())

    ########################
    #   "Private" methods  #
    ########################

    def _is_in_blocked_apps(self, app: str, blocked_apps: list[str]) -> bool:
        """Check if this name is in blocked apps."""
        if not app:
            return False
        app_substrings = app.split("-")
        for blocked_app in blocked_apps:
            if blocked_app == app:
                self.logger.info("App %r: found exact match: %r", app, blocked_app)
                return True
            for app_substring in app_substrings:
                if blocked_app == app_substring:
                    self.logger.info(
                        "App %r: found substring match: %r", app, blocked_app
                    )
                    return True
        return False

    def _write_inactive_to_blocked_apps_file(self, new_blocked_apps: list[str]) -> None:
        inactive_new_blocked_apps = sorted(
            app for app in new_blocked_apps if not self._is_active_app(app)
        )
        with open(BLOCKED_APPS_PATH, "w", encoding="utf-8") as f:
            json.dump(inactive_new_blocked_apps, f, indent=4)

    def _is_active_app(self, app: str) -> bool:
        """Check if the app is currently active."""
        self.logger.info("Checking if app %r is active", app)

        for proc in psutil.process_iter(["name", "exe"]):
            try:
                proc_name = proc.info["name"]
                exe_name = proc.info["exe"].split("/")[-1] if proc.info["exe"] else ""

                if app.lower() in [str(proc_name).lower(), str(exe_name).lower()]:
                    self.logger.info(
                        "Found exact match: %r (proc_name=%r, exe_name=%r)",
                        app,
                        proc_name,
                        exe_name,
                    )
                    return True

                # Check if app is a substring (e.g., "signal" in "signal-desktop")
                if app.lower() in f"{proc_name}-{exe_name}".lower().strip().split("-"):
                    self.logger.info(
                        "Found substring match: %r (proc_name=%r, exe_name=%r)",
                        app,
                        proc_name,
                        exe_name,
                    )
                    return True

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        self.logger.info("App %r is not active", app)
        return False

    def __str__(self) -> str:
        return f"AppBlocker(check_tick={self.check_tick}, reset_tick={self.reset_tick}, previous_check_tick_blocked_apps={self.previous_check_tick_blocked_apps})"


def _load_blocked_apps(*, default: bool = False) -> list[str]:
    file_path = DEFAULT_BLOCKED_APPS_PATH if default else BLOCKED_APPS_PATH
    return sorted(app.lower() for app in load_json_list_of_strings(file_path))


def _load_check_tick() -> float:
    return float(os.environ.get("CHECK_TICK", DEFAULT_CHECK_TICK))


def _load_reset_tick() -> float:
    return float(os.environ.get("RESET_TICK", DEFAULT_RESET_TICK))
