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
from telegram_rutor_bot.db.models import Search, TaskExecution, User, subscribes_table
from telegram_rutor_bot.helpers import format_films
from telegram_rutor_bot.rutor import parse_rutor
from telegram_rutor_bot.schemas import Notification
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

    new = await parse_rutor(
        search.url,
        session,
        category_id=search.category_id,
        progress_callback=update_progress,
    )

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
            # Run the search
            new = await parse_rutor(search.url, session, category_id=search.category_id)
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
