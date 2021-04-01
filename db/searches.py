from typing import Iterable, List, TYPE_CHECKING

from .connections import cursor, execute
import models as m


if TYPE_CHECKING:
    from sqlite3 import Connection


def add_search_to_db(url: str, cron: str, creator_id: int):
    with cursor() as cur:
        count = cur.execute(f'SELECT count(*) FROM searches WHERE url=\'{url}\'').fetchone()[0]
        if count:
            raise ValueError(f'search with url {url} already exists')
        cur.execute(f'INSERT INTO searches (url, cron, creator_id) VALUES (\'{url}\', \'{cron}\', \'{creator_id}\')')
        return cur.lastrowid


def get_searches(show_empty: bool = False, connection: 'Connection' = None) -> List['m.Search']:
    non_empty_q = 'SELECT *, (SELECT COUNT(*) FROM subscribes WHERE search_id =searches.id) subscribers FROM searches WHERE subscribers;'
    with_empty_q = 'SELECT * FROM searches'
    with cursor(connection) as cur:
        for search in cur.execute(with_empty_q if show_empty else non_empty_q):
            yield m.Search(*search[:4])


def delete_search(id: int) -> None:
    q = 'DELETE FROM searches WHERE id = ' + str(id)
    return execute(q)


def get_search_subscribers(id: int) -> Iterable['m.User']:
    q = 'SELECT u.* FROM subscribes JOIN user u on u.id = subscribes.user_id WHERE search_id = ' + str(id)
    for u in execute(q):
        yield m.User(*u)
