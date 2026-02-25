"""Configuration API endpoints."""

import logging
import os
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy import delete, select

from telegram_rutor_bot.clients.tmdb import TmdbClient
from telegram_rutor_bot.config import SearchConfig, settings
from telegram_rutor_bot.db import get_async_session, get_or_create_user_by_chat_id
from telegram_rutor_bot.db.config_ops import get_db_config, update_db_config
from telegram_rutor_bot.db.models import AppConfigUpdate, Search
from telegram_rutor_bot.db.searches import _get_or_create_category
from telegram_rutor_bot.torrent_clients import get_torrent_client
from telegram_rutor_bot.web.auth import get_current_admin_if_configured

log = logging.getLogger(__name__)

router = APIRouter(prefix='/api/config', tags=['config'])


class ConfigCheckResponse(BaseModel):
    """Response model for configuration check."""

    configured: bool
    missing_fields: list[str] = []
    current_values: dict[str, Any] = {}
    env_vars: list[str] = []
    searches: list[SearchConfig] = []


class TorrentConfig(BaseModel):
    """Torrent client configuration model."""

    client: str = Field(..., pattern='^(qbittorrent|transmission)$')
    host: str
    port: int
    username: str
    password: str


class UserConfig(BaseModel):
    """User configuration model."""

    id: int
    username: str | None = None
    password: str | None = None
    is_tfa_enabled: bool = False
    language: str | None = 'en'


class TelegramConfig(BaseModel):
    """Telegram configuration model."""

    token: str
    initial_users: list[UserConfig] = []


class ConfigSetupRequest(BaseModel):
    """Request model for configuration setup."""

    telegram: TelegramConfig
    torrent: TorrentConfig
    tmdb_api_key: str | None = None
    tmdb_session_id: str | None = None
    seed_ratio_limit: float = 1.0
    seed_time_limit: int = 2880
    inactive_seeding_time_limit: int = 0
    seed_limit_action: int = 0  # 0 = Pause, 1 = Remove
    searches: list[SearchConfig] = []


