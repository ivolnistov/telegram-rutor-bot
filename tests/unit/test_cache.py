import pytest

from telegram_rutor_bot.utils.cache import FilmInfoCache


@pytest.fixture
def temp_cache(tmp_path):
    # Reset singleton for testing
    FilmInfoCache._instance = None
    return FilmInfoCache(cache_dir=str(tmp_path))


def test_cache_get_set(temp_cache):
    key = 'test_key'
    data = {'name': 'Test Film', 'year': 2024}

    assert temp_cache.get(key) is None
    assert temp_cache.has(key) is False

    temp_cache.set(key, data)
    assert temp_cache.has(key) is True
    assert temp_cache.get(key) == data
    assert temp_cache.size() == 1


def test_cache_delete(temp_cache):
    key = 'delete_me'
    temp_cache.set(key, {'test': 1})
    assert temp_cache.size() == 1

    temp_cache.delete(key)
    assert temp_cache.get(key) is None
    assert temp_cache.size() == 0


def test_cache_clear(temp_cache):
    temp_cache.set('k1', {'v': 1})
    temp_cache.set('k2', {'v': 2})
    assert temp_cache.size() == 2

    temp_cache.clear()
    assert temp_cache.size() == 0


def test_cache_safe_key(temp_cache):
    # Test key with slashes
    key = 'path/to/item:123'
    temp_cache.set(key, {'val': 1})
    # Should not raise OSError, but create a safe filename
    assert temp_cache.get(key) == {'val': 1}
