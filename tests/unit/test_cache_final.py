import pytest
from pathlib import Path
from telegram_rutor_bot.utils.cache import FilmInfoCache

def test_cache_file_lifecycle(tmp_path):
    cache = FilmInfoCache(cache_dir=str(tmp_path))
    
    # set
    cache.set("k1", {"a": 1})
    assert cache.has("k1") is True
    
    # get
    assert cache.get("k1") == {"a": 1}
    
    # delete
    cache.delete("k1")
    assert cache.has("k1") is False
    assert cache.get("k1") is None
    
    # clear
    cache.set("k2", {"b": 2})
    cache.clear()
    assert cache.size() == 0

def test_cache_invalid_file(tmp_path):
    cache = FilmInfoCache(cache_dir=str(tmp_path))
    path = Path(tmp_path) / "invalid.json"
    path.write_text("invalid{")
    
    # Should handle error and return None
    assert cache.get("invalid") is None
