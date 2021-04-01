import settings
from utils import security


__all__ = (
    'start',
    'unknown',
)


@security(settings.USERS_WHITE_LIST)
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


@security(settings.USERS_WHITE_LIST)
def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Sorry, I didn\'t understand that command.')
