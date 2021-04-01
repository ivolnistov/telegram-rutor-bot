import logging
from os.path import dirname, join as opj
from typing import TYPE_CHECKING

import settings
from .connections import cursor


if TYPE_CHECKING:
    from sqlite3 import Connection

log = logging.getLogger(f'{settings.LOG_PREFIX}.sql')

__all__ = ('init',)


def init(connection: 'Connection'):
    with cursor(connection) as cur:
        log.info('creating database')
        with open(opj(dirname(__file__), 'schemas/schema.sql'), 'r') as f:
            cur.executescript(f.read())
        log.info('database created')
