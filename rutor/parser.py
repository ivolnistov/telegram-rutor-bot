import argparse
import datetime
import locale
import logging
import pickle
import re
import sqlite3
import os
import sys
from contextlib import contextmanager
from hashlib import blake2s

from typing import List, Tuple, TYPE_CHECKING
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.exceptions import InvalidURL
from transmission_rpc import Client

import settings
from settings import DB_PATH, TRANSMISSION_HOST, TRANSMISSION_PASSWORD, TRANSMISSION_PORT, TRANSMISSION_USERNAME
from db import add_torrent, get_or_create_film, get_torrent_by_blake, get_torrent_by_magnet, modify_torrent
import db

log = logging.getLogger(f'{settings.LOG_PREFIX}.schedule')

if TYPE_CHECKING:
    from sqlite3 import Connection
    import bs4
    import models as m

UNITS = ['KB', 'MB', 'GB', 'TB', 'PB']
UNIT_LIST = zip(UNITS, [0, 0, 1, 2, 2, 2])

HEADERS = {}
PATTERN = re.compile(r'^(.*)\s+\((\d{4})\)\s+.*\s?(\|.*)?$')

FILMS = {}
TV_SHOWS = {}
IMDB_RE = re.compile(r'http://s.rutor.info/imdb/pic/[0-9]+\.gif')
KINOPOISK_RE = re.compile(r'http://www.kinopoisk.ru/rating/[0-9]+\.gif')


def _load_db():
    try:
        with open(DB_PATH, 'rb') as f:
            return pickle.load(f)
    except IOError:
        return {}


def _save_db(data):
    try:
        with open(DB_PATH, 'wb') as f:
            return pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
    except:
        pass


def size_to_bytes_converter(text):
    parts = text.split()
    if not len(parts):
        return parts[0]
    size = float(parts[0])
    unit = str.upper(parts[1])
    if size == 0.0:
        return size
    if unit not in UNITS:
        raise ValueError(f'unknown unit {unit}')
    mp = UNITS.index(unit) + 1
    return int(size * (1000 ** mp))


def _opener(url):
    proxy = getattr(settings, 'PROXY', None)
    proxies = None
    if proxy:
        proxies = {
            'http':  proxy,
            'https': proxy
        }
    return requests.get(url, proxies=proxies)


def get_torrent_node(node: str):
    for node in node.find_all('a'):
        href = node.attrs.get('href', None)
        if not href:
            continue
        if href.startswith('/torrent'):
            return node


def sanitizer(text: str):
    return text.strip()


def parse_name(text: str):
    search = PATTERN.search(text)
    parts = search.groups()
    if len(parts):
        return [*map(sanitizer, parts[0].split('/')), parts[1]]
    return parts


def get_transmission_client():
    return


def get_torrents(client):
    return client.get_torrents()


@contextmanager
def localize(cat, loc):
    yield locale.setlocale(cat, loc)
    locale.resetlocale()


def parse_rutor(url, connection: 'Connection' = None):
    # open('raw_data.html', 'wb').write(_opener(url).read())
    # data = open('raw_data.html', 'rb').read()
    try:
        data = _opener(url).text
    except InvalidURL:
        raise ValueError('invalid url ' + url)
    soup = BeautifulSoup(data, 'lxml')
    new = []
    film_cache = {}
    con = connection or db.connection()
    with localize(locale.LC_ALL, os.getenv('HTML_LOCALE', 'ru_RU.UTF-8')):
        for lnk in soup.body.find_all('a'):
            href = lnk.attrs.get('href', None)
            if not href or not href.startswith('magnet'):
                continue
            row: 'bs4.element.Tag' = lnk.parent.parent
            tds = row.findChildren('td')
            size = size_to_bytes_converter(tds[-2].get_text())
            try:
                date = datetime.datetime.strptime(tds[0].get_text(), '%d\xa0%b\xa0%y').date()
            except ValueError:
                date = datetime.datetime.now().date()
            magnet = lnk.attrs['href']
            torrent = get_torrent_node(lnk.parent)
            torrent_lnk = torrent.attrs['href']
            torrent_lnk_blake = blake2s(torrent_lnk.encode()).hexdigest()
            text = parse_name(torrent.get_text())
            year = text.pop()
            blake = blake2s(text[-1].encode()).hexdigest()
            if settings.SIZE_LIMIT and int(size) > settings.SIZE_LIMIT:
                continue
            torrent_id = get_torrent_by_blake(torrent_lnk_blake, con)
            if torrent_id:
                continue
            film_id = film_cache.get(blake, None)
            if not film_id:
                film_id, is_new = get_or_create_film(text, year, blake, con)
                film_cache[blake] = film_id
                if is_new:
                    new.append(film_id)
            try:
                add_torrent(film_id, torrent_lnk_blake, torrent.get_text(), date, magnet, torrent_lnk, size, False, False, con)
            except sqlite3.IntegrityError:
                obj = get_torrent_by_magnet(magnet, con)
                modify_torrent(
                    obj.id,
                    con,
                    film_id=film_id,
                    blake=torrent_lnk_blake,
                    name=torrent.get_text(),
                    magnet=magnet,
                    created=date,
                    link=torrent_lnk,
                    sz=size
                )
        con.commit()
        return new


def images_filter(source: str) -> bool:
    if IMDB_RE.match(source):
        return True
    if KINOPOISK_RE.match(source):
        return True
    return False


def get_torrent_info(url, download_url) -> Tuple[str, str, List[str]]:
    url = urljoin('http://rutor.info', url)
    text = _opener(url).text
    if not text:
        return 'failed to download torrent info', '', []
    soup = BeautifulSoup(text, 'lxml')
    data = soup.find('table', {
        'id': 'details'
    })
    if not data:
        log.error('parse failed: %s', text)
        return 'parse error', '', []
    data = data.findChildren('td')[1]
    start_delete = False
    for el in data.find_all():
        if hasattr(el, 'attrs') and el.attrs.get('class', None) == ['hidewrap']:
            start_delete = True
        if not start_delete:
            continue
        el.extract()
    images = [i.attrs['src'] for idx, i in enumerate(data.find_all('img')) if idx == 0 or images_filter(i.attrs['src'])]
    txt = data.get_text().rstrip()
    chars_cnt = len(txt)
    download_lnk = f'\n{download_url}'
    max_msg_len = 4096 - len(download_lnk)
    if chars_cnt > max_msg_len:
        return txt[:4092 - len(download_lnk)] + '...' + download_lnk
    return txt + '\n\n' + download_lnk, images[0], images[1:]


def download_torrent(torrent: 'm.Torrent'):
    client = Client(host=TRANSMISSION_HOST, port=TRANSMISSION_PORT, username=TRANSMISSION_USERNAME, password=TRANSMISSION_PASSWORD)
    settings = client.session_stats()
    free_space = client.free_space(settings.download_dir)
    if torrent.size >= free_space:
        return False, 'out of free space'
    return client.add_torrent(torrent.magnet)
