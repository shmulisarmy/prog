from typing import get_args, get_origin


def my_isinstance(value, expected):
    if get_origin(expected) is list:
        if not isinstance(value, list):
            return False

        args = get_args(expected)
        return not args or all(my_isinstance(item, args[0]) for item in value)

    return isinstance(value, expected)


def black(text: str):
    return f"\033[30m{text}\033[0m"


def red(text: str):
    return f"\033[31m{text}\033[0m"


def green(text: str):
    return f"\033[32m{text}\033[0m"


def yellow(text: str):
    return f"\033[33m{text}\033[0m"


def blue(text: str):
    return f"\033[34m{text}\033[0m"


def magenta(text: str):
    return f"\033[35m{text}\033[0m"


def cyan(text: str):
    return f"\033[36m{text}\033[0m"


def white(text: str):
    return f"\033[37m{text}\033[0m"
