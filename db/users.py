from sqlite3 import Connection

import models as m
from .connections import execute, cursor
from .helpers import value_fmt


__all__ = (
    'get_user',
    'get_user_by_chat',
    'get_or_create_user_by_chat_id',
)


def get_or_create_user_by_chat_id(id: int) -> m.User:
    try:
        return get_user_by_chat(id)
    except StopIteration:
        pass
    return create_user(id)


def create_user(chat_id: int) -> m.User:
    q = f'INSERT INTO user (chat_id) VALUES ({value_fmt(chat_id)})'
    with cursor() as cur:
        cur.execute(q)
        return m.User(id=cur.lastrowid, chat_id=chat_id)


def get_user(id: int, connection: 'Connection') -> m.User:
    q = 'SELECT * FROM user WHERE id = ' + str(id)
    return m.User(*next(execute(q, connection)))


def get_user_by_chat(chat_id: int) -> m.User:
    q = 'SELECT * FROM user WHERE chat_id = ' + str(chat_id)
    return m.User(*next(execute(q)))
