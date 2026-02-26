from datetime import UTC, datetime

from bs4 import BeautifulSoup

from telegram_rutor_bot.rutor.parser import (
    _determine_category,
    _is_potential_series,
    _should_skip_torrent,
    get_torrent_node,
    parse_name,
    size_to_bytes_converter,
)


def test_parse_name_detailed():
    assert parse_name('Film (2020) 1080p') == ('Film', None, 2020)
    current_year = datetime.now(UTC).year
    assert parse_name('Only Name') == ('Only Name', None, current_year)


def test_get_torrent_node_fail():
    soup = BeautifulSoup('<div><p>No link</p></div>', 'html.parser')
    assert get_torrent_node(soup.div) is None


def test_size_to_bytes_converter_cases():
    assert size_to_bytes_converter('1.5 GB') == int(1.5 * 1024 * 1024 * 1024)
    assert size_to_bytes_converter('500 MB') == 500 * 1024 * 1024
    assert size_to_bytes_converter('100 KB') == 100 * 1024
    assert size_to_bytes_converter('invalid') == 0


def test_should_skip_torrent(mocker):
    soup = BeautifulSoup('<a>torrent 1080p lostfilm</a>', 'html.parser')
    tag = soup.a

    # Mock settings.size_limit - making sure it is not skipped by size
    mocker.patch('telegram_rutor_bot.rutor.parser.settings.size_limit', 5000)

    # Matches filters - should NOT be skipped (return False)
    # filters are lowercased in the function? No, let's check.
    # any(f in full_name for f in q_filters)
    # full_name is tag.get_text().lower()
    assert _should_skip_torrent({'size': 1000, 'torrent': tag}, ['1080p'], ['lostfilm']) is False

    # Too large - should be skipped (return True)
    assert _should_skip_torrent({'size': 6000, 'torrent': tag}, [], []) is True


def test_determine_category():
    assert _determine_category('Action', 'Фильмы', 'Matrix') == 'FILMS'


def test_is_potential_series():
    assert _is_potential_series('FILMS', 'драма') is True
    assert _is_potential_series('SERIES', 'драма') is False
