import logging
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Bot
from telegram.constants import ParseMode

from telegram_rutor_bot.clients.tmdb import TmdbClient
from telegram_rutor_bot.config import settings
from telegram_rutor_bot.db import get_films_by_ids
from telegram_rutor_bot.db.models import Film, User
from telegram_rutor_bot.rutor import parse_rutor
from telegram_rutor_bot.rutor.constants import RUTOR_BASE_URL

log = logging.getLogger(__name__)


class WatchlistMonitor:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.tmdb = TmdbClient()

    async def sync_watchlist(self) -> int:
        """Syncs TMDB watchlist to local DB."""
        # Fetch both movies and TV
        movies = await self.tmdb.get_watchlist('movie')
        shows = await self.tmdb.get_watchlist('tv')

        all_items = []
        for m in movies:
            m['media_type'] = 'movie'
            all_items.append(m)
        for s in shows:
            s['media_type'] = 'tv'
            all_items.append(s)

        count = 0
        for item in all_items:
            tmdb_id = item.get('id')
            if not tmdb_id:
                continue

            # Check if exists
            result = await self.session.execute(select(Film).where(Film.tmdb_id == tmdb_id))
            film = result.scalar_one_or_none()

            if film:
                if not film.monitored:
                    film.monitored = True
                    count += 1
            else:
                # Create new monitored film
                # We need details? item from watchlist has basic info
                new_film = Film(
                    tmdb_id=tmdb_id,
                    tmdb_media_type=item.get('media_type'),
                    name=item.get('title') or item.get('name') or 'Unknown',
                    # original_name might be needed for search
                    blake=f'tmdb_{tmdb_id}',  # Placeholder blake until linked?
                    # Actually blake is for Rutor matching. If we haven't matched yet, what is blake?
                    # blake is required/non-nullable in Film model?
                    # Let's check model. Film.blake is nullable=False.
                    # Problem: We monitor items we haven't found on Rutor yet.
                    # We might need to adjust model or use dummy blake.
                    # Using "tmdb_{id}" seems safe for now.
                    year=int((item.get('release_date') or item.get('first_air_date') or '0')[:4]),
                    poster=item.get('poster_path'),
                    rating=str(item.get('vote_average')),
                    monitored=True,
                )
                self.session.add(new_film)
                count += 1

        await self.session.commit()
        return count

    async def check_monitored_items(self) -> None:
        """Search Rutor for monitored items."""

        # Get monitored films that haven't been searched recently (e.g., 4 hours)
        cutoff = datetime.now(UTC) - timedelta(hours=4)
        stmt = (
            select(Film)
            .where(Film.monitored.is_(True))
            .where((Film.last_search.is_(None)) | (Film.last_search < cutoff))
        )
        result = await self.session.execute(stmt)
        films = result.scalars().all()

        if not films:
            return

        bot = Bot(token=settings.telegram_token) if settings.telegram_token else None

        for film in films:
            log.info(f'Checking monitored film: {film.name}')
            try:
                # Construct search URL
                # Search by original title + year to be specific, or just name?
                # Using name from DB.
                query = film.name
                url = f'{RUTOR_BASE_URL}/search/0/0/0/0/{quote(query)}'

                # parse_rutor handles filtering (via settings) and DB saving
                new_ids = await parse_rutor(url, self.session, is_series=(film.tmdb_media_type == 'tv'))

                if new_ids:
                    log.info(f'Found {len(new_ids)} new items for {film.name}')
                    if bot:
                        await self._notify_users_about_found_items(bot, new_ids, film.name)

                film.last_search = datetime.now(UTC)
                await self.session.commit()

            except Exception as e:
                log.error(f'Error searching for {film.name}: {e}')

    async def _send_notification_to_all_users(self, bot: Bot, msg: str) -> None:
        """Send a single message to all registered users"""
        stmt_users = select(User)
        users_result = await self.session.execute(stmt_users)
        users = users_result.scalars().all()

        for user in users:
            if not user.chat_id:
                continue
            try:
                await bot.send_message(chat_id=user.chat_id, text=msg, parse_mode=ParseMode.HTML)
            except Exception as e:
                log.warning(f'Failed to send notification to user {user.chat_id}: {e}')

    async def _notify_users_about_found_items(self, bot: Bot, new_ids: list[int], original_name: str) -> None:
        """Notify users about new films found in search"""
        found_films = await get_films_by_ids(self.session, new_ids)
        for f in found_films:
            for torrent in f.torrents:
                msg = (
                    f'🎬 <b>Found Watchlist Item:</b> {f.name} ({f.year})\n'
                    f'💾 {torrent.name}\n'
                    f'📦 {torrent.sz / 1024 / 1024 / 1024:.2f} GB\n'
                    f"🔗 <a href='{torrent.magnet}'>Magnet</a>"
                )
                try:
                    await self._send_notification_to_all_users(bot, msg)
                except Exception as e:
                    log.error(f'Failed to notify for film {original_name}: {e}')
