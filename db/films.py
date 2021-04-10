from typing import Iterable, List, TYPE_CHECKING

from db import cursor
import models as m
from .connections import execute


if TYPE_CHECKING:
    from sqlite3 import Connection


def get_or_create_film(name: List[str], year: int, blake: str, connection: 'Connection' = None):
    with cursor(connection) as cur:
        q = f'SELECT id FROM films WHERE blake = \'{blake}\''
        res = cur.execute(q).fetchone()
        if res:
            return res[0], False
        name = (' / '.join(name)).replace('\'', '\'\'')
        inq = f'INSERT INTO films (name, year, blake) VALUES (\'{name}\', \'{year}\', \'{blake}\')'
        cur.execute(inq)
        return cur.lastrowid, True


def get_films(limit: int = 20, connection: 'Connection' = None, query='', order='ASC') -> Iterable:
    sub_q = '(SELECT min(created) FROM torrents WHERE torrents.film_id = films.id)'
    where_clause = ''
    if query:
        where_clause = f'WHERE {query}'
    q = f'''SELECT films.*, {sub_q} created FROM films {where_clause} ORDER BY created {str.upper(order)} LIMIT {limit};'''
    with cursor(connection) as cur:
        for film in cur.execute(q):
            yield m.Film(*film)


def get_films_by_ids(ids: List[int], connection: 'Connection' = None) -> Iterable[m.Film]:
    q = 'SELECT * FROM films WHERE id IN (' + ','.join(map(str, ids)) + ')'
    for film in execute(q, connection):
        yield m.Film(*film)
