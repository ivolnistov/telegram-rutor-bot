"""Common Telegram bot command handlers"""

from telegram import Update
from telegram.ext import ContextTypes

from telegram_rutor_bot.config import settings
from telegram_rutor_bot.utils import security

__all__ = (
    'start',
    'unknown',
)


@security(settings.users_white_list)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    assert update.effective_chat is not None  # Checked by security decorator
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


@security(settings.users_white_list)
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands"""
    assert update.effective_chat is not None  # Checked by security decorator
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")
