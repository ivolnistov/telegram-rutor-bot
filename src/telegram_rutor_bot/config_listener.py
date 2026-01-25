"""Configuration reload listener and sync logic."""

import logging
import os
from typing import Any

from redis.asyncio import Redis

from telegram_rutor_bot.config import settings
from telegram_rutor_bot.db import get_async_session
from telegram_rutor_bot.db.config_ops import get_db_config

log = logging.getLogger(__name__)


async def refresh_settings_from_db() -> None:
    """Fetch configuration from DB and update global settings."""
    try:
        async with get_async_session() as session:
            db_config = await get_db_config(session)

            updates: dict[str, Any] = {}
            updates['is_configured'] = db_config.is_configured

            if db_config.telegram_token:
                updates['telegram_token'] = db_config.telegram_token
            if db_config.unauthorized_message:
                updates['unauthorized_message'] = db_config.unauthorized_message

            updates['torrent_client'] = db_config.torrent_client

            updates['qbittorrent_host'] = db_config.qbittorrent_host
            updates['qbittorrent_port'] = db_config.qbittorrent_port
            updates['qbittorrent_username'] = db_config.qbittorrent_username
            if db_config.qbittorrent_password:
                updates['qbittorrent_password'] = db_config.qbittorrent_password

            updates['transmission_host'] = db_config.transmission_host
            updates['transmission_port'] = db_config.transmission_port
            if db_config.transmission_username:
                updates['transmission_username'] = db_config.transmission_username
            if db_config.transmission_password:
                updates['transmission_password'] = db_config.transmission_password

            if db_config.proxy:
                updates['proxy'] = db_config.proxy

            updates['seed_ratio_limit'] = db_config.seed_ratio_limit
            updates['seed_time_limit'] = db_config.seed_time_limit
            updates['inactive_seeding_time_limit'] = db_config.inactive_seeding_time_limit

            if db_config.tmdb_api_key:
                updates['tmdb_api_key'] = db_config.tmdb_api_key
            if db_config.tmdb_session_id:
                updates['tmdb_session_id'] = db_config.tmdb_session_id

            # Respect Env Vars (Locking)
            # Pydantic Settings usually handles this priority (Env > File).
            # But here we are overwriting manually.
            # We must NOT overwrite if Env Var is present.

            def apply_if_no_env(field: str, env_var: str) -> None:
                if env_var not in os.environ and field in updates:
                    # No op needed since 'updates' has new value, just ensure we don't accidentally ignore env
                    pass
                elif env_var in os.environ:
                    # Env var is present, remove from updates
                    # (assuming current 'settings' already has env var value loaded at startup)
                    # BUT if 'settings' was modified strictly in-memory?
                    # Pydantic BaseSettings loads env vars once.
                    # We should probably trust that 'settings' has the env var value.
                    updates.pop(field, None)

            apply_if_no_env('telegram_token', 'RUTOR_BOT_TELEGRAM_TOKEN')
            apply_if_no_env('torrent_client', 'RUTOR_BOT_TORRENT_CLIENT')

            # ... repeat for all ...
            # Actually, simpler:
            # If we update 'settings' in-place, we are mutating it.
            # If we want to respect Env, we should check before mutating.

            # Map of Field -> EnvVar
            env_map = {
                'telegram_token': 'RUTOR_BOT_TELEGRAM_TOKEN',
                'torrent_client': 'RUTOR_BOT_TORRENT_CLIENT',
                'qbittorrent_host': 'RUTOR_BOT_QBITTORRENT_HOST',
                'qbittorrent_port': 'RUTOR_BOT_QBITTORRENT_PORT',
                'qbittorrent_username': 'RUTOR_BOT_QBITTORRENT_USERNAME',
                'qbittorrent_password': 'RUTOR_BOT_QBITTORRENT_PASSWORD',
                'transmission_host': 'RUTOR_BOT_TRANSMISSION_HOST',
                'transmission_port': 'RUTOR_BOT_TRANSMISSION_PORT',
                'transmission_username': 'RUTOR_BOT_TRANSMISSION_USERNAME',
                'transmission_password': 'RUTOR_BOT_TRANSMISSION_PASSWORD',
                'proxy': 'RUTOR_BOT_PROXY',
                'seed_ratio_limit': 'RUTOR_BOT_SEED_RATIO_LIMIT',
                'seed_time_limit': 'RUTOR_BOT_SEED_TIME_LIMIT',
                'inactive_seeding_time_limit': 'RUTOR_BOT_INACTIVE_SEEDING_TIME_LIMIT',
            }

            final_updates = {}
            for k, v in updates.items():
                env_key = env_map.get(k)
                if env_key and env_key in os.environ:
                    continue
                final_updates[k] = v

            settings.refresh(**final_updates)
            log.info('Settings refreshed from DB')

    except Exception as e:  # pylint: disable=broad-exception-caught
        log.error('Failed to refresh settings from DB: %s', e)


async def config_listener_task() -> None:
    """Background task to listen for config reload events."""
    if not settings.redis_url:
        log.warning('No Redis URL configured, config reload listener disabled')
        return

    try:
        redis = Redis.from_url(settings.redis_url)
        pubsub = redis.pubsub()
        await pubsub.subscribe('config_reload')

        log.info('Started config reload listener')

        async for message in pubsub.listen():
            if message['type'] == 'message':
                log.info('Received config reload signal')
                await refresh_settings_from_db()
    except Exception as e:  # pylint: disable=broad-exception-caught
        log.error('Config listener failed: %s', e)
        # Retry logic? For now let it crash/log
