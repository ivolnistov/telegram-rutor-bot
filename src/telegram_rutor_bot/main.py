"""Main entry point for telegram-rutor-bot"""

import argparse
import asyncio
import logging
import multiprocessing
import sys
from contextlib import suppress

from taskiq import InMemoryBroker
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from telegram_rutor_bot import handlers as h
from telegram_rutor_bot.config import settings
from telegram_rutor_bot.db import init_db
from telegram_rutor_bot.db.migrate import init_database
from telegram_rutor_bot.tasks.broker import broker, scheduler
from telegram_rutor_bot.tasks.jobs import execute_scheduled_searches, notify_about_new

logging.basicConfig(level=settings.log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


async def run_bot() -> None:
    """Run the Telegram bot in async mode"""
    application = Application.builder().token(settings.telegram_token).build()

    # Add handlers
    application.add_handler(CommandHandler('start', h.start))
    application.add_handler(CommandHandler('list', h.torrent_list))
    application.add_handler(CommandHandler('search', h.torrent_search))
    application.add_handler(CommandHandler('add_search', h.search_add))
    application.add_handler(CommandHandler('list_search', h.search_list))
    application.add_handler(CommandHandler('list_subscriptions', h.subscriptions_list))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(/dl_\d+)$'), h.torrent_download))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(/in_\d+)$'), h.torrent_info))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(/ds_\d+)$'), h.search_delete))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(/es_\d+)$'), h.search_execute))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(/subscribe_\d+)$'), h.subscribe))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(/unsubscribe_\d+)$'), h.unsubscribe))
    application.add_handler(MessageHandler(filters.COMMAND, h.unknown))

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
    # Import tasks to register them
    _ = notify_about_new
    _ = execute_scheduled_searches

    await broker.startup()
    await scheduler.startup()

    try:
        # Keep the scheduler running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await scheduler.shutdown()
        await broker.shutdown()


def main() -> int:
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description='Telegram Rutor Bot')
    parser.add_argument(
        'mode',
        choices=['bot', 'scheduler', 'worker'],
        help='Run mode: bot for telegram bot, scheduler for TaskIQ scheduler, worker for TaskIQ worker',
    )
    args = parser.parse_args()

    if sys.platform == 'darwin':
        multiprocessing.set_start_method('fork')

    # Initialize database with SQLAlchemy and run migrations
    init_db()
    init_database()

    if args.mode == 'bot':
        with suppress(KeyboardInterrupt):
            asyncio.run(run_bot())
    elif args.mode == 'scheduler':
        with suppress(KeyboardInterrupt):
            asyncio.run(run_scheduler())
    elif args.mode == 'worker':
        # Import tasks to register them
        _ = notify_about_new
        _ = execute_scheduled_searches

        # Check if broker supports workers
        if isinstance(broker, InMemoryBroker):
            log.warning("InMemoryBroker doesn't support separate workers. Tasks will run in the scheduler process.")
            log.info('To use separate workers, configure Redis by setting redis_url in config.toml')
            return 0

        # Run worker
        async def run_worker() -> None:
            async for _ in broker.listen():
                pass

        with suppress(KeyboardInterrupt):
            asyncio.run(run_worker())

    return 0


if __name__ == '__main__':
    sys.exit(main())
