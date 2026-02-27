"""Episode parser for extracting season/episode info from torrent names."""

import re
from typing import NamedTuple


class EpisodeInfo(NamedTuple):
    """Parsed season and episode information."""

    season: int | None
    episode: int | None
    episode_end: int | None  # For ranges like E01-E10
    is_full_season: bool


# Ordered from most specific to least specific
_PATTERNS = [
    # S01E05-E10 or S01E05-10
    re.compile(r'[Ss](\d{1,2})[Ee](\d{1,3})[-–]E?(\d{1,3})'),
    # S01E05
    re.compile(r'[Ss](\d{1,2})[Ee](\d{1,3})'),
    # 1x05
    re.compile(r'(\d{1,2})[xX](\d{1,3})'),
    # Russian: "Сезон 1 Серия 5" or "Сезон 1 Серии 1-8"
    re.compile(r'[Сс]езон\s*(\d{1,2})\s*[Сс]ери[яи]\s*(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?'),
    # Season 1 Episode 5
    re.compile(r'[Ss]eason\s*(\d{1,2})\s*[Ee]pisode\s*(\d{1,3})'),
    # S01 only (full season pack)
    re.compile(r'[Ss](\d{1,2})(?:\s|$|\])'),
    # Russian: "Сезон 1" only
    re.compile(r'[Сс]езон\s*(\d{1,2})(?:\s|$|[)\]])'),
]


def parse_episode(name: str) -> EpisodeInfo | None:
    """Extract season/episode info from a torrent name.

    Returns EpisodeInfo if found, None if no season/episode pattern detected.
    """
    for pattern in _PATTERNS:
        match = pattern.search(name)
        if not match:
            continue

        groups = match.groups()

        if len(groups) == 1:
            return EpisodeInfo(
                season=int(groups[0]),
                episode=None,
                episode_end=None,
                is_full_season=True,
            )
        if len(groups) == 2:
            return EpisodeInfo(
                season=int(groups[0]),
                episode=int(groups[1]),
                episode_end=None,
                is_full_season=False,
            )
        if len(groups) == 3:
            return EpisodeInfo(
                season=int(groups[0]),
                episode=int(groups[1]),
                episode_end=int(groups[2]) if groups[2] else None,
                is_full_season=False,
            )

    return None


def format_episode_label(info: EpisodeInfo) -> str:
    """Format episode info into a human-readable label."""
    if info.is_full_season:
        return f'S{info.season:02d} (Full Season)'
    if info.episode_end:
        return f'S{info.season:02d}E{info.episode:02d}-E{info.episode_end:02d}'
    if info.episode is not None:
        return f'S{info.season:02d}E{info.episode:02d}'
    return f'S{info.season:02d}'
