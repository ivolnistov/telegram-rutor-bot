from typing import Any


def value_fmt(*args: Any) -> str:
    def fmt(value):
        return f'\'{str(value)}\''

    return ', '.join(map(fmt, args))


def where_fmt(**kwargs: str) -> str:
    return ', '.join([f'{k} = \'{v}\'' for k, v in kwargs.items()])
