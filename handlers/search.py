import settings
from db import add_search_to_db, delete_search, get_searches
from db.users import get_or_create_user_by_chat_id
from utils import security


__all__ = (
    'search_list',
    'search_delete',
    'search_add',
)


@security(settings.USERS_WHITE_LIST)
def search_list(update, context):
    message = ''
    for search in get_searches():
        message += f'/ds_{search.id} /subscribe_{search.id} {search.url} {search.cron}'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


@security(settings.USERS_WHITE_LIST)
def search_delete(update, context):
    id = update.message.text.replace('/ds_', '')
    delete_search(id)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'search was deleted')


@security(settings.USERS_WHITE_LIST)
def search_add(update, context):
    text = update.message.text.replace('/add_search ', '')
    try:
        search, cron = text.split(' ', 1)
    except ValueError:
        return context.bot.send_message(chat_id=update.effective_chat.id, text=f'Invalid format, must be like: http://rutor.info/example * * * * *')
    if len(cron.split(' ')) < 5:
        return context.bot.send_message(chat_id=update.effective_chat.id, text=f'Invalid cron must be like: * * * * *')
    try:
        user = get_or_create_user_by_chat_id(update.effective_chat.id)
        id = add_search_to_db(search, cron, user.id)
    except ValueError as e:
        return context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'/subscribe_{id} search with id {id} added')