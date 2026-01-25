"""Database module with SQLAlchemy models and operations"""

# Database initialization and session management
from .database import get_async_db, get_async_session, init_db

# Film operations
from .films import (
    get_films,
    get_films_by_ids,
    get_or_create_film,
    get_recommendations,
    search_films,
    update_film_metadata,
)
from .models import Base, Film, Search, Torrent, User

# Search operations
from .searches import (
    add_search_to_db,
    create_category,
    delete_category,
    delete_search,
    get_categories,
    get_search,
    get_search_subscribers,
    get_searches,
    get_searches_by_user,
    get_subscribed_searches,
    update_category,
    update_last_success,
    update_search,
)

# Subscription operations
from .subscriptions import get_subscriptions, is_subscribed, subscribe, unsubscribe

# Torrent operations
from .torrents import (
    add_torrent,
    get_recent_torrents,
    get_torrent_by_blake,
    get_torrent_by_id,
    get_torrent_by_magnet,
    get_torrents,
    get_torrents_by_film,
    mark_torrent_downloaded,
    modify_torrent,
    search_torrents,
)

# User operations
from .users import (
    get_all_users,
    get_or_create_user_by_chat_id,
    get_user,
    get_user_by_chat,
    grant_access,
    set_user_language,
    update_user_info,
)

__all__ = [
    'Base',
    'Film',
    'Search',
    'Torrent',
    'User',
    'add_search_to_db',
    'add_torrent',
    'create_category',
    'delete_category',
    'delete_search',
    'get_all_users',
    'get_async_db',
    'get_async_session',
    'get_categories',
    'get_films',
    'get_films_by_ids',
    'get_or_create_film',
    'get_or_create_user_by_chat_id',
    'get_recent_torrents',
    'get_recommendations',
    'get_search',
    'get_search_subscribers',
    'get_searches',
    'get_searches_by_user',
    'get_subscribed_searches',
    'get_subscriptions',
    'get_torrent_by_blake',
    'get_torrent_by_id',
    'get_torrent_by_magnet',
    'get_torrents',
    'get_torrents_by_film',
    'get_user',
    'get_user_by_chat',
    'grant_access',
    'init_db',
    'is_subscribed',
    'mark_torrent_downloaded',
    'modify_torrent',
    'search_films',
    'search_torrents',
    'set_user_language',
    'subscribe',
    'unsubscribe',
    'update_category',
    'update_film_metadata',
    'update_last_success',
    'update_search',
    'update_user_info',
]
