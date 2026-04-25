"""Internationalization utilities."""

from typing import Any, Final

DEFAULT_LANGUAGE: Final[str] = 'en'
SUPPORTED_LANGUAGES: Final[set[str]] = {'en', 'ru'}

TRANSLATIONS = {
    'en': {
        'start_message': 'Hello! I am Rutor Bot. Choose an action from the menu:',
        'help_text': (
            '🤖 *Rutor Bot Help*\n\n'
            '*/search <text>* - Find and download torrent\n'
            '*/list_search* - List your saved searches\n'
            '*/list_subscriptions* - List your series subscriptions\n'
            '*/list* - List active torrents in client\n'
            '*/language* - Change language\n\n'
            'Just use the menu buttons for lists.'
        ),
        'unknown_command': 'Sorry, I did not understand this command. Use the menu or /start',
        'usage_adduser': 'Usage: /adduser <chat_id>',
        'id_must_be_number': 'ID must be a number',
        'user_added': 'User {chat_id} added and authorized.',
        'menu_saved_searches': '🔎 Saved Searches',
        'menu_subscriptions': '📜 My Subscriptions',
        'menu_active_torrents': '📥 Active Torrents',
        'menu_help': 'ℹ️ Help',
        'no_searches': 'No searches defined',
        'search_deleted': 'Search was deleted',
        'subscribed': 'You subscribed to search {search_id}',
        'unsubscribed': 'You unsubscribed from search {search_id}',
        'no_subscriptions': 'No subscriptions',
        'fetching_torrents': 'Fetching torrents...',
        'no_films_db': 'No films found in database',
        'no_messages': 'No messages to send',
        'no_films_found': 'No films found',
        'start_downloading': 'Start downloading of <b>{name}</b>',
        'torrent_not_found': 'Torrent not found',
        'getting_info': '🔍 Getting movie information...',
        'error_getting_info': '❌ Error getting information:\n{error}',
        'started_downloading': '✅ Started downloading: <b>{name}</b>',
        'language_changed': 'Language changed to English 🇺🇸',
        'choose_language': 'Choose your language / Выберите язык:',
        'every_minute': 'Every minute',
        'every_hour': 'Every hour at {minute} minutes',
        'every_day': 'Every day at {hour}:{minute}',
        'every_week': 'Every {dow} at {hour}:{minute}',
        'every_month': 'On day {day} of every month at {hour}:{minute}',
        'cron_dow_0': 'Sunday',
        'cron_dow_1': 'Monday',
        'cron_dow_2': 'Tuesday',
        'cron_dow_3': 'Wednesday',
        'cron_dow_4': 'Thursday',
        'cron_dow_5': 'Friday',
        'cron_dow_6': 'Saturday',
        'discovery_usage': 'Usage: /discovery <title>',
        'discovery_no_results': 'No results found in TMDB',
        'discovery_results_header': 'Found in TMDB:',
        'discovery_tv_not_supported': 'TV shows are not yet supported by /discovery — only movies for now.',
        'discovery_search_started': (
            '🔎 Started a rutor search for <b>{title}</b> ({year}). I will ping you when torrents show up.'
        ),
        'discovery_existing_from_db': ('🎬 <b>{title}</b> ({year}) — {count} torrent(s) in your library.'),
        'discovery_refresh_no_new': '🔎 No new torrents on rutor for «{title}» ({year}).',
        'discovery_refresh_no_new_no_film': '🔎 No new torrents on rutor.',
        'discovery_refresh_new_header': '🆕 {count} new torrent(s) on rutor for «{title}» ({year}):',
        'discovery_tmdb_error': 'Could not query TMDB right now. Please try again later.',
        'btn_discovery_pick_torrents': '🔎 Find torrents on rutor',
        'btn_discovery_pick_seasons': '📺 Pick a season',
        'btn_discovery_all_seasons': '🔎 All seasons',
        'btn_discovery_season': '📺 S{n}',
    },
    'ru': {
        'start_message': 'Привет! Я Rutor Bot. Выбери действие в меню:',
        'help_text': (
            '🤖 *Помощь по Rutor Bot*\n\n'
            '*/search <text>* - Найти и скачать торрент\n'
            '*/list_search* - Список ваших поисков\n'
            '*/list_subscriptions* - Список подписок на сериалы\n'
            '*/list* - Список активных закачек в клиенте\n'
            '*/language* - Сменить язык\n\n'
            'Просто используйте кнопки меню.'
        ),
        'unknown_command': 'Извини, я не понял эту команду. Используй меню или /start',
        'usage_adduser': 'Использование: /adduser <chat_id>',
        'id_must_be_number': 'ID должен быть числом',
        'user_added': 'Пользователь {chat_id} добавлен и авторизован.',
        'menu_saved_searches': '🔎 Сохраненные поиски',
        'menu_subscriptions': '📜 Мои подписки',
        'menu_active_torrents': '📥 Активные торренты',
        'menu_help': 'ℹ️ Помощь',
        'no_searches': 'Нет сохраненных поисков',
        'search_deleted': 'Поиск удален',
        'subscribed': 'Вы подписались на поиск {search_id}',
        'unsubscribed': 'Вы отписались от поиска {search_id}',
        'no_subscriptions': 'Нет подписок',
        'fetching_torrents': 'Получение списка торрентов...',
        'no_films_db': 'В базе данных нет фильмов',
        'no_messages': 'Нет сообщений для отправки',
        'no_films_found': 'Фильмы не найдены',
        'start_downloading': 'Начало загрузки <b>{name}</b>',
        'torrent_not_found': 'Торрент не найден',
        'getting_info': '🔍 Получение информации о фильме...',
        'error_getting_info': '❌ Ошибка получения информации:\n{error}',
        'started_downloading': '✅ Загрузка началась: <b>{name}</b>',
        'language_changed': 'Язык изменен на Русский 🇷🇺',
        'choose_language': 'Choose your language / Выберите язык:',
        'every_minute': 'Каждую минуту',
        'every_hour': 'Каждый час в {minute} минут',
        'every_day': 'Ежедневно в {hour}:{minute}',
        'every_week': 'Каждый {dow} в {hour}:{minute}',
        'every_month': '{day}-го числа каждого месяца в {hour}:{minute}',
        'cron_dow_0': 'Вс',
        'cron_dow_1': 'Пн',
        'cron_dow_2': 'Вт',
        'cron_dow_3': 'Ср',
        'cron_dow_4': 'Чт',
        'cron_dow_5': 'Пт',
        'cron_dow_6': 'Сб',
        'discovery_usage': 'Использование: /discovery <название>',
        'discovery_no_results': 'Ничего не найдено в TMDB',
        'discovery_results_header': 'Найдено в TMDB:',
        'discovery_tv_not_supported': 'Сериалы пока не поддерживаются командой /discovery — только фильмы.',
        'discovery_search_started': (
            '🔎 Запустил поиск на rutor для <b>{title}</b> ({year}). Пришлю, когда найду торренты.'
        ),
        'discovery_existing_from_db': ('🎬 <b>{title}</b> ({year}) — {count} торрентов в библиотеке.'),
        'discovery_refresh_no_new': '🔎 По «{title}» ({year}) новых торрентов на rutor не найдено.',
        'discovery_refresh_no_new_no_film': '🔎 Новых торрентов на rutor не найдено.',
        'discovery_refresh_new_header': '🆕 По «{title}» ({year}) {count} новых торрентов на rutor:',
        'discovery_tmdb_error': 'Не удалось обратиться к TMDB. Попробуйте позже.',
        'btn_discovery_pick_torrents': '🔎 Найти торренты на rutor',
        'btn_discovery_pick_seasons': '📺 Выбрать сезон',
        'btn_discovery_all_seasons': '🔎 Все сезоны',
        'btn_discovery_season': '📺 С{n}',
    },
}


def get_text(key: str, lang: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:  # noqa: ANN401
    """Get translated text for a key."""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANGUAGE])
    text = lang_dict.get(key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text
