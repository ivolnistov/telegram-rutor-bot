from telegram_rutor_bot.utils.cron import get_cron_description


def test_get_cron_description_every_minute():
    # We check if it returns localized string or at least not raw cron
    res = get_cron_description('* * * * *', 'en')
    assert 'minute' in res.lower()


def test_get_cron_description_every_hour():
    res = get_cron_description('15 * * * *', 'en')
    assert 'hour' in res.lower()
    assert '15' in res


def test_get_cron_description_every_day():
    res = get_cron_description('30 14 * * *', 'en')
    assert 'day' in res.lower()
    assert '14:30' in res


def test_get_cron_description_every_week():
    res = get_cron_description('0 10 * * 1', 'en')
    assert 'Monday' in res
    assert '10:00' in res


def test_get_cron_description_every_month():
    res = get_cron_description('0 12 1 * *', 'en')
    assert '1st' in res or 'month' in res.lower()
    assert '12:00' in res


def test_get_cron_description_invalid():
    assert get_cron_description('* * * *', 'en') == '* * * *'