@router.get('', response_model=ConfigCheckResponse, dependencies=[Depends(get_current_admin_if_configured)])
async def get_config() -> ConfigCheckResponse:
    """Get current configuration status and effective values."""
    async with get_async_session() as session:
        db_config = await get_db_config(session)

        stmt = select(Search).where(Search.creator_id.is_(None))
        system_searches_db = (await session.execute(stmt)).scalars().all()
        searches = [
            SearchConfig(
                name=s.query or '',
                url=s.url,
                cron=s.cron,
                category=s.category_rel.name if s.category_rel else None,
                is_series=s.is_series,
            )
            for s in system_searches_db
        ]

    # Convert DB config to dict
    current_vals: dict[str, Any] = {
        'telegram_token': db_config.telegram_token,
        'torrent_client': db_config.torrent_client,
        'qbittorrent_host': db_config.qbittorrent_host,
        'qbittorrent_port': db_config.qbittorrent_port,
        'qbittorrent_username': db_config.qbittorrent_username,
        'transmission_port': db_config.transmission_port,
        'transmission_username': db_config.transmission_username,
        'tmdb_api_key': db_config.tmdb_api_key,
        'tmdb_session_id': db_config.tmdb_session_id,
    }

    # Fetch live limits from qBittorrent
    try:
        client = get_torrent_client()
        await client.connect()
        prefs = await client.get_app_preferences()

        # specific handling for qBittorrent keys
        # max_ratio is float, others are int (minutes)
        current_vals['seed_ratio_limit'] = float(prefs.get('max_ratio', -1))
        current_vals['seed_time_limit'] = int(prefs.get('max_seeding_time', -1))
        current_vals['inactive_seeding_time_limit'] = int(prefs.get('max_inactive_seeding_time', -1))
        current_vals['seed_limit_action'] = int(prefs.get('max_ratio_act', 0))
        await client.disconnect()
    except Exception as e:
        log.warning('Failed to fetch qBittorrent preferences: %s', e)
        # Fallback to sensible defaults or -1 to indicate error/unknown
        current_vals['seed_ratio_limit'] = -1
        current_vals['seed_time_limit'] = -1
        current_vals['inactive_seeding_time_limit'] = -1
        current_vals['seed_limit_action'] = 0

    # Store raw passwords to check against env, then mask
    q_pass = db_config.qbittorrent_password
    t_pass = db_config.transmission_password
    current_vals['qbittorrent_password'] = '***' if q_pass else ''
    current_vals['transmission_password'] = '***' if t_pass else ''

    # Identify Env Var overrides (Locked fields)
    env_vars = []
    if 'RUTOR_BOT_TELEGRAM_TOKEN' in os.environ:
        env_vars.append('telegram_token')
        current_vals['telegram_token'] = settings.telegram_token

    if 'RUTOR_BOT_QBITTORRENT_HOST' in os.environ:
        env_vars.append('qbittorrent_host')
        current_vals['qbittorrent_host'] = settings.qbittorrent_host
    if 'RUTOR_BOT_QBITTORRENT_PORT' in os.environ:
        env_vars.append('qbittorrent_port')
        current_vals['qbittorrent_port'] = settings.qbittorrent_port
    if 'RUTOR_BOT_QBITTORRENT_USERNAME' in os.environ:
        env_vars.append('qbittorrent_username')
        current_vals['qbittorrent_username'] = settings.qbittorrent_username
    if 'RUTOR_BOT_QBITTORRENT_PASSWORD' in os.environ:
        env_vars.append('qbittorrent_password')
        current_vals['qbittorrent_password'] = '***'

    missing = []
    if not current_vals.get('telegram_token'):
        missing.append('telegram_token')

    is_configured = bool(current_vals.get('telegram_token'))

    # System searches already fetched from DB

    return ConfigCheckResponse(
        configured=is_configured,
        missing_fields=missing,
        current_values=current_vals,
        env_vars=env_vars,
        searches=searches,
    )


@router.post('', response_model=ConfigCheckResponse, dependencies=[Depends(get_current_admin_if_configured)])
async def save_config(config: ConfigSetupRequest) -> ConfigCheckResponse:  # noqa: PLR0912,PLR0915
    """Save configuration to Database and initialize users."""

    updates = {
        'is_configured': True,
        'telegram_token': config.telegram.token,
    }

    updates.update(
        {
            'qbittorrent_host': config.torrent.host,
            'qbittorrent_port': config.torrent.port,
            'qbittorrent_username': config.torrent.username,
            'qbittorrent_password': config.torrent.password,
        }
    )

    if config.tmdb_api_key:
        updates['tmdb_api_key'] = config.tmdb_api_key
    if config.tmdb_session_id:
        updates['tmdb_session_id'] = config.tmdb_session_id

    # Save to DB
    async with get_async_session() as session:
        # Cast to AppConfigUpdate to satisfy mypy
        config_updates = cast(AppConfigUpdate, updates)
        await update_db_config(session, **config_updates)

        # Init Users
        if config.telegram.initial_users:
            for user_data in config.telegram.initial_users:
                try:
                    user = await get_or_create_user_by_chat_id(session, user_data.id)
                    user.is_authorized = True
                    user.is_admin = True
                    if user_data.username:
                        user.username = user_data.username
                    if user_data.password:
                        user.password = user_data.password
                    if user_data.is_tfa_enabled:
                        user.is_tfa_enabled = True
                    if user_data.language:
                        user.language = user_data.language
                except Exception as e:
                    log.error('Failed to init user %s: %s', user_data.id, e)
            await session.commit()

    # Save system searches to DB instead of config.toml
    async with get_async_session() as session:
        await session.execute(delete(Search).where(Search.creator_id.is_(None)))

        for idx, s in enumerate(config.searches):
            category_id = None
            if s.category:
                cat_obj = await _get_or_create_category(session, s.category)
                category_id = cat_obj.id

            db_search = Search(
                url=s.url,
                cron=s.cron,
                creator_id=None,
                query=s.name or f'System Search {idx + 1}',
                category_id=category_id,
                is_series=s.is_series,
            )
            session.add(db_search)
        await session.commit()

    settings.searches = config.searches

    # Trigger Reload (In-process)
    settings.refresh(**cast(AppConfigUpdate, updates))

    # Save preferences to qBittorrent
    try:
        client = get_torrent_client()
        await client.connect()

        prefs = {
            'max_ratio': config.seed_ratio_limit,
            'max_seeding_time': config.seed_time_limit,
            'max_inactive_seeding_time': config.inactive_seeding_time_limit,
            'max_ratio_act': config.seed_limit_action,
        }
        await client.set_app_preferences(prefs)
        await client.disconnect()
    except Exception as e:
        log.error('Failed to save qBittorrent preferences: %s', e)
        # We don't fail the request, but logging is important

    # Trigger Reload (In-process)
    settings.refresh(**cast(AppConfigUpdate, updates))

    # Trigger Reload (Cluster)
    if settings.redis_url:
        try:
            redis = Redis.from_url(settings.redis_url)
            await redis.publish('config_reload', 'reload')
            await redis.close()
        except Exception as e:
            log.error('Failed to publish config reload: %s', e)

    return ConfigCheckResponse(configured=True)


