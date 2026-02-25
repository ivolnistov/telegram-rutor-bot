"""TaskIQ tasks for scheduled jobs"""

import contextlib
import logging
import traceback
from datetime import UTC, datetime

from croniter import croniter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Bot
from telegram import error as telegram_error
from telegram.constants import ParseMode

from telegram_rutor_bot.config import settings
from telegram_rutor_bot.db import (
    delete_search,
    get_async_session,
    get_films_by_ids,
    get_search,
    get_search_subscribers,
    get_searches,
    get_user,
    update_last_success,
)
from telegram_rutor_bot.db.models import Film, Search, TaskExecution, User, subscribes_table
from telegram_rutor_bot.helpers import format_films
from telegram_rutor_bot.rutor import parse_rutor
from telegram_rutor_bot.schemas import Notification
from telegram_rutor_bot.services.watchlist import check_matches
from telegram_rutor_bot.torrent_clients import get_torrent_client

from .broker import broker

log = logging.getLogger(f'{settings.log_prefix}.tasks')


async def _resolve_search_task(
    session: AsyncSession,
    search_id: int,
    execution_id: int | None,
    bot: Bot,
    requester_chat_id: int | None,
) -> TaskExecution | None:
    if execution_id:
        task = await session.get(TaskExecution, execution_id)
        if task and task.status == 'cancelled':
            log.info('Task %s cancelled', execution_id)
            if requester_chat_id:
                with contextlib.suppress(Exception):
                    await bot.send_message(requester_chat_id, '❌ Task was cancelled')
            return None
        if task:
            task.status = 'running'
            return task

    stmt = (
        select(TaskExecution)
        .where(
            TaskExecution.search_id == search_id,
            TaskExecution.status == 'pending',
        )
        .order_by(TaskExecution.id.desc())
    )
    task = (await session.execute(stmt)).scalars().first()

    if task:
        task.status = 'running'
        return task

    stmt_running = select(TaskExecution).where(
        TaskExecution.search_id == search_id,
        TaskExecution.status == 'running',
    )
    if (await session.execute(stmt_running)).scalars().first():
        log.warning('Search %s is already running. Skipping.', search_id)
        return None

    task = TaskExecution(search_id=search_id, status='running')
    session.add(task)
    return task


async def _run_search_process(session: AsyncSession, task: TaskExecution, search_id: int) -> str:
    search = await get_search(session, search_id)
    if not search:
        return 'Search not found'

    task.progress = 10
    await session.commit()

    async def update_progress(percent: int) -> None:
        task.progress = percent
        await session.commit()

    # Parse dynamic variables in URL
    current_year = datetime.now(UTC).year
    resolved_url = search.url.replace('{year}', str(current_year))

    new = await parse_rutor(
        resolved_url,
        session,
        category_id=search.category_id,
        progress_callback=update_progress,
    )

    # Passive Search: Check new torrents against watchlist
    if new:
        try:
            # Fetch full Torrent objects since parse_rutor returns IDs.
            films = await get_films_by_ids(session, new)
            new_torrents = []
            for f in films:
                new_torrents.extend(f.torrents)

            await check_matches(session, new_torrents)

        except Exception as e:
            log.exception('Passive watchlist check failed: %s', e)

    task.progress = 90
    await session.commit()
    await update_last_success(session, search_id)

    result_details = f'Found {len(new)} new items.'
    if new:
        stmt_subs = select(User).join(subscribes_table).where(subscribes_table.c.search_id == search_id)
        subscribers = (await session.execute(stmt_subs)).scalars().all()
        subscriber_names = [u.username or str(u.chat_id) for u in subscribers]

        if subscriber_names:
            result_details += f'<br>Notified {len(subscriber_names)} users: {", ".join(subscriber_names)}'
        else:
            result_details += '<br>No subscribers to notify.'

        await notify_subscribers(search_id, new)

    return result_details


