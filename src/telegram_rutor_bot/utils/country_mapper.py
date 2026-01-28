"""
Simple utility to map Russian country names to ISO 3166-1 alpha-2 codes.
Used for displaying flags in the UI.
"""

COUNTRY_MAP = {
    'США': 'US',
    'Великобритания': 'GB',
    'Россия': 'RU',
    'СССР': 'RU',  # Historical mapping
    'Франция': 'FR',
    'Германия': 'DE',
    'Италия': 'IT',
    'Испания': 'ES',
    'Япония': 'JP',
    'Южная Корея': 'KR',
    'Корея Южная': 'KR',
    'Китай': 'CN',
    'Индия': 'IN',
    'Канада': 'CA',
    'Австралия': 'AU',
    'Новая Зеландия': 'NZ',
    'Бразилия': 'BR',
    'Мексика': 'MX',
    'Швеция': 'SE',
    'Норвегия': 'NO',
    'Дания': 'DK',
    'Финляндия': 'FI',
    'Нидерланды': 'NL',
    'Бельгия': 'BE',
    'Австрия': 'AT',
    'Швейцария': 'CH',
    'Ирландия': 'IE',
    'Польша': 'PL',
    'Чехия': 'CZ',
    'Венгрия': 'HU',
    'Турция': 'TR',
    'Израиль': 'IL',
    'Гонконг': 'HK',
    'Тайвань': 'TW',
    'Таиланд': 'TH',
    'Вьетнам': 'VN',
    'Индонезия': 'ID',
    'Филиппины': 'PH',
    'Аргентина': 'AR',
    'Чили': 'CL',
    'Колумбия': 'CO',
    'ЮАР': 'ZA',
    'Египет': 'EG',
    'Иран': 'IR',
    'Украина': 'UA',
    'Беларусь': 'BY',
    'Казахстан': 'KZ',
}


def map_country_to_iso(country_name: str | None) -> str | None:
    """Map localized country name to ISO code."""
    if not country_name:
        return None

    # Handle multiple countries "США, Великобритания" - take first
    first_country = country_name.split(',')[0].strip()
    return COUNTRY_MAP.get(first_country)
