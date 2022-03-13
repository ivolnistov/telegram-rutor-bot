from typing import Any


def escape_value(value: Any) -> str:
    if isinstance(value, str):
        return str.replace(value, '\'', '\'\'')
    return str(value)


def value_fmt(*args: Any) -> str:
    def fmt(value):
        return f'\'{escape_value(value)}\''

    return ', '.join(map(fmt, args))


def where_fmt(**kwargs: str) -> str:
    return ', '.join([f'{k} = \'{escape_value(v)}\'' for k, v in kwargs.items()])