@broker.task
async def send_digest() -> None:
    """Send daily digest of downloaded movies"""
    log.info('Checking for downloaded movies to notify...')

    # Check if it's time to run (if we run this task frequently, e.g. hourly)
    # But if we schedule it via cron in main.py or broker, we assume it runs at correct time.
    # The broker decorator just defines the task.
    # The scheduling happens in main.py via taskiq-scheduler or here via @broker.task(schedule)
    # Since we want dynamic schedule from settings, we might need to rely on static cron for now
    # or handle the logic "is it time?" here if we run it often.
    # Let's assume we run this every hour and check if "now" matches "settings.notification_cron".
    # OR: simpler, just define the task here, and we will rely on a static schedule "every hour"?
    # User said "time we set in settings".
    # Let's use croniter to check if we mark it as "run now" logic?
    # NO. Let's just run it every hour, and if the hour matches the config, we send?
    # Or better: "send_digest" task checks matches.

    # Wait, the prompt says "run at settings.notification_time".
    # If I put `@broker.task` without schedule, I need to schedule it elsewhere.
    # If I put `@broker.task(schedule=[{'cron': '...'}])`, it's hardcoded.
    # I will stick to running it periodically (e.g. hourly) and checking:
    # "Are there any unnotified downloaded films?"
    # If yes -> Check if current time >= notification_time (or match cron).
    # Actually, simpler:
    # Just check for unnotified films. If user wants a Digest, they probably want it at specific time.
    # But if I can't dynamically schedule easily without restarting,
    # I'll check "is current hour == notification hour".

    # For now, let's implement the logic to send.

    async with get_async_session() as session:
        # Get downloaded but not notified films
        stmt = select(Film).where(Film.watch_status == 'downloaded', Film.notified == False)  # noqa: E712
        films = (await session.execute(stmt)).scalars().all()

        if not films:
            return

        # Check time constraint if we want strict "Digest Time"
        # Parse settings.notification_cron
        # Default '0 21 * * *' -> 21:00.
        # If we run this every hour, we check: does cron match previous hour?
        # A bit complex.
        # Let's just implement the "Sending" part and we'll handle scheduling via @broker.task logic below
        # assuming we passed the check.

        log.info('Found %d unnotified downloaded films', len(films))

        msg = '🎥 <b>Daily Digest: Downloaded Movies</b>\n\n'
        for film in films:
            msg += f'✅ <b>{film.name}</b>\n'
            film.notified = True

        await session.commit()

        token = settings.telegram_token
        if token:
            bot = Bot(token=token)
            # Notify authorized users
            stmt_users = select(User).where(User.is_authorized == True, User.chat_id.is_not(None))  # noqa: E712
            users = (await session.execute(stmt_users)).scalars().all()
            for user in users:
                with contextlib.suppress(Exception):
                    await bot.send_message(user.chat_id, msg, parse_mode=ParseMode.HTML)


# Schedule digest based on config?
# We can't easily dynamically bind schedule in decorator.
# Workaround: Run every minute/hour, check if cron matches.
@broker.task(schedule=[{'cron': '* * * * *'}])
async def digest_scheduler() -> None:
    if croniter.match(settings.notification_cron, datetime.now(UTC)):
        await send_digest.kiq()


@broker.task
async def execute_search(
    search_id: int,
    requester_chat_id: int | None = None,
    execution_id: int | None = None,
) -> None:
    """Execute a search and optionally notify the requester"""
    log.info('Executing search %s', search_id)
    token = settings.telegram_token
    if not token:
        log.error('Telegram token not set, cannot execute search %s', search_id)
        return

    bot = Bot(token=token)

    async with get_async_session() as session:
        task = await _resolve_search_task(session, search_id, execution_id, bot, requester_chat_id)
        if not task:
            return

        await session.commit()

        # 2. Execute
        try:
            result = await _run_search_process(session, task, search_id)
            if result == 'Search not found':
                task.status = 'failed'
                task.result = result
                await _notify_requester(bot, requester_chat_id, f'Search {search_id} not found')
            else:
                task.status = 'success'
                task.result = result
                task.progress = 100
                await _notify_requester(
                    bot, requester_chat_id, f'✅ Search executed successfully. {result.replace("<br>", " ")}'
                )

        except (ValueError, ConnectionError) as e:
            log.exception('Search %s failed: %s', search_id, e)
            task.status = 'failed'
            task.result = str(e)
            tb_str = ''.join(traceback.format_tb(e.__traceback__))
            await _notify_requester(bot, requester_chat_id, f'❌ Search failed:\n{e!s}\n\nTraceback:\n{tb_str}')

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Generic error handling
            log.exception('Unexpected error: %s', e)
            task.status = 'failed'
            task.result = f'Unexpected: {e!s}'
            tb_str = ''.join(traceback.format_tb(e.__traceback__))
            await _notify_requester(bot, requester_chat_id, f'❌ Search failed:\n{e!s}\n\nTraceback:\n{tb_str}')

        task.end_time = datetime.now(UTC)
        await session.commit()


