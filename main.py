import logging
import multiprocessing
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

import handlers as h
import settings
from db import connection, get_searches, init
from helpers import gen_hash
from schedulers import notify_about_new, scan_about_new_schedules


logging.basicConfig(level=settings.LOG_LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def bot():
    updater = Updater(token=settings.TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', h.start))
    dp.add_handler(CommandHandler('list', h.torrent_list))
    dp.add_handler(CommandHandler('add_search', h.search_add))
    dp.add_handler(CommandHandler('list_search', h.search_list))
    dp.add_handler(CommandHandler('list_subscriptions', h.subscriptions_list))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'^(/dl_\d+)$'), h.torrent_download))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'^(/in_\d+)$'), h.torrent_info))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'^(/ds_\d+)$'), h.search_delete))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'^(/subscribe_\d+)$'), h.subscribe))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'^(/unsubscribe_\d+)$'), h.unsubscribe))
    dp.add_handler(MessageHandler(Filters.command, h.unknown))
    try:
        updater.start_polling()
    except KeyboardInterrupt:
        pass


def scheduler():
    try:
        sc = BlockingScheduler()
        sc.add_job(scan_about_new_schedules, 'cron', month='*', day='*', hour='*', minute='*', args=(sc,))
        with connection() as con:
            for search in get_searches(con.cursor()):
                # noinspection PyTupleAssignmentBalance
                minute, hour, day, month, day_of_week = search.cron
                id = gen_hash(search.url, 'search_')
                sc.add_job(notify_about_new, 'cron', id=id, args=(search,), minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week)
            sc.start()
    except KeyboardInterrupt:
        pass


def main():
    if sys.platform == 'darwin':
        multiprocessing.set_start_method('fork')
    bot_proc = multiprocessing.Process(target=bot, args=())
    sc_proc = multiprocessing.Process(target=scheduler, args=())
    with connection() as con:
        init(con)
    try:
        bot_proc.start()
        sc_proc.start()
        bot_proc.join()
        sc_proc.join()
    except KeyboardInterrupt:
        bot_proc.terminate()
        sc_proc.terminate()
    return 0


if __name__ == '__main__':
    sys.exit(main())
