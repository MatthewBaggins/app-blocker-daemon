import pathlib

REPO_PATH = pathlib.Path(__file__).parent.parent

DEFAULT_BLOCKED_APPS_PATH = REPO_PATH / "default_blocked_apps.json"
BLOCKED_APPS_PATH = REPO_PATH / "blocked_apps.json"
LOGS_DIR = REPO_PATH / "logs"
DOTENV_PATH = REPO_PATH / ".env"
