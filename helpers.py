import re
from hashlib import blake2s
from typing import Iterable, List, TYPE_CHECKING

from db import get_torrents_by_film


if TYPE_CHECKING:
    import models as m


def gen_hash(text: str, prefix: str = None) -> str:
    return prefix or '' + blake2s(text.encode()).hexdigest()


def humanize_bytes(num, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1000.0:
            return f'{num:3.1f} {unit}{suffix}'
        num /= 1000.0
    return f'{num:.1f} Y{suffix}'


def format_films(films: Iterable['m.Film']) -> List[str]:
    messages = ['', ]
    idx = 0
    for film in films:
        text = f'{film.name} ({film.year})\n'
        for t in get_torrents_by_film(film.id):
            tn = re.sub(fr'^.*\s\({film.year}\)\s', '', t.name)
            text += f'   /dl_{t.id} /in_{t.id} {tn} {humanize_bytes(t.size)}\n'

        if len(messages[idx]) + len(text) > 4096:
            idx += 1
            messages += ['']
        messages[idx] += text

    if not messages[0]:
        messages[0] = 'Torrents list is empty'
    return messages