@broker.task
async def search_film_on_rutor(
    film_id: int,
    query: str,
    requester_chat_id: int | None = None,  # pylint: disable=unused-argument
) -> None:
    """Execute a search for a specific film on Rutor"""
    log.info('Executing film search for film %s with query "%s"', film_id, query)

    # Construct Rutor URL
    # We need a proper URL construction logic.
    # Usually it is http://rutor.info/search/0/0/000/0/{query}
    safe_query = query.replace(' ', '+')  # simple encoding
    url = f'http://rutor.info/search/0/0/000/0/{safe_query}'

    async with get_async_session() as session:
        try:
            # We don't track this as a "Search" entity in DB (which is for subscribed searches),
            # but we could track it as a TaskExecution if we had a generic task model.
            # For now, just run it.

            new_ids = await parse_rutor(url, session, film_id=film_id)

            log.info('Film search %s finished. Found %s torrents.', film_id, len(new_ids))

            # Notify requester if needed?
            # The UI triggers this, so maybe just log it.
            # If we want to notify via ws, we need a mechanism.
            # For now, rely on simply adding to DB.

        except Exception as e:  # pylint: disable=broad-exception-caught
            log.exception('Film search failed: %s', e)


async def _notify_requester(bot: Bot, chat_id: int | None, message: str) -> None:
    """Helper to notify requester safely"""
    if not chat_id:
        return
    try:
        await bot.send_message(chat_id, message)
    except Exception as e:  # pylint: disable=broad-exception-caught
        log.error('Failed to send notification: %s', e)


@broker.task
async def notify_subscribers(search_id: int, new_film_ids: list[int]) -> None:
    """Notify subscribers about new torrents"""
    log.info('Notifying subscribers for search %s', search_id)

    token = settings.telegram_token
    if not token:
        log.error('Telegram token not set, cannot notify subscribers')
        return

    bot = Bot(token=token)

    async with get_async_session() as session:
        # Get films and format messages
        films = await get_films_by_ids(session, new_film_ids)
        notifications = await format_films(films)

        # Get subscribers and notify them
        subscribers = await get_search_subscribers(session, search_id)

        for subscriber in subscribers:
            log.info('Notifying chat %s', subscriber.chat_id)

            for note in notifications:
                try:
                    if note['type'] == 'photo' and note['media']:
                        await bot.send_photo(
                            subscriber.chat_id,
                            photo=note['media'],
                            caption=note['caption'],
                            parse_mode=ParseMode.HTML,
                            reply_markup=note['reply_markup'],
                        )
                    else:
                        await bot.send_message(
                            subscriber.chat_id,
                            text=note['caption'],
                            parse_mode=ParseMode.HTML,
                            reply_markup=note['reply_markup'],
                        )
                except telegram_error.TelegramError as e:
                    log.error('Failed to send notification to %s: %s', subscriber.chat_id, e)


async def _notify_single_subscriber(bot: Bot, subscriber: User, notifications: list[Notification]) -> None:
    """Notify a single subscriber"""
    log.info('Notifying chat %s', subscriber.chat_id)

    for note in notifications:
        try:
            if note['type'] == 'photo' and note['media']:
                await bot.send_photo(
                    subscriber.chat_id,
                    photo=note['media'],
                    caption=note['caption'],
                    parse_mode=ParseMode.HTML,
                    reply_markup=note['reply_markup'],
                )
            else:
                await bot.send_message(
                    subscriber.chat_id,
                    text=note['caption'],
                    parse_mode=ParseMode.HTML,
                    reply_markup=note['reply_markup'],
                )
        except telegram_error.TelegramError as e:
            log.error('Failed to send notification to %s: %s', subscriber.chat_id, e)


