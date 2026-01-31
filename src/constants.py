import pathlib

REPO_PATH = pathlib.Path(__file__).parent.parent

DEFAULT_BLOCKED_APPS_PATH = REPO_PATH / "default_blocked_apps.json"
BLOCKED_APPS_PATH = REPO_PATH / "blocked_apps.json"
LOGS_DIR = REPO_PATH / "logs"
DOTENV_PATH = REPO_PATH / ".env"

DEFAULT_CHECK_TICK: float = 1.0  # 1 second
DEFAULT_RESET_TICK: float = 300.0  # 5 minutes
