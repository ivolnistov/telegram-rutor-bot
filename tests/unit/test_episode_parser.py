"""Tests for episode parser utility."""

import pytest

from telegram_rutor_bot.utils.episode_parser import EpisodeInfo, format_episode_label, parse_episode


class TestParseEpisode:
    def test_standard_sxxexx(self) -> None:
        result = parse_episode('Breaking Bad S01E05 1080p BluRay')
        assert result == EpisodeInfo(season=1, episode=5, episode_end=None, is_full_season=False)

    def test_lowercase_sxxexx(self) -> None:
        result = parse_episode('show.s03e12.hdtv')
        assert result == EpisodeInfo(season=3, episode=12, episode_end=None, is_full_season=False)

    def test_range_pattern(self) -> None:
        result = parse_episode('Show S01E01-E10 720p')
        assert result == EpisodeInfo(season=1, episode=1, episode_end=10, is_full_season=False)

    def test_range_without_e_prefix(self) -> None:
        result = parse_episode('Show S02E05-10 720p')
        assert result == EpisodeInfo(season=2, episode=5, episode_end=10, is_full_season=False)

    def test_1x05_format(self) -> None:
        result = parse_episode('Show 2x07 DVDRip')
        assert result == EpisodeInfo(season=2, episode=7, episode_end=None, is_full_season=False)

    def test_russian_season_episode(self) -> None:
        result = parse_episode('Сериал / Show (2023) Сезон 2 Серия 5 1080p')
        assert result == EpisodeInfo(season=2, episode=5, episode_end=None, is_full_season=False)

    def test_russian_season_episodes_range(self) -> None:
        result = parse_episode('Сериал (2023) Сезон 1 Серии 1-8')
        assert result == EpisodeInfo(season=1, episode=1, episode_end=8, is_full_season=False)

    def test_full_season_pack(self) -> None:
        result = parse_episode('Show S03 Complete 1080p')
        assert result == EpisodeInfo(season=3, episode=None, episode_end=None, is_full_season=True)

    def test_russian_season_only(self) -> None:
        result = parse_episode('Сериал (2023) Сезон 2')
        assert result == EpisodeInfo(season=2, episode=None, episode_end=None, is_full_season=True)

    def test_no_episode_info(self) -> None:
        result = parse_episode('Movie (2023) 1080p BluRay')
        assert result is None

    def test_english_long_form(self) -> None:
        result = parse_episode('Show Season 1 Episode 3 720p')
        assert result == EpisodeInfo(season=1, episode=3, episode_end=None, is_full_season=False)

    @pytest.mark.parametrize(
        ('name', 'expected_season', 'expected_episode'),
        [
            ('Игра престолов S08E06 2160p', 8, 6),
            ('The.Last.of.Us.s01e09.1080p', 1, 9),
            ('Мандалорец Сезон 3 Серия 1', 3, 1),
        ],
    )
    def test_various_formats(self, name: str, expected_season: int, expected_episode: int) -> None:
        result = parse_episode(name)
        assert result is not None
        assert result.season == expected_season
        assert result.episode == expected_episode


class TestFormatEpisodeLabel:
    def test_standard(self) -> None:
        assert format_episode_label(EpisodeInfo(1, 5, None, False)) == 'S01E05'

    def test_range(self) -> None:
        assert format_episode_label(EpisodeInfo(1, 1, 10, False)) == 'S01E01-E10'

    def test_full_season(self) -> None:
        assert format_episode_label(EpisodeInfo(3, None, None, True)) == 'S03 (Full Season)'

    def test_season_only(self) -> None:
        assert format_episode_label(EpisodeInfo(2, None, None, False)) == 'S02'
