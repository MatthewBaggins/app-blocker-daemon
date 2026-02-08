import pathlib


def load_list_of_strings_from_txt(path: pathlib.Path) -> list[str]:
    """Load a list of strings from a text file, newline-separated."""
    assert path.suffix == ".txt", f"{path=!r}; {path.suffix=!r}"
    with open(path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.read().split("\n") if l.strip()]
    return lines


class Box[T]:
    """Something like pointer in more low-level proglangs or Box<T> in Rust."""

    __slots__ = ("value",)

    def __init__(self, value: T, /) -> None:
        self.value: T = value

    def __bool__(self) -> bool:
        return bool(self.value)


def format_float(x: float, *, max_digits_after_comma: int = 2) -> str:
    """Format a floating point number to have some maximum number of digits after comma,
    prune trailing zeros, and the trailing dot if integer, and then return a string.
    """
    s = str(x)
    if (dot_loc := s.find(".")) == -1:
        return s
    return s[: dot_loc + max_digits_after_comma].rstrip("0").rstrip(".")
