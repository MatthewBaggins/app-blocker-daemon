import typing as typ


def is_list_of_strings(x: object) -> typ.TypeGuard[list[str]]:
    return isinstance(x, list) and all(isinstance(el, str) for el in x)
