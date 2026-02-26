from unittest.mock import AsyncMock, MagicMock

import pytest
from bs4 import BeautifulSoup

from telegram_rutor_bot.rutor.parser import (
    _determine_category,
    _is_potential_series,
    _process_torrent_item,
    _should_skip_torrent,
    parse_name,
)


def test_parse_name_variants():
    assert parse_name('Ru Name / En Name (2020)') == ('Ru Name', 'En Name', 2020)
    assert parse_name('Simple Name (2021)')[0] == 'Simple Name'


def test_should_skip_torrent_variants(mocker):
    mocker.patch('telegram_rutor_bot.rutor.parser.settings.size_limit', 1000)
    soup = BeautifulSoup('<a>name</a>', 'html.parser')
    tag = soup.a
    assert _should_skip_torrent({'size': 2000, 'torrent': tag}, [], []) is True
    assert _should_skip_torrent({'size': 500, 'torrent': tag}, ['forbidden'], []) is True


def test_determine_category_variants():
    assert _determine_category('аниме', None, 'Name') == 'CARTOONS'
    assert _determine_category(None, 'Сериалы', 'Name') == 'TVSHOWS'


def test_is_potential_series_variants():
    assert _is_potential_series('FILMS', 'боевик') is True
    assert _is_potential_series('OTHER', 'драма') is False


@pytest.mark.asyncio
async def test_process_torrent_item_simple(mocker):
    mock_session = AsyncMock()
    from datetime import date

    torrent_data = {
        'blake': 'b1',
        'torrent_lnk_blake': 'tb1',
        'name': 'Film',
        'magnet': 'mag',
        'date': date(2024, 1, 1),
        'torrent_lnk': '/t/1',
        'size': 100,
        'torrent': MagicMock(),
        'year': '2024',
    }
    torrent_data['torrent'].get_text.return_value = 'Film'

    mocker.patch('telegram_rutor_bot.rutor.parser.get_or_create_film', AsyncMock(return_value=MagicMock(id=1)))
    mocker.patch('telegram_rutor_bot.rutor.parser.add_torrent', AsyncMock())

    new = []
    await _process_torrent_item(mock_session, torrent_data, {}, new)
    assert 1 in new
