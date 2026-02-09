from telegram_rutor_bot.db.models import Film, Torrent
from telegram_rutor_bot.services.watchlist import select_best_torrent


def test_select_best_torrent_hard_constraints():
    film = Film(name='Test', max_size_gb=10, min_size_gb=1)

    t1 = Torrent(name='Small', sz=500 * 1024 * 1024)  # 0.5 GB (Too small)
    t2 = Torrent(name='Good', sz=5 * 1024 * 1024 * 1024)  # 5 GB (OK)
    t3 = Torrent(name='Big', sz=20 * 1024 * 1024 * 1024)  # 20 GB (Too big)

    best = select_best_torrent([t1, t2, t3], film)
    assert best == t2


def test_select_best_torrent_voiceover_fuzzy():
    film = Film(name='Breaking Bad', voiceover_filter='LostFilm')

    t1 = Torrent(name='Breaking Bad (NewStudio)', sz=100)
    t2 = Torrent(name='Breaking Bad (LostFilm) 1080p', sz=100)
    t3 = Torrent(name='Breaking Bad (Dub)', sz=100)

    best = select_best_torrent([t1, t2, t3], film)
    assert best == t2


def test_select_best_torrent_target_size():
    film = Film(name='Matrix', target_size_gb=10)  # Target 10 GB

    t1 = Torrent(name='Rip', sz=2 * 1024 * 1024 * 1024)  # 2 GB (Diff 8)
    t2 = Torrent(name='Remux', sz=30 * 1024 * 1024 * 1024)  # 30 GB (Diff 20)
    t3 = Torrent(name='FullHD', sz=12 * 1024 * 1024 * 1024)  # 12 GB (Diff 2)

    best = select_best_torrent([t1, t2, t3], film)
    assert best == t3


def test_select_best_torrent_minimal_size_default():
    film = Film(name='Matrix')  # No constraints

    t1 = Torrent(name='Small', sz=100)
    t2 = Torrent(name='Medium', sz=200)

    best = select_best_torrent([t1, t2], film)
    assert best == t1
