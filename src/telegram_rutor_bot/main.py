"""Main entry point for telegram-rutor-bot"""

import argparse
import asyncio
import logging
import multiprocessing
import sys
import time
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import update
from taskiq import InMemoryBroker
from taskiq.receiver import Receiver
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from telegram_rutor_bot import handlers as h
from telegram_rutor_bot.config import settings
from telegram_rutor_bot.config_listener import config_listener_task, refresh_settings_from_db
from telegram_rutor_bot.db import get_async_session, init_db
from telegram_rutor_bot.db.migrate import init_database
from telegram_rutor_bot.db.models import TaskExecution
from telegram_rutor_bot.services.search_manager import sync_system_searches
from telegram_rutor_bot.tasks.broker import broker, scheduler
from telegram_rutor_bot.tasks.jobs import (
    cleanup_torrents,
    execute_scheduled_searches,
    execute_search,
    notify_about_new,
    search_film_on_rutor,
)

logging.basicConfig(level=settings.log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Keep strong references to background tasks to prevent garbage collection
_background_tasks: set[asyncio.Task[Any]] = set()


async def run_bot() -> None:
    """Run the Telegram bot in async mode"""
    # Sync config
    await refresh_settings_from_db()

    # Sync system searches
    await sync_system_searches()

    # Store reference to prevent garbage collection
    task = asyncio.create_task(config_listener_task())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    if not settings.telegram_token:
        log.error('Telegram token not configured. Please configure via Web UI.')
        return

    application = Application.builder().token(settings.telegram_token).build()

    # Add handlers
    application.add_handler(CommandHandler('start', h.start))
    application.add_handler(CommandHandler('list', h.torrent_list))
    application.add_handler(CommandHandler('search', h.torrent_search))
    application.add_handler(CommandHandler('watch', h.watch_command))
    application.add_handler(CommandHandler('list_search', h.search_list))
    application.add_handler(CommandHandler('list_subscriptions', h.subscriptions_list))
    application.add_handler(CommandHandler('downloads', h.torrent_downloads))
    application.add_handler(CommandHandler('recommend', h.torrent_recommend))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(/dl_\d+)$'), h.torrent_download))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(/in_\d+)$'), h.torrent_info))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(/ds_\d+)$'), h.search_delete))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(/es_\d+)$'), h.search_execute))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(/subscribe_\d+)$'), h.subscribe))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(/unsubscribe_\d+)$'), h.unsubscribe))
    application.add_handler(CommandHandler('adduser', h.add_user_cmd))
    application.add_handler(CommandHandler('language', h.language_handler))
    application.add_handler(CallbackQueryHandler(h.search_callback_handler, pattern=r'^(ds_|es_|sub_|unsub_)'))
    application.add_handler(CallbackQueryHandler(h.set_language_callback, pattern='^lang_'))
    application.add_handler(CallbackQueryHandler(h.callback_query_handler))
    application.add_handler(MessageHandler(filters.COMMAND, h.unknown))

    # Menu Handlers
    application.add_handler(CommandHandler('help', h.help_handler))
    application.add_handler(
        MessageHandler(filters.Regex(r'^📜 (My Subscriptions|Мои подписки)$'), h.subscriptions_list)
    )
    application.add_handler(MessageHandler(filters.Regex(r'^🔎 (Saved Searches|Сохраненные поиски)$'), h.search_list))
    application.add_handler(MessageHandler(filters.Regex(r'^📥 (Active Torrents|Активные торренты)$'), h.torrent_list))
    application.add_handler(MessageHandler(filters.Regex(r'^ℹ️ (Help|Помощь)$'), h.help_handler))

    # Start bot
    await application.initialize()
    await application.start()
    if application.updater:
        await application.updater.start_polling()

    # Keep running until interrupted
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        if application.updater:
            await application.updater.stop()
        await application.stop()
        await application.shutdown()


