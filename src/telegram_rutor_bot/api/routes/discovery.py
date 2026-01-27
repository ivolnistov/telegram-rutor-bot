import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from telegram_rutor_bot.clients.tmdb import TmdbClient
from telegram_rutor_bot.db.database import get_async_db
from telegram_rutor_bot.db.films import get_or_create_film, update_film_metadata
from telegram_rutor_bot.db.models import Film, Torrent, User
from telegram_rutor_bot.schemas import TorrentResponse
from telegram_rutor_bot.services.matcher import TmdbMatcher
from telegram_rutor_bot.services.monitor import WatchlistMonitor
from telegram_rutor_bot.tasks.jobs import search_film_on_rutor
from telegram_rutor_bot.web.auth import get_current_user

router = APIRouter(prefix='/api/discovery', tags=['discovery'])
tmdb = TmdbClient()
log = logging.getLogger(__name__)


async def _enrich_with_library_status(results: list[dict[str, Any]], db: AsyncSession) -> list[dict[str, Any]]:
    if not results:
        return []

    # Get all TMDB IDs from results
    tmdb_ids = [r['id'] for r in results if 'id' in r]
    if not tmdb_ids:
        return results

    # Find which ones exist in DB and check for torrents

    stmt = (
        select(Film.tmdb_id, func.count(Torrent.id))
        .outerjoin(Torrent)
        .where(Film.tmdb_id.in_(tmdb_ids))
        .group_by(Film.tmdb_id)
    )
    result = await db.execute(stmt)

    # Map tmdb_id -> torrent_count
    counts_map = {row[0]: row[1] for row in result.all()}
    existing_ids = set(counts_map.keys())

    for r in results:
        tmdb_id = r.get('id')
        r['in_library'] = tmdb_id in existing_ids
        r['torrents_count'] = counts_map.get(tmdb_id, 0)

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


@router.get('/{media_type}/{media_id}/torrents', response_model=list[TorrentResponse])
async def get_media_torrents(
    media_type: str,
    media_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> list[TorrentResponse]:
    """Get torrents linked to a movie or TV show"""
    # Find the film by TMDB ID
    stmt = select(Film).options(selectinload(Film.torrents)).where(Film.tmdb_id == media_id)
    result = await db.execute(stmt)
    film = result.scalar_one_or_none()

    if not film:
        log.warning(f'Film not found for media_id {media_id}')
        return []

    log.info(f'Returning {len(film.torrents)} torrents for film {film.id} (TMDB {media_id})')
    # Convert SQLAlchemy Torrent to Pydantic TorrentResponse
    return [TorrentResponse.model_validate(t) for t in film.torrents]


@router.post('/search_on_rutor', response_model=dict[str, str])
async def search_on_rutor(
    media_type: str,
    media_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, str]:
    """
    Search for torrents on Rutor by TMDB ID.
    If film doesn't exist locally, it will be created.
    """
    if media_type != 'movie':
        raise HTTPException(status_code=400, detail='Only movies are supported for now')

    # Check if film exists
    stmt = select(Film).where(Film.tmdb_id == media_id)
    film = (await db.execute(stmt)).scalar_one_or_none()

    # Always fetch details to get original_title
    details = {}
    try:
        details = await tmdb.get_details(media_type, media_id)
    except Exception as e:
        if not film:
            raise HTTPException(status_code=404, detail=f'TMDB error: {e}') from e
        # If we have the film, we can proceed without fresh details, but won't be able to search for original title
        pass

    if not film and not details:
        raise HTTPException(status_code=404, detail='Media not found in TMDB')

    if not film:
        # Create film
        name = details.get('title') or details.get('name') or 'Unknown'
        year = None
        if details.get('release_date'):
            year = int(details['release_date'][:4])
        elif details.get('first_air_date'):
            year = int(details['first_air_date'][:4])

        original_title = details.get('original_title') or details.get('original_name')

        # We can use a dummy blake for now, e.g. tmdb_movie_12345
        dummy_blake = f'tmdb_{media_type}_{media_id}'

        film = await get_or_create_film(
            db,
            blake=dummy_blake,
            year=year,
            name=name,
            poster=details.get('poster_path'),
            rating=details.get('vote_average'),
            original_title=original_title,
        )

        await update_film_metadata(
            db,
            film_id=film.id,
            tmdb_id=media_id,
            tmdb_media_type=media_type,
            year=year,
            name=name,
            poster=details.get('poster_path'),
            rating=details.get('vote_average'),
            original_title=original_title,
        )

    # Now we have a film, trigger search

    # 1. Search with localized name
    queries = set()
    query_localized = film.name
    if film.year:
        query_localized += f' ({film.year})'
    queries.add(query_localized)

    # 2. Search with original name if available and different
    original_name = details.get('original_title') or details.get('original_name')
    if original_name and original_name != film.name:
        query_original = original_name
        if film.year:
            query_original += f' ({film.year})'
        queries.add(query_original)

    # Queue tasks
    for q in queries:
        await search_film_on_rutor.kiq(film.id, q, requester_chat_id=user.chat_id)

    return {'status': 'search_started'}
