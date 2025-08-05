"""Simple persistent cache for film information"""

import json
import logging
from pathlib import Path
from typing import Any

from telegram_rutor_bot.config import settings

log = logging.getLogger(f'{settings.log_prefix}.cache')


class FilmInfoCache:
    """Persistent cache for film information using JSON files (Singleton)"""

    _instance: 'FilmInfoCache | None' = None

    def __new__(cls, cache_dir: str | None = None) -> 'FilmInfoCache':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, cache_dir: str | None = None):
        # Only initialize once
        if hasattr(self, '_initialized'):
            return

        if cache_dir is None:
            # Default to a cache directory in the data folder
            # In Docker, this will be /app/data/film_cache (mounted as volume)
            # In local dev, this will be next to the database file
            if settings.database_url and str(settings.database_url).startswith('postgresql://'):
                # Running in Docker with PostgreSQL
                cache_dir = '/app/data/film_cache'
            else:
                # Running locally with SQLite
                cache_dir = str(Path(settings.database_path).parent / 'film_cache')

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        log.info('Film cache initialized at %s', self.cache_dir)

    def _get_cache_path(self, key: str) -> Path:
        """Get the cache file path for a given key"""
        # Use the key as filename with .json extension
        # Replace any problematic characters
        safe_key = key.replace('/', '_').replace('\\', '_').replace(':', '_')
        return self.cache_dir / f'{safe_key}.json'

    def get(self, key: str) -> dict[str, Any] | None:
        """Get cached data for a key"""
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with cache_path.open(encoding='utf-8') as f:
                data: dict[str, Any] = json.load(f)
                log.debug('Cache hit for key: %s', key)
                return data
        except (json.JSONDecodeError, OSError) as e:
            log.error('Error reading cache for key %s: %s', key, e)
            return None

    def set(self, key: str, data: dict[str, Any]) -> None:
        """Set cache data for a key"""
        cache_path = self._get_cache_path(key)

        try:
            with cache_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                log.debug('Cache set for key: %s', key)
        except (TypeError, OSError) as e:
            log.error('Error writing cache for key %s: %s', key, e)

    def has(self, key: str) -> bool:
        """Check if a key exists in cache"""
        return self._get_cache_path(key).exists()

    def delete(self, key: str) -> None:
        """Delete a cached item"""
        cache_path = self._get_cache_path(key)

        if cache_path.exists():
            try:
                cache_path.unlink()
                log.debug('Cache deleted for key: %s', key)
            except OSError as e:
                log.error('Error deleting cache for key %s: %s', key, e)

    def clear(self) -> None:
        """Clear all cached items"""
        try:
            for cache_file in self.cache_dir.glob('*.json'):
                cache_file.unlink()
            log.info('Film cache cleared')
        except OSError as e:
            log.error('Error clearing cache: %s', e)

    def size(self) -> int:
        """Get the number of cached items"""
        return len(list(self.cache_dir.glob('*.json')))
