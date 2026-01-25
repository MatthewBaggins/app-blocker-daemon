import pathlib

DEFAULT_BLOCKED_APPS: list[str] = [
    "discord",
    "slack",
    "steam",
    "brave",
    "firefox",
    "signal",
]


BLOCKED_APPS_PATH = pathlib.Path(__file__).parent.parent / "blocked_apps.json"
LOGS_DIR = pathlib.Path(__file__).parent.parent / "logs"

BLOCKED_APPS_CHECK_INTERVAL: float = 0.5  # 500 ms
BLOCKED_APPS_RESET_INTERVAL: float = 60.0  # 1 minute
