import settings
import db
from utils import security


__all__ = (
    'subscribe',
    'unsubscribe',
    'subscriptions_list',
)


@security(settings.USERS_WHITE_LIST)
def subscribe(update, context):
    id = int(update.message.text.replace('/subscribe_', ''))
    success, message = db.subscribe(id, update.effective_chat.id)
    if not success:
        return context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'You subscribed to search {id}')


@security(settings.USERS_WHITE_LIST)
def unsubscribe(update, context):
    id = int(update.message.text.replace('/unsubscribe_', ''))
    user = db.get_user_by_chat(update.effective_chat.id)
    db.unsubscribe(id, user.id)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'You unsubscribed from search {id}')


@security(settings.USERS_WHITE_LIST)
def subscriptions_list(update, context):
    user = db.get_user_by_chat(update.effective_chat.id)
    message = ''
    for search in db.get_subscriptions(user.id):
        message += f'/ds_{search.id} {search}'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
