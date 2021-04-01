__all__ = ('security',)

import settings


def security(white_list):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            update, context = args
            msg = getattr(update, 'message', None)
            if not msg:
                return
            user = msg.from_user
            if user.id not in white_list:
                return context.bot.send_message(chat_id=update.effective_chat.id, text=settings.UNAUTHORIZED_MESSAGE)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
