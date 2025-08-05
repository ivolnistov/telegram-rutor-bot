"""Map movie genres to qBittorrent categories"""

from telegram_rutor_bot.config import settings


def map_genre_to_category(genre: str | None) -> str | None:
    """Map movie genre to qBittorrent category based on configuration

    Based on user's categories: FILMS, TVSHOWS, CARTOONS
    """
    if not genre:
        return None

    genre_lower = genre.lower()

    # Check each configured category
    for category, keywords in dict(settings.genre_mapping).items():
        if any(keyword.lower() in genre_lower for keyword in keywords):
            return category

    # Everything else is FILMS
    return 'FILMS'


def detect_category_from_title(title: str | None) -> str | None:
    """Try to detect category from torrent title if genre is not available"""
    if not title:
        return None

    title_lower = title.lower()

    # Check for cartoons first (they can also have season patterns like S01)
    cartoon_patterns = dict(settings.title_patterns).get('CARTOONS', [])
    if any(pattern.lower() in title_lower for pattern in cartoon_patterns):
        return 'CARTOONS'

    # Then check for TV shows
    tvshow_patterns = dict(settings.title_patterns).get('TVSHOWS', [])
    if any(pattern.lower() in title_lower for pattern in tvshow_patterns):
        return 'TVSHOWS'

    # Default to FILMS
    return 'FILMS'


def map_rutor_category(rutor_category: str | None) -> str | None:
    """Map rutor category to qBittorrent category"""
    if not rutor_category:
        return None

    category_lower = rutor_category.lower()

    # Common rutor categories mapping
    if any(word in category_lower for word in ['мультфильм', 'мультсериал', 'анимация', 'детские']):
        return 'CARTOONS'
    if any(word in category_lower for word in ['сериал', 'тв', 'tv']):
        return 'TVSHOWS'
    if any(word in category_lower for word in ['фильм', 'кино', 'movie']):
        return 'FILMS'

    # Try to use genre mapping as fallback
    return map_genre_to_category(rutor_category)
