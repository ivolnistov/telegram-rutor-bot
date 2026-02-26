from telegram_rutor_bot.utils.country_mapper import map_country_to_iso


def test_map_country_to_iso():
    assert map_country_to_iso('США') == 'US'
    assert map_country_to_iso('Великобритания') == 'GB'
    assert map_country_to_iso('Unknown') is None
