import json
import pathlib
import typing as typ


def is_list_of_strings(x: object) -> typ.TypeGuard[list[str]]:
    return isinstance(x, list) and all(isinstance(el, str) for el in x)


def load_json_list_of_strings(path: pathlib.Path | str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert is_list_of_strings(
        loaded
    ), f"{loaded=!r} from {path=!r} is not a list of strings."
    return loaded


class Box[T]:
    __slots__ = ("value",)

    def __init__(self, value: T, /) -> None:
        self.value: T = value

    def __bool__(self) -> bool:
        return bool(self.value)


def format_float(x: float, *, max_digits_after_comma: int = 2) -> str:
    s = str(x)
    if (dot_loc := s.find(".")) == -1:
        return s
    return s[: dot_loc + max_digits_after_comma].rstrip("0").rstrip(".")
