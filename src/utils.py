import json
import pathlib
import typing as typ

from src.constants import DEFAULT_BLOCKED_APPS_PATH


def is_list_of_strings(x: object) -> typ.TypeGuard[list[str]]:
    return isinstance(x, list) and all(isinstance(el, str) for el in x)


def load_json_list_of_strings(path: pathlib.Path | str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert is_list_of_strings(loaded), f"{loaded=!r} is not a list of strings."
    return loaded


def load_default_blocked_apps() -> list[str]:
    return load_json_list_of_strings(DEFAULT_BLOCKED_APPS_PATH)
