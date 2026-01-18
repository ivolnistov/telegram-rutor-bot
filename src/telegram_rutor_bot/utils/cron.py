"""Cron expression utilities."""

from .i18n import DEFAULT_LANGUAGE, get_text

__all__ = ('get_cron_description',)


def get_cron_description(cron: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """
    Convert a cron expression into a human-readable string.
    Handles standard 5-part cron: minute hour day month day_of_week
    """
    parts = cron.split()
    if len(parts) != 5:
        return cron

    minute, hour, day, month, day_of_week = parts

    # Helper maps
    days_map = {
        '0': 'cron_dow_0',
        '1': 'cron_dow_1',
        '2': 'cron_dow_2',
        '3': 'cron_dow_3',
        '4': 'cron_dow_4',
        '5': 'cron_dow_5',
        '6': 'cron_dow_6',
        '7': 'cron_dow_0',
        'sun': 'cron_dow_0',
        'mon': 'cron_dow_1',
        'tue': 'cron_dow_2',
        'wed': 'cron_dow_3',
        'thu': 'cron_dow_4',
        'fri': 'cron_dow_5',
        'sat': 'cron_dow_6',
    }

    description = cron

    # Case: Every minute (* * * * *)
    if cron == '* * * * *':
        description = get_text('every_minute', lang)

    # Case: Every hour at minute X (X * * * *)
    elif minute != '*' and hour == '*' and day == '*' and month == '*' and day_of_week == '*':
        description = get_text('every_hour', lang, minute=minute)

    # Case: Every day at HH:MM (M H * * *)
    elif minute != '*' and hour != '*' and day == '*' and month == '*' and day_of_week == '*':
        description = get_text('every_day', lang, hour=hour.zfill(2), minute=minute.zfill(2))

    # Case: Every week on Day at HH:MM (M H * * D)
    elif minute != '*' and hour != '*' and day == '*' and month == '*' and day_of_week != '*':
        dow_key = days_map.get(day_of_week.lower(), 'cron_dow_0')
        dow = get_text(dow_key, lang)
        description = get_text('every_week', lang, dow=dow, hour=hour.zfill(2), minute=minute.zfill(2))

    # Case: Specific day of month at HH:MM (M H D * *)
    elif minute != '*' and hour != '*' and day != '*' and month == '*' and day_of_week == '*':
        description = get_text('every_month', lang, day=day, hour=hour.zfill(2), minute=minute.zfill(2))

    return description