class TmdbAuthResponse(BaseModel):
    auth_url: str


class TmdbSessionRequest(BaseModel):
    request_token: str


@router.get('/tmdb/auth-url', response_model=TmdbAuthResponse, dependencies=[Depends(get_current_admin_if_configured)])
async def get_tmdb_auth_url(redirect_to: str) -> TmdbAuthResponse:
    """Get TMDB authentication URL."""
    tmdb = TmdbClient()

    token = await tmdb.create_request_token()
    if not token:
        # If API key is missing or invalid
        raise HTTPException(status_code=500, detail='Failed to create request token (Check API Key)')

    return TmdbAuthResponse(auth_url=f'https://www.themoviedb.org/authenticate/{token}?redirect_to={redirect_to}')


@router.post(
    '/tmdb/session', response_model=ConfigCheckResponse, dependencies=[Depends(get_current_admin_if_configured)]
)
async def create_tmdb_session(request: TmdbSessionRequest) -> ConfigCheckResponse:
    """Create TMDB session from approved token."""
    tmdb = TmdbClient()

    session_id = await tmdb.create_session_id(request.request_token)
    if not session_id:
        raise HTTPException(status_code=400, detail='Failed to create session ID')

    # Update DB
    async with get_async_session() as session:
        # Cast to AppConfigUpdate to satisfy mypy
        config_updates = cast(AppConfigUpdate, {'tmdb_session_id': session_id})
        await update_db_config(session, **config_updates)

    # Trigger Reloads
    settings.refresh(tmdb_session_id=session_id)

    if settings.redis_url:
        try:
            redis = Redis.from_url(settings.redis_url)
            await redis.publish('config_reload', 'reload')
            await redis.close()
        except Exception:
            pass

    return await get_config()


class SearchFilters(BaseModel):
    quality: str | None = None
    translation: str | None = None


@router.get('/filters', dependencies=[Depends(get_current_admin_if_configured)])
async def get_filters() -> SearchFilters:
    """Get search filters."""
    async with get_async_session() as session:
        config = await get_db_config(session)
        return SearchFilters(
            quality=config.search_quality_filters,
            translation=config.search_translation_filters,
        )


@router.post('/filters', dependencies=[Depends(get_current_admin_if_configured)])
async def update_filters(filters: SearchFilters) -> dict[str, str]:
    """Update search filters."""
    async with get_async_session() as session:
        await update_db_config(
            session,
            search_quality_filters=filters.quality,
            search_translation_filters=filters.translation,
        )
    return {'status': 'success'}
