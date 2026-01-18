"""Common Telegram bot command handlers"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from telegram_rutor_bot.db import (
    get_async_session,
    get_or_create_user_by_chat_id,
    get_user_by_chat,
    grant_access,
    set_user_language,
)
from telegram_rutor_bot.utils import DEFAULT_LANGUAGE, get_text, security

__all__ = (
    'add_user_cmd',
    'help_handler',
    'language_handler',
    'set_language_callback',
    'start',
    'unknown',
)


async def _get_lang(update: Update) -> str:
    """Helper to get language from user object"""
    chat_id = update.effective_chat.id if update.effective_chat else 0
    if not chat_id:
        return DEFAULT_LANGUAGE

    async with get_async_session() as session:
        user = await get_user_by_chat(session, chat_id)
        if user:
            return user.language
        # If user not found (e.g. not authorized yet), defaults to EN
        return DEFAULT_LANGUAGE


@security()
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    assert update.effective_chat is not None  # Checked by security decorator

    # Ensure user exists to have a language preference
    async with get_async_session() as session:
        user = await get_or_create_user_by_chat_id(session, update.effective_chat.id)
        lang = user.language

    keyboard = [
        [get_text('menu_saved_searches', lang), get_text('menu_subscriptions', lang)],
        [get_text('menu_active_torrents', lang), get_text('menu_help', lang)],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=get_text('start_message', lang), reply_markup=reply_markup
    )


@security()
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Help"""
    if not update.effective_chat:
        return

    lang = await _get_lang(update)
    text = get_text('help_text', lang)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='Markdown')


@security()
async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /language command"""
    assert update.effective_chat is not None
    lang = await _get_lang(update)

    keyboard = [
        [
            InlineKeyboardButton('English 🇺🇸', callback_data='lang_en'),
            InlineKeyboardButton('Русский 🇷🇺', callback_data='lang_ru'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=get_text('choose_language', lang), reply_markup=reply_markup
    )


@security()
async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection callback"""
    query = update.callback_query
    if not query or not query.data:
        return

    lang_code = query.data.replace('lang_', '')
    if lang_code not in ('en', 'ru'):
        return

    await query.answer()

    if update.effective_chat:
        async with get_async_session() as session:
            await set_user_language(session, update.effective_chat.id, lang_code)

        # Confirmation message in new language
        text = get_text('language_changed', lang_code)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

        # Refresh main menu in new language
        keyboard = [
            [get_text('menu_saved_searches', lang_code), get_text('menu_subscriptions', lang_code)],
            [get_text('menu_active_torrents', lang_code), get_text('menu_help', lang_code)],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=get_text('start_message', lang_code), reply_markup=reply_markup
        )


@security()
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands"""
    assert update.effective_chat is not None  # Checked by security decorator
    lang = await _get_lang(update)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('unknown_command', lang))


@security()
async def add_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /adduser command"""
    assert update.effective_chat is not None
    lang = await _get_lang(update)

    if not context.args:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('usage_adduser', lang))
        return

    try:
        new_chat_id = int(context.args[0])
    except ValueError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('id_must_be_number', lang))
        return

    async with get_async_session() as session:
        await grant_access(session, new_chat_id)

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=get_text('user_added', lang, chat_id=new_chat_id)
    )
