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

            updates: dict[str, Any] = {'is_configured': db_config.is_configured}
            fields_to_check = [
                'telegram_token',
                'unauthorized_message',
                'torrent_client',
                'qbittorrent_host',
                'qbittorrent_port',
                'qbittorrent_username',
                'qbittorrent_password',
                'transmission_host',
                'transmission_port',
                'transmission_username',
                'transmission_password',
                'proxy',
                'seed_ratio_limit',
                'seed_time_limit',
                'inactive_seeding_time_limit',
                'tmdb_api_key',
                'tmdb_session_id',
            ]
            for field in fields_to_check:
                val = getattr(db_config, field, None)
                if val is not None:
                    updates[field] = val

            # Respect Env Vars (Locking)
            # Pydantic Settings usually handles this priority (Env > File).
            # But here we are overwriting manually.
            # We must NOT overwrite if Env Var is present.

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
