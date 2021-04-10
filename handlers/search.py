import settings
import db
from schedulers import notify_about_new
from utils import security


__all__ = (
    'search_list',
    'search_delete',
    'search_add',
    'search_execute',
)


@security(settings.USERS_WHITE_LIST)
def search_list(update, context):
    message = ''
    for search in db.get_searches(show_empty=True):
        message += f'/ds_{search.id} /es_{search.id} /subscribe_{search.id} {search.url} {" ".join(search.cron)}\n'
    if not message:
        message = 'No searches is defined'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


@security(settings.USERS_WHITE_LIST)
def search_execute(update, context):
    id = update.message.text.replace('/es_', '')
    search = db.get_search(id)
    notify_about_new(search)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'search with id {id} executed')


@security(settings.USERS_WHITE_LIST)
def search_delete(update, context):
    id = update.message.text.replace('/ds_', '')
    db.delete_search(id)
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
        user = db.get_or_create_user_by_chat_id(update.effective_chat.id)
        id = db.add_search_to_db(search, cron, user.id)
    except ValueError as e:
        return context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'/subscribe_{id} search with id {id} added')
