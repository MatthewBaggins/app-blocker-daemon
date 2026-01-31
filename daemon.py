#!/usr/bin/env python3
"""
Standalone app blocker daemon.
Reads blocked apps from blocked_apps.json and kills matching processes.
"""
import time


from src.app_blocking import State, reset_blocked_apps, kill_blocked_apps
from src.register_shutdown_handling import register_shutdown_handling
from src.utils import Box


def main() -> None:
    running: Box[bool] = register_shutdown_handling()
    state = State.make(last_state=None)
    last_blocked_apps_reset_time: float = 0.0

    while running:
        if ((now := time.time()) - last_blocked_apps_reset_time) >= state.reset_tick:
            reset_blocked_apps()
            last_blocked_apps_reset_time = now
        kill_blocked_apps()
        time.sleep(state.check_tick)
        state = State.make(last_state=state)


if __name__ == "__main__":
    main()
