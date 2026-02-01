import pathlib

# Paths
REPO_PATH = pathlib.Path(__file__).parent.parent

DEFAULT_BLOCKED_APPS_PATH = REPO_PATH / "default_blocked_apps.json"
BLOCKED_APPS_PATH = REPO_PATH / "blocked_apps.json"
LOGS_DIR_PATH = REPO_PATH / "logs"
LOGS_FILE_PATH = LOGS_DIR_PATH / "daemon.log"
DOTENV_FILE_PATH = REPO_PATH / ".env"

# Default values
DEFAULT_CHECK_TICK: float = 1.0  # 1 second
DEFAULT_RESET_TICK: float = 300.0  # 5 minutes
DEFAULT_DEFAULT_BLOCKED_APPS: list[str] = [
    "brave",
    "discord",
    "firefox",
    "signal",
    "slack",
    "steam",
]