async def run_scheduler() -> None:
    """Run the TaskIQ scheduler"""
    # Sync config
    await refresh_settings_from_db()

    # Store reference to prevent garbage collection
    task = asyncio.create_task(config_listener_task())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    # Import tasks to register them
    _ = notify_about_new
    _ = execute_scheduled_searches
    _ = execute_search
    _ = cleanup_torrents

    await broker.startup()
    await scheduler.startup()

    last_search_run = 0.0
    last_cleanup_run = 0.0

    try:
        # Keep the scheduler running
        log.info('Scheduler started, entering loop...')
        try:
            while True:
                now = time.time()

                # Run searches every minute
                if now - last_search_run >= 60:
                    log.info('Triggering execute_scheduled_searches')
                    await execute_scheduled_searches.kiq()
                    last_search_run = now

                # Run cleanup every 5 minutes
                if now - last_cleanup_run >= 300:
                    log.info('Triggering cleanup_torrents')
                    await cleanup_torrents.kiq()
                    last_cleanup_run = now

                await asyncio.sleep(1)
        except Exception as e:
            log.exception('Scheduler crashed: %s', e)
            raise
    except KeyboardInterrupt:
        pass
    finally:
        await scheduler.shutdown()
        await broker.shutdown()


def main() -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Telegram Rutor Bot')
    parser.add_argument('mode', choices=['api', 'bot', 'scheduler', 'worker', 'all'], help='Mode to run')
    args = parser.parse_args()

    if args.mode == 'all':
        log.error("Mode 'all' is not yet implemented.")
        return 1

    if sys.platform == 'darwin':
        multiprocessing.set_start_method('fork')

    # Initialize database with SQLAlchemy
    init_db()

    if args.mode == 'bot':
        # Only run migrations if configured to do so
        if settings.run_migrations:
            init_database()

        with suppress(KeyboardInterrupt):
            asyncio.run(run_bot())
    elif args.mode == 'api':
        import uvicorn
        uvicorn.run('telegram_rutor_bot.web.app:app', host='0.0.0.0', port=8000, reload=True)
    elif args.mode == 'scheduler':
        with suppress(KeyboardInterrupt):
            asyncio.run(run_scheduler())
    elif args.mode == 'worker':
        # Import tasks to register them
        _ = notify_about_new
        _ = execute_scheduled_searches
        _ = execute_search
        log.info('Registering task: search_film_on_rutor')
        _ = search_film_on_rutor

        # Check if broker supports workers
        if isinstance(broker, InMemoryBroker):
            log.warning("InMemoryBroker doesn't support separate workers. Tasks will run in the scheduler process.")
            log.info('To use separate workers, configure Redis by setting redis_url in config.toml')
            return 0

        # Run worker
        async def run_worker() -> None:
            # Sync config
            await refresh_settings_from_db()

            # Store reference to prevent garbage collection
            task = asyncio.create_task(config_listener_task())
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)

            # Clean up stale pending tasks (older than 5 minutes)
            # This is safe for multi-worker setups as we only cancel tasks that are clearly stuck/abandoned
            try:
                log.info('Cleaning up stale pending tasks...')
                async with get_async_session() as session:
                    stmt = (
                        update(TaskExecution)
                        .where(
                            TaskExecution.status.in_(['pending', 'running']),
                            TaskExecution.start_time < datetime.now(UTC) - timedelta(minutes=5),
                        )
                        .values(
                            status='cancelled',
                            result='Cancelled on worker startup (stale)',
                            end_time=datetime.now(UTC),
                        )
                    )
                    await session.execute(stmt)
                    await session.commit()
                    log.info('Cleaned up stale pending tasks')
            except Exception as e:  # pylint: disable=broad-exception-caught
                log.error('Failed to cleanup stale tasks: %s', e)

            receiver = Receiver(broker=broker)
            stop_event = asyncio.Event()
            await receiver.listen(stop_event)

        with suppress(KeyboardInterrupt):
            asyncio.run(run_worker())

    return 0


if __name__ == '__main__':
    sys.exit(main())
