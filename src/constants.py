import pathlib

REPO_PATH = pathlib.Path(__file__).parent.parent

DEFAULT_BLOCKED_APPS_PATH = REPO_PATH / "default_blocked_apps.json"
BLOCKED_APPS_PATH = REPO_PATH / "blocked_apps.json"
LOGS_DIR = REPO_PATH / "logs"

BLOCKED_APPS_CHECK_INTERVAL: float = 1.0  # 1 second
BLOCKED_APPS_RESET_INTERVAL: float = 2 * 60.0  # 2 minutes
