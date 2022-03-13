from typing import Iterable, List
from .connections import cursor
import models as m


__all__ = (
    'add_torrent',
    'get_torrent_by_id',
    'get_torrents',
    'get_torrent_by_blake',
    'get_torrents_by_film',
    'get_torrent_by_magnet',
    'modify_torrent',
)

from .helpers import where_fmt
from .db import log

def get_torrent_by_blake(blake, connection):
    q = f'SELECT id FROM torrents WHERE blake = \'{blake}\''
    log.debug('executing query: "%s"', q)
    res = connection.cursor().execute(q).fetchone()
    if res:
        return res[0]


def modify_torrent(id, connection=None, **kwargs):
    q = f'UPDATE torrents SET {where_fmt(**kwargs)} WHERE id = {id}'
    log.debug('executing query: "%s"', q)
    with cursor(connection) as cur:
        cur.execute(q)


def get_torrent_by_magnet(magnet, connection=None):
    q = f'SELECT * FROM torrents WHERE magnet = \'{magnet}\''
    log.info('executing query: "%s"', q)
    with cursor(connection=connection) as cur:
        return m.Torrent(*cur.execute(q).fetchone())


def add_torrent(film_id, blake, name, created, magnet, link, size, approved, downloaded, connection):
    name = name.replace('\'', '\'\'')
    q = f'''INSERT INTO torrents 
    (film_id, blake, name, magnet, created, link, sz, approved, downloaded) 
    VALUES ('{film_id}', '{blake}', '{name}', '{magnet}', '{created}', '{link}', {size}, {approved}, {downloaded});'''
    log.debug('executing query: "%s"', q)
    with cursor(connection) as cur:
        cur.execute(q)
        return cur.lastrowid


def get_torrents_by_film(film_id: int) -> Iterable:
    q = 'SELECT * FROM torrents WHERE film_id = ' + str(film_id)
    log.debug('executing query: "%s"', q)
    with cursor() as cur:
        for torrent in cur.execute(q):
            yield m.Torrent(*torrent)


def get_torrent_by_id(id: int):
    with cursor() as cur:
        return m.Torrent(*cur.execute('SELECT * FROM torrents WHERE id = ' + str(id)).fetchone())


def get_torrents(films: List[int]) -> Iterable:
    q = 'SELECT * FROM torrents WHERE id IN (' + ','.join(map(str, films)) + ')'
    log.debug('executing query: "%s"', q)
    with cursor() as cur:
        return cur.execute(q)
