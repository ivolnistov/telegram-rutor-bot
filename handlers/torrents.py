# noinspection PyUnusedLocal
import settings
from db import get_films, get_torrent_by_id
from helpers import format_films
from rutor import download_torrent, get_torrent_info
from utils import security
from unicodedata import normalize

__all__ = (
    'download_torrent',
    'torrent_download',
    'torrent_info',
    'torrent_list',
    'torrent_search',
)


# noinspection PyUnusedLocal
@security(settings.USERS_WHITE_LIST)
def torrent_download(update, context):
    id = update.message.text.replace('/dl_', '')
    torrent = get_torrent_by_id(int(id))
    download_torrent(torrent)
    update.message.reply_text(f'Start downloading of {torrent.name}', parse_mode='Markdown')


# noinspection PyUnusedLocal
@security(settings.USERS_WHITE_LIST)
def torrent_info(update, context):
    id = update.message.text.replace('/in_', '')
    torrent = get_torrent_by_id(int(id))
    message = get_torrent_info(torrent.link, f'/dl_{id}')
    update.message.reply_text(message)


# noinspection PyUnusedLocal
@security(settings.USERS_WHITE_LIST)
def torrent_list(update, context):
    messages = format_films(get_films(20))
    for msg in messages:
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode=None)


# noinspection PyUnusedLocal
@security(settings.USERS_WHITE_LIST)
def torrent_search(update, context):
    search = str.strip(update.message.text.replace('/search', ''))
    messages = format_films(get_films(20, query=f'LOWER(name) LIKE LOWER(\'%{search}%\')'))
    for msg in messages:
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode=None)
