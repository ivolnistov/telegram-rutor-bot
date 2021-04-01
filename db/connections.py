import contextlib
import logging
import sqlite3
from sqlite3 import Connection

import settings


__all__ = ('connection', 'cursor', 'execute',)
log = logging.getLogger(f'{settings.LOG_PREFIX}.sql')

globals()['__CONNECTION'] = None


@contextlib.contextmanager
def connection():
    try:
        connection = sqlite3.connect(settings.DB_PATH)
        yield connection
        connection.close()
    except sqlite3.Error as error:
        log.error('sqlite connection error:', error)


def _connection():
    if globals()['__CONNECTION'] is None:
        try:
            globals()['__CONNECTION'] = sqlite3.connect(settings.DB_PATH)
        except sqlite3.Error as error:
            log.error('sqlite connection error:', error)
    return globals()['__CONNECTION']


@contextlib.contextmanager
def cursor(connection: sqlite3.Connection = None):
    con = connection or _connection()
    yield con.cursor()
    con.commit()


def execute(sql, connection: 'Connection' = None):
    with cursor(connection) as cur:
        return cur.execute(sql)
