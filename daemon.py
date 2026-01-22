#!/usr/bin/env python3
"""
Standalone app blocker daemon.
Reads blocked apps from config.json and kills matching processes.
"""

import signal
import time


from src.load_config import Config, CONFIG_PATH


def main() -> None:
    print("App Blocker started")
    print(f"Config: {CONFIG_PATH}")

    # Handle graceful shutdown
    running = True

    def _shutdown(sig, frame) -> None:
        nonlocal running
        print("\nShutting down...")
        running = False

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    last_mtime = 0
    config = Config()

    while running:
        # Reload config if changed
        try:
            mtime = CONFIG_PATH.stat().st_mtime
            if mtime > last_mtime:
                config = Config()
                last_mtime = mtime
                print(f"Loaded blocked apps: {config.blocked_apps}")
        except FileNotFoundError:
            pass

        # Kill blocked apps
        config.kill_blocked_apps()

        time.sleep(config.check_interval)

    print("Daemon stopped")


if __name__ == "__main__":
    main()
