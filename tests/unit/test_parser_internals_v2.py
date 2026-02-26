from bs4 import BeautifulSoup

from telegram_rutor_bot.rutor.parser import _determine_category, _process_field, _should_skip_torrent, parse_name


def test_parser_helpers():
    res = {}
    _process_field('Описание', 'Text', res)
    assert res['description'] == 'Text'

    name, _, year = parse_name('Film / Orig (2024)')
    assert name == 'Film'
    assert year == 2024

    assert _determine_category(None, 'Сериалы', 'Show') == 'TVSHOWS'

    # Create mock torrent data - CAMRip should be skipped when quality filter requires BDRip
    soup = BeautifulSoup('<a>CAMRip movie</a>', 'html.parser')
    tag = soup.a
    t_data_skip = {'size': 0, 'torrent': tag}
    assert _should_skip_torrent(t_data_skip, ['bdrip'], []) is True

    # BDRip matches the quality filter, should not be skipped
    soup2 = BeautifulSoup('<a>Proper BDRip</a>', 'html.parser')
    tag2 = soup2.a
    t_data_ok = {'size': 0, 'torrent': tag2}
    assert _should_skip_torrent(t_data_ok, ['bdrip'], []) is False

    # No filters means nothing is skipped
    assert _should_skip_torrent(t_data_skip, [], []) is False