async def _handle_connection_error(bot: Bot, search: Search, user: User, search_id: int, e: ConnectionError) -> None:
    """Handle connection errors during search execution"""
    tb_str = ''.join(traceback.format_tb(e.__traceback__))

    last_success_seconds = search.last_success_from_now()
    if last_success_seconds is not None and last_success_seconds >= 60 * 60 * 24 * 7:
        last_success_days = last_success_seconds / (60 * 60 * 24)
        msg = (
            f'/ds_{search_id} search with id {search_id} last success was '
            f'{last_success_days:.0f} days ago, failed: {tb_str}'
        )
    else:
        log.exception(e)
        msg = f'/ds_{search_id} search with id {search_id} failed: {tb_str}'

    await bot.send_message(user.chat_id, msg)


@broker.task
async def notify_about_new(search_id: int) -> None:
    """Check for new torrents and notify subscribers"""
    log.info('Starting task for search %s', search_id)

    token = settings.telegram_token
    if not token:
        log.error('Telegram token not set, cannot check for new items')
        return

    bot = Bot(token=token)

    async with get_async_session() as session:
        search = await get_search(session, search_id)
        if not search:
            log.error('Search %s not found', search_id)
            return

        if search.creator_id is None:
            log.error('Search %s has no creator', search_id)
            return

        user = await get_user(session, search.creator_id)
        if not user:
            log.error('User %s not found', search.creator_id)
            return

        subscribers = await get_search_subscribers(session, search_id)
        if not subscribers:
            log.info('Search %s has no subscribers. Skipping.', search_id)
            return

        try:
            # Parse dynamic variables in URL
            current_year = datetime.now(UTC).year
            resolved_url = search.url.replace('{year}', str(current_year))

            # Run the search
            new = await parse_rutor(resolved_url, session, category_id=search.category_id)
            await update_last_success(session, search_id)

            if not new:
                return

            # Get films and format messages
            films = await get_films_by_ids(session, new)
            notifications = await format_films(films)

            for subscriber in subscribers:
                await _notify_single_subscriber(bot, subscriber, notifications)

        except ValueError as e:
            log.exception(e)
            await delete_search(session, search_id)
            await bot.send_message(user.chat_id, f'search with id {search_id} deleted because failed: {e}')
        except ConnectionError as e:
            await _handle_connection_error(bot, search, user, search_id, e)
        except telegram_error.TelegramError as e:
            log.exception(e)
            tb_str = ''.join(traceback.format_tb(e.__traceback__))
            await bot.send_message(user.chat_id, f'/ds_{search_id} search with id {search_id} failed: {tb_str}')

    log.info('End task for search %s', search_id)


@broker.task
async def execute_scheduled_searches() -> None:
    """Execute scheduled searches"""
    log.info('Checking for scheduled searches...')

    async with get_async_session() as session:
        searches = await get_searches(session, show_empty=False)

    now = datetime.now(UTC)
    for search in searches:
        try:
            if not croniter.match(search.cron, now):
                continue

            # Execute search
            await execute_search.kiq(search.id)
            log.info('Scheduled search %s (cron: %s)', search.id, search.cron)
        except Exception:  # pylint: disable=broad-exception-caught
            log.exception('Failed to schedule search %s', search.id)

    log.info('Finished checking scheduled searches')


@broker.task(schedule=[{'cron': '*/5 * * * *'}])
async def cleanup_torrents() -> None:
    """Cleanup completed torrents based on ratio/time limits"""
    log.info('Starting torrent cleanup task...')
    client = get_torrent_client()
    try:
        await client.connect()
        torrents = await client.list_torrents()

        for torrent in torrents:
            # Check for pausedUP state (limit reached)
            # qBittorrent uses 'pausedUP' when seeding limits are reached
            status = torrent.get('status', '').lower()

            should_remove = False

            # If status indicates limit reached
            if status in ('pausedup', 'paused_up', 'finished', 'seeding_complete'):
                should_remove = True

            if should_remove:
                log.info('Removing torrent %s (Status: %s)', torrent.get('name'), status)
                await client.remove_torrent(torrent['hash'])

    except Exception as e:  # pylint: disable=broad-exception-caught
        log.error('Torrent cleanup failed: %s', e)
    finally:
        await client.disconnect()
