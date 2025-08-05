"""TaskIQ tasks for scheduled jobs"""

import logging
import traceback
from typing import TYPE_CHECKING

from telegram import Bot
from telegram import error as telegram_error

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
from telegram_rutor_bot.helpers import format_films
from telegram_rutor_bot.rutor import parse_rutor

from .broker import broker

if TYPE_CHECKING:
    from telegram_rutor_bot.db.models import Search, User

log = logging.getLogger(f'{settings.log_prefix}.tasks')


@broker.task
async def execute_search(search_id: int, requester_chat_id: int | None = None) -> None:
    """Execute a search and optionally notify the requester"""
    log.info('Executing search %s', search_id)

    bot = Bot(token=settings.telegram_token)

    async with get_async_session() as session:
        search = await get_search(session, search_id)
        if not search:
            log.error('Search %s not found', search_id)
            if requester_chat_id:
                await bot.send_message(requester_chat_id, f'Search with id {search_id} not found')
            return

        try:
            # Run the search
            new = await parse_rutor(search.url, session)
            await update_last_success(session, search_id)

            # Notify requester about completion
            if requester_chat_id:
                if new:
                    await bot.send_message(
                        requester_chat_id, f'✅ Search executed successfully. Found {len(new)} new items.'
                    )
                else:
                    await bot.send_message(requester_chat_id, '✅ Search executed successfully. No new items found.')

            # If there are new items and subscribers, notify them
            if new:
                await notify_subscribers(search_id, new)

        except (ValueError, ConnectionError) as e:
            log.exception('Search %s failed: %s', search_id, e)
            if requester_chat_id:
                tb_str = ''.join(traceback.format_tb(e.__traceback__))
                await bot.send_message(requester_chat_id, f'❌ Search failed:\n{e!s}\n\nTraceback:\n{tb_str}')


@broker.task
async def notify_subscribers(search_id: int, new_film_ids: list[int]) -> None:
    """Notify subscribers about new torrents"""
    log.info('Notifying subscribers for search %s', search_id)

    bot = Bot(token=settings.telegram_token)

    async with get_async_session() as session:
        # Get films and format messages
        films = await get_films_by_ids(session, new_film_ids)
        messages, posters = await format_films(films)

        # Get subscribers and notify them
        subscribers = await get_search_subscribers(session, search_id)

        for subscriber in subscribers:
            log.info('Notifying chat %s', subscriber.chat_id)

            # Send posters first if available
            for poster_data, caption in posters:
                try:
                    await bot.send_photo(subscriber.chat_id, photo=poster_data, caption=caption)
                except telegram_error.TelegramError as e:
                    log.error('Failed to send poster to %s: %s', subscriber.chat_id, e)

            for msg in messages:
                try:
                    await bot.send_message(subscriber.chat_id, msg)
                except telegram_error.TelegramError as e:
                    log.error('Failed to send message to %s: %s', subscriber.chat_id, e)


async def _notify_single_subscriber(
    bot: Bot, subscriber: 'User', messages: list[str], posters: list[tuple[bytes, str]]
) -> None:
    """Notify a single subscriber with messages and posters"""
    log.info('Notifying chat %s', subscriber.chat_id)

    # Send posters first if available
    for poster_data, caption in posters:
        try:
            await bot.send_photo(subscriber.chat_id, photo=poster_data, caption=caption)
        except telegram_error.TelegramError as e:
            log.error('Failed to send poster to %s: %s', subscriber.chat_id, e)

    for msg in messages:
        try:
            await bot.send_message(subscriber.chat_id, msg)
        except telegram_error.TelegramError as e:
            log.error('Failed to send message to %s: %s', subscriber.chat_id, e)


async def _handle_connection_error(
    bot: Bot, search: 'Search', user: 'User', search_id: int, e: ConnectionError
) -> None:
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

    bot = Bot(token=settings.telegram_token)

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

        try:
            # Run the async parse_rutor
            new = await parse_rutor(search.url, session)
            await update_last_success(session, search_id)

            if not new:
                return

            # Get films and format messages
            films = await get_films_by_ids(session, new)
            messages, posters = await format_films(films)

            # Get subscribers and notify them
            subscribers = await get_search_subscribers(session, search_id)

            for subscriber in subscribers:
                await _notify_single_subscriber(bot, subscriber, messages, posters)

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


@broker.task(schedule=[{'cron': '* * * * *'}])  # Run every minute
async def execute_scheduled_searches() -> None:
    """Execute scheduled searches"""
    log.info('Checking for scheduled searches...')

    async with get_async_session() as session:
        searches = await get_searches(session, show_empty=False)

    for search in searches:
        # Create a unique task name for this search

        # Check if task already scheduled
        # For now, we'll just execute all searches every minute
        # In production, you'd want to track last execution time
        await notify_about_new.kiq(search.id)
        log.info('Scheduled search %s', search.id)

    log.info('Finished checking scheduled searches')
