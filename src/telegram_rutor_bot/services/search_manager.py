"""Service for managing searches and syncing with configuration"""

import logging
from datetime import UTC, datetime

from sqlalchemy import select

from telegram_rutor_bot.config import settings
from telegram_rutor_bot.db import get_async_session
from telegram_rutor_bot.db.models import Search

log = logging.getLogger(__name__)


def _substitute_variables(url: str) -> str:
    """Substitute variables in URL with current date values"""
    now = datetime.now(UTC)

    replacements = {
        '{year}': str(now.year),
        '{prev_year}': str(now.year - 1),
        '{next_year}': str(now.year + 1),
        '{month}': f'{now.month:02d}',
        '{prev_month}': f'{(now.month - 2) % 12 + 1:02d}',
        '{next_month}': f'{(now.month % 12 + 1):02d}',
        '{day}': f'{now.day:02d}',
    }

    result = url
    for key, value in replacements.items():
        result = result.replace(key, value)

    return result


async def sync_system_searches() -> None:
    """Sync system-defined searches from config to database"""
    if not settings.searches:
        log.info('No system searches defined in config.')
        return

    log.info('Syncing %d system searches...', len(settings.searches))

    async with get_async_session() as session:
        for search_cfg in settings.searches:
            url = _substitute_variables(search_cfg.url)

            # Check if search exists by URL (or maybe by name if we stored it?)
            # Since we don't have a 'name' field in Search model yet, we'll just check URL
            # But wait, if URL changes due to variable substitution (e.g. year), we might create duplicates
            # if we don't identify them by some stable ID.
            # However, for now, let's just ensure this URL exists.

            stmt = select(Search).where(Search.url == url)
            existing = (await session.execute(stmt)).scalars().first()

            if not existing:
                log.info('Creating system search: %s (%s)', search_cfg.name, url)
                new_search = Search(
                    url=url,
                    cron=search_cfg.cron,
                    query=search_cfg.name,  # Store name in query field for identification?
                    creator_id=None,  # System search
                )
                session.add(new_search)
            # Update cron if changed
            elif existing.cron != search_cfg.cron:
                existing.cron = search_cfg.cron
                session.add(existing)

        await session.commit()
