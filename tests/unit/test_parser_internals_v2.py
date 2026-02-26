import pytest
from unittest.mock import MagicMock
from telegram_rutor_bot.rutor.parser import (
    _process_field,
    parse_name,
    _determine_category,
    _should_skip_torrent
)

def test_parser_helpers():
    res = {}
    _process_field("Описание", "Text", res)
    assert res["description"] == "Text"
    
    name, _, year = parse_name("Film / Orig (2024)")
    assert name == "Film"
    assert year == 2024
    
    assert _determine_category(None, "Сериалы", "Show") == 'TVSHOWS'
    
    # signature: _should_skip_torrent(torrent_name, t_filters)
    assert _should_skip_torrent("CAMRip movie", []) is True
    assert _should_skip_torrent("Proper BDRip", []) is False
