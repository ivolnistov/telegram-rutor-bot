import sqlite3
from typing import Iterable

from .connections import cursor
from .helpers import where_fmt, value_fmt

import models as m


__all__ = (
    'subscribe',
    'unsubscribe',
    'get_subscriptions',
)


def subscribe(search_id, chat_id):
    count_q = f'SELECT id FROM user where chat_id = {chat_id}'
    with cursor() as cur:
        try:
            id = next(cur.execute(count_q))[0]
        except StopIteration:
            cur.execute(f'INSERT INTO user (chat_id) VALUES ({chat_id})')
            id = cur.lastrowid
        try:
            cur.execute(f'INSERT INTO subscribes (search_id, user_id) VALUES ({value_fmt(search_id, id)})')
        except sqlite3.IntegrityError:
            return False, f'You already subscriber to search {search_id}'
        return True, ''


def unsubscribe(search_id, user_id):
    q = f'DELETE FROM subscribes WHERE {where_fmt(search_id=search_id, user_id=user_id)}'
    with cursor() as cur:
        return cur.execute(q)


def get_subscriptions(user_id: int) -> Iterable[m.Search]:
    q = f'SELECT searches.* FROM searches JOIN subscribes ON subscribes.search_id = searches.id WHERE subscribes.user_id = {user_id}'
    with cursor() as cur:
        for search in cur.execute(q):
            yield m.Search(*search)
