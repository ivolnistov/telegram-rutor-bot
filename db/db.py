import settings
import logging
from os.path import dirname, join as opj

import settings
from .connections import cursor


log = logging.getLogger(f'{settings.LOG_PREFIX}.sql')

__all__ = ('init',)


def init():
    with cursor() as cur:
        log.info('creating database')
        with open(opj(dirname(__file__), 'schemas/schema.sql'), 'r') as f:
            cur.executescript(f.read())
        log.info('database created')
