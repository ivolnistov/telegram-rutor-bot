from typing import Optional, TYPE_CHECKING, Tuple


if TYPE_CHECKING:
    from datetime import datetime
__all__ = ('Film', 'Torrent',)


class Film:
    name: str
    blake: str
    year: int
    crete: Optional['datetime.date']

    def __init__(self, id, blake, year, name, created=None):
        self.id = id
        self.blake = blake
        self.year = year
        self.name = name
        self.created = created

    def __str__(self):
        return self.name


class Torrent:
    id: int
    film_id: int
    blake: str
    name: str
    magnet: str
    created: 'datetime.date'
    link: str
    size: int
    approved: bool
    downloaded: bool

    def __init__(self, id, film_id, blake, name, magnet, created, link, size, approved=False, downloaded=False):
        self.id = id
        self.film_id = film_id
        self.blake = blake
        self.name = name
        self.magnet = magnet
        self.created = created
        self.link = link
        self.size = int(size)
        self.approved = approved
        self.downloaded = downloaded

    def __str__(self):
        return self.name

    def __lt__(self, other):
        if isinstance(other, Torrent):
            return self.size < other.size
        return False

    def __gt__(self, other):
        if isinstance(other, Torrent):
            return self.size > other.size
        return False

    def __eq__(self, other):
        if isinstance(other, Torrent):
            return self.id > other.id
        return False


class Search:
    id: int
    url: str
    cron: Tuple[str]
    creator_id: int

    def __init__(self, id: int, url: str, cron: str, creator_id: int):
        self.id = id
        self.url = url
        self.creator_id = creator_id
        cron_ = tuple(cron.split(' '))
        if len(cron_) != 5:
            raise ValueError('Invalid cron')
        self.cron = cron_

    def __str__(self):
        return self.url


class User:
    id: int
    chat_id: int

    def __init__(self, id: int, chat_id: int):
        self.id = id
        self.chat_id = chat_id
