#!/usr/bin/env python3
"""
Standalone app blocker daemon.
Reads blocked apps from blocked_apps.txt and kills matching processes.
"""
import time

from src.app_blocking import State, reset_blocked_apps, kill_blocked_apps
from src.make_running_flag import make_running_flag


def main() -> None:
    """
    Initializes the running flag and application state, then enters
    a loop to periodically reset and kill blocked applications based on the
    configured time intervals. The loop continues as long as the running flag
    remains active.

    Performs the following tasks:
    - Resets the list of blocked applications if the reset interval has elapsed.
    - Kills currently blocked applications.
    - Sleeps for a duration specified by the state's check interval.
    - Updates the application state at the end of each loop iteration.
    """
    state = State()
    running_flag = make_running_flag()
    last_blocked_apps_reset_time: float = 0.0

    while running_flag:
        if ((now := time.time()) - last_blocked_apps_reset_time) >= state.reset_tick:
            reset_blocked_apps()
            last_blocked_apps_reset_time = now
        kill_blocked_apps()
        time.sleep(state.check_tick)
        state.update()


if __name__ == "__main__":
    main()
