"""Filter torrents to only genuinely new episodes for series notifications."""

from telegram_rutor_bot.db.models import Torrent


def filter_new_episode_torrents(
    torrents: list[Torrent],
    already_notified: set[tuple[int, int | None]],
) -> list[Torrent]:
    """Filter torrents to only those with genuinely new episodes.

    Rules:
    - If torrent has no season info: always include (can't dedup)
    - If (season, episode) already notified: skip
    - Full season packs tracked as (season, None)
    """
    result: list[Torrent] = []
    for t in torrents:
        if t.season is None:
            result.append(t)
            continue
        key = (t.season, t.episode)
        if key not in already_notified:
            result.append(t)
    return result
