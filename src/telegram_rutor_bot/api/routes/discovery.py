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
from telegram_rutor_bot.utils.country_mapper import map_country_to_iso
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

    # Find which ones exist in DB and check for torrents
    stmt = (
        select(Film.tmdb_id, func.count(Torrent.id), Film.kp_rating)
        .outerjoin(Torrent)
        .where(Film.tmdb_id.in_(tmdb_ids))
        .group_by(Film.tmdb_id, Film.kp_rating)
    )
    result = await db.execute(stmt)

    # Map tmdb_id -> {count, kp_rating}
    library_map = {row[0]: {'count': row[1], 'kp_rating': row[2]} for row in result.all()}
    existing_ids = set(library_map.keys())

    for r in results:
        tmdb_id = r.get('id')
        if tmdb_id in existing_ids:
            r['in_library'] = True
            data = library_map[tmdb_id]
            r['torrents_count'] = data['count']
            if data['kp_rating']:
                r['kp_rating'] = data['kp_rating']
        else:
            r['in_library'] = False
            r['torrents_count'] = 0

    return results


@router.get('/trending')
async def get_trending(
    media_type: str = Query('all', pattern='^(all|movie|tv)$'),
    time_window: str = Query('week', pattern='^(day|week)$'),
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


@router.get('/{media_type}/{media_id}')
async def get_media_details(
    media_type: str,
    media_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Get full details for a movie or TV show"""
    # Fetch details with external_ids
    details = await tmdb.get_details(media_type, media_id, append_to_response='external_ids')

    # Enrich with library status (single item list)
    enriched_list = await _enrich_with_library_status([details], db)
    return enriched_list[0] if enriched_list else details


class RateRequest(BaseModel):
    media_type: str
    media_id: int
    value: float


@router.get('/watchlist')
async def get_watchlist(
    media_type: str = Query('movie', pattern='^(movie|tv)$'),
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


@router.get('/library')
async def get_library(
    media_type: str = Query('movie', pattern='^(movie|tv|all)$'),
    limit: int = 20,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> list[dict[str, Any]]:
    """Get films in local library"""
    stmt = select(Film).order_by(Film.id.desc()).offset(offset).limit(limit)

    if media_type != 'all':
        stmt = stmt.where(Film.tmdb_media_type == media_type)

    result = await db.execute(stmt)
    films = result.scalars().all()

    # Convert to TMDB-like format
    results = []
    for film in films:
        kp_val = film.kp_rating if film.kp_rating is not None else None
        rating_fallback = float(film.rating) if film.rating else 0.0
        final_rating = float(kp_val) if kp_val is not None else rating_fallback

        # Map Film model to partial TmdbMedia
        media = {
            'id': film.tmdb_id or film.id,  # Fallback to local ID if no TMDB ID
            'tmdb_id': film.tmdb_id,
            'title': film.name,
            'original_title': film.original_title,
            'poster_path': film.poster,
            'vote_average': final_rating,
            'release_date': f'{film.year}-01-01' if film.year else None,
            'media_type': film.tmdb_media_type or 'movie',
            'in_library': True,
            'kp_rating': film.kp_rating,
            'production_countries': (
                [{'iso_3166_1': iso, 'name': film.country}] if (iso := map_country_to_iso(film.country)) else []
            ),
        }
        results.append(media)

    return await _enrich_with_library_status(results, db)


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
    media_type: str = Query('movie', pattern='^(movie|tv)$'),
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

        # Extract country (take first production country)
        country = None
        if details.get('production_countries'):
            country = details['production_countries'][0].get('name')

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
            country=country,
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
            country=country,
        )

    # Now we have a film, trigger search
    queries = _build_search_queries(film, details)

    # Queue tasks
    for q in queries:
        await search_film_on_rutor.kiq(film.id, q, requester_chat_id=user.chat_id)

    return {'status': 'search_started'}


def _build_search_queries(film: Film, details: dict[str, Any]) -> set[str]:
    queries = set()
    query_localized = film.name
    if film.year:
        query_localized += f' ({film.year})'
    queries.add(query_localized)

    original_name = details.get('original_title') or details.get('original_name')
    if original_name and original_name != film.name:
        query_original = original_name
        if film.year:
            query_original += f' ({film.year})'
        queries.add(query_original)

    return queries
