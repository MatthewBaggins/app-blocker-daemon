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

BLOCKED_APPS_CHECK_INTERVAL: float = 1.0  # 1 second
BLOCKED_APPS_RESET_INTERVAL: float = 2 * 60.0  # 2 minutes
