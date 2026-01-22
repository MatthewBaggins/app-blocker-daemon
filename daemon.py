#!/usr/bin/env python3
"""
Standalone app blocker daemon.
Reads blocked apps from config.json and kills matching processes.
"""

import json
import signal
import time
import pathlib
import psutil

CONFIG_PATH = pathlib.Path(__file__).parent / "config.json"


class AppBlocker:
    __slots__ = ("blocked_apps", "check_interval")
    blocked_apps: set[str]
    check_interval: float

    def __init__(self) -> None:
        self.reload()

    def reload(self) -> None:
        """Reload the settings from `./config.json`."""
        assert CONFIG_PATH.exists()
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        self.blocked_apps = set(config["blocked_apps"])
        self.check_interval = config["check_interval"]

    def kill_blocked_apps(self) -> None:
        """Kill any processes matching blocked app names."""
        if not self.blocked_apps:
            return
        for proc in psutil.process_iter(["name", "exe"]):
            try:
                proc_name = proc.info["name"]
                exe_name = proc.info["exe"].split("/")[-1] if proc.info["exe"] else ""

                if proc_name in self.blocked_apps or exe_name in self.blocked_apps:
                    print(f"Killing {proc_name} (PID {proc.pid})")
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass


def main() -> None:
    print("App Blocker started")
    print(f"Config: {CONFIG_PATH}")

    # Handle graceful shutdown
    running = True

    def _shutdown(_sig, _frame) -> None:
        nonlocal running
        print("\nShutting down...")
        running = False

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    last_mtime = 0
    app_blocker = AppBlocker()

    while running:
        # Reload config if changed
        try:
            mtime = CONFIG_PATH.stat().st_mtime
            if mtime > last_mtime:
                app_blocker.reload()
                last_mtime = mtime
                print(f"Loaded blocked apps: {app_blocker.blocked_apps}")
        except FileNotFoundError:
            pass

        # Kill blocked apps
        app_blocker.kill_blocked_apps()

        time.sleep(app_blocker.check_interval)

    print("Daemon stopped")


if __name__ == "__main__":
    main()
