from apscheduler.schedulers.blocking import BlockingScheduler
from telegram.ext import Updater

import settings
from helpers import format_films, gen_hash
from db import connection, delete_search, get_films_by_ids, get_search_subscribers, get_searches, get_user
from rutor import parse_rutor
import traceback
import logging


log = logging.getLogger(f'{settings.LOG_PREFIX}.schedule')

__all__ = (
    'notify_about_new',
    'scan_about_new_schedules',
)


def notify_about_new(search):
    log.info('starting scheduler job for %s', search.url)
    updater = Updater(token=settings.TELEGRAM_TOKEN, use_context=True)
    with connection() as con:
        user = get_user(search.creator_id, con)
        try:
            new = parse_rutor(search.url, con)
        except ValueError as e:
            log.exception(e)
            delete_search(search.id)
            updater.bot.send_message(user.chat_id, f'search with id {search.id} deleted because failed: {e}')
            return
        except Exception as e:
            log.exception(e)
            tb_str = ''.join(traceback.format_tb(e.__traceback__))
            updater.bot.send_message(user.chat_id, f'/ds_{search.id} search with id {search.id} failed: {tb_str}')
            return
        if not new:
            return
        messages = format_films(get_films_by_ids(new))
        for s in get_search_subscribers(search.id):
            log.info('notify chat %s', s.chat_id)
            for msg in messages:
                updater.bot.send_message(s.chat_id, msg)
        log.info('end scheduler job for %s', search.url)


def scan_about_new_schedules(sc: BlockingScheduler):
    with connection() as con:
        searches = {gen_hash(s.url, 'search_'): s for s in get_searches(con.cursor())}
        job_ids = []
        for job in sc.get_jobs():
            if not job.id.startswith('search_'):
                continue
            if job.id not in searches:
                job.remove()
            job_ids += [job.id]
        for id, search in searches.items():
            if id in job_ids:
                continue
            minute, hour, day, month, day_of_week = search.cron
            sc.add_job(notify_about_new, 'cron', id=id, args=(search,), minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week)
