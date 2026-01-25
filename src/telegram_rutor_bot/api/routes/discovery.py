from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from telegram_rutor_bot.clients.tmdb import TmdbClient
from telegram_rutor_bot.db.database import get_async_db
from telegram_rutor_bot.db.models import Film, Torrent, User
from telegram_rutor_bot.services.matcher import TmdbMatcher
from telegram_rutor_bot.services.monitor import WatchlistMonitor
from telegram_rutor_bot.web.auth import get_current_user

router = APIRouter(prefix='/api/discovery', tags=['discovery'])
tmdb = TmdbClient()


async def _enrich_with_library_status(results: list[dict[str, Any]], db: AsyncSession) -> list[dict[str, Any]]:
    if not results:
        return []

    # Get all TMDB IDs from results
    tmdb_ids = [r['id'] for r in results if 'id' in r]
    if not tmdb_ids:
        return results

    # Find which ones exist in DB
    stmt = select(Film.tmdb_id).where(Film.tmdb_id.in_(tmdb_ids))
    result = await db.execute(stmt)
    existing_ids = set(result.scalars().all())

    for r in results:
        r['in_library'] = r.get('id') in existing_ids

    return results


@router.get('/trending')
async def get_trending(
    media_type: str = Query('all', regex='^(all|movie|tv)$'),
    time_window: str = Query('week', regex='^(day|week)$'),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> list[dict[str, Any]]:
    """Get trending movies and TV shows"""
    results = await tmdb.get_trending(media_type, time_window)
    return await _enrich_with_library_status(results, db)


@router.get('/search')
async def search_discovery(
    q: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> list[dict[str, Any]]:
    """Search for movies and TV shows in TMDB"""
    results = await tmdb.search_multi(q)
    return await _enrich_with_library_status(results, db)


@router.get('/{media_type}/{media_id}/recommendations')
async def get_recommendations(
    media_type: str,
    media_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> list[dict[str, Any]]:
    """Get recommendations based on a movie or TV show"""
    results = await tmdb.get_recommendations(media_type, media_id)
    return await _enrich_with_library_status(results, db)


class RateRequest(BaseModel):
    media_type: str
    media_id: int
    value: float


@router.get('/watchlist')
async def get_watchlist(
    media_type: str = Query('movie', regex='^(movie|tv)$'),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> list[dict[str, Any]]:
    """Get user watchlist from TMDB"""
    items = await tmdb.get_watchlist(media_type)
    return await _enrich_with_library_status(items, db)


@router.post('/watchlist')
async def add_to_watchlist(
    media_type: str,
    media_id: int,
    watchlist: bool = True,
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Add or remove from TMDB watchlist via proxy"""
    success = await tmdb.add_to_watchlist(media_type, media_id, watchlist)
    return {'status': 'success' if success else 'failed'}


@router.post('/watchlist/sync')
async def sync_watchlist_items(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Trigger watchlist sync and check"""
    monitor = WatchlistMonitor(db)
    # Sync immediately
    count = await monitor.sync_watchlist()

    # Schedule check in background
    background_tasks.add_task(monitor.check_monitored_items)

    return {'status': 'success', 'synced': count}


@router.post('/rate')
async def rate_media(request: RateRequest, user: User = Depends(get_current_user)) -> dict[str, str]:
    """Rate a movie or TV show"""
    success = await tmdb.rate_media(request.media_type, request.media_id, request.value)
    if not success:
        raise HTTPException(status_code=400, detail='Failed to rate media')
    return {'status': 'success'}


@router.get('/personal')
@router.get('/personal')
async def get_personal_recs(user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    """Get personalized recommendations based on ratings"""
    return await tmdb.get_personal_recommendations()


@router.post('/sync')
async def sync_library(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Sync library with TMDB (link local films)"""
    matcher = TmdbMatcher(db)
    count = await matcher.match_films(limit=limit)
    return {'status': 'success', 'matched': count}


@router.get('/{media_type}/{media_id}/account_states')
async def get_account_states(
    media_type: str,
    media_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Get account states (rating) for a movie or TV show"""
    states = await tmdb.get_account_states(media_type, media_id)

    # Check if in library
    result = await db.execute(select(Film).where(Film.tmdb_id == media_id))
    film = result.scalar_one_or_none()

    states['in_library'] = bool(film)
    return states


@router.delete('/rate')
async def delete_rating(
    media_type: str,
    media_id: int,
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Delete rating for a movie or TV show"""
    success = await tmdb.delete_rating(media_type, media_id)
    if not success:
        raise HTTPException(status_code=400, detail='Failed to delete rating')
    return {'status': 'success'}


@router.get('/rated')
@router.get('/rated')
async def get_rated(
    media_type: str = Query('movie', regex='^(movie|tv)$'),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> list[dict[str, Any]]:
    """Get rated movies or tv shows"""
    results = await tmdb.get_rated_media(media_type)
    return await _enrich_with_library_status(results, db)


@router.get('/{media_type}/{media_id}/torrents')
async def get_media_torrents(
    media_type: str,
    media_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> list[Torrent]:
    """Get torrents linked to a movie or TV show"""
    # Find the film by TMDB ID
    stmt = select(Film).options(selectinload(Film.torrents)).where(Film.tmdb_id == media_id)
    result = await db.execute(stmt)
    film = result.scalar_one_or_none()

    if not film:
        return []

    # Return torrents
    # We map to TorrentResponse. Note: film field in TorrentResponse might be recursive if we populate it here,
    # but Film.torrents -> Torrent.film (back_populates).
    # Since we loaded Film.torrents, each torrent has torrent.film populated as this film object.
    # Pydantic should handle the cycle if configured, or we just return list.
    return film.torrents
