"""FastAPI web application for Telegram Rutor Bot"""

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete, select, update
from sqlalchemy.orm import joinedload

# Import discovery routes
from telegram_rutor_bot.api.routes import discovery
from telegram_rutor_bot.config import settings
from telegram_rutor_bot.config_listener import config_listener_task, refresh_settings_from_db
from telegram_rutor_bot.db import (
    add_search_to_db,
    count_torrents,
    create_category,
    delete_category,
    delete_search,
    get_all_users,
    get_async_session,
    get_categories,
    get_films,
    get_or_create_user_by_chat_id,
    get_search_subscribers,
    get_searches,
    get_torrent_by_id,
    get_torrents,
    get_user,
    init_db,
    search_films,
    search_torrents,
    subscribe,
    unsubscribe,
    update_category,
    update_search,
)
from telegram_rutor_bot.db.models import Category, Film, Search, TaskExecution, Torrent, User
from telegram_rutor_bot.rutor import download_torrent
from telegram_rutor_bot.schemas import (
    CategoryResponse,
    FilmResponse,
    PaginatedTorrentResponse,
    SearchResponse,
    StatusResponse,
    TaskExecutionResponse,
    TorrentResponse,
    UserResponse,
)
from telegram_rutor_bot.tasks.broker import broker
from telegram_rutor_bot.tasks.jobs import (
    execute_search,
    search_film_on_rutor,
)

# Import torrent clients
from telegram_rutor_bot.torrent_clients import get_torrent_client
from telegram_rutor_bot.torrent_clients.base import TorrentClient
from telegram_rutor_bot.web import auth, config_api

# Import authentication dependency
from telegram_rutor_bot.web.auth import get_current_admin_user, get_current_user

# Configure logging
logging.basicConfig(level=settings.log_level)
log = logging.getLogger('rutorbot.web')


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan."""
    # Startup
    init_db()
    await broker.startup()

    # Initialize background tasks set
    app.state.background_tasks = set()

    # Sync config and start listener
    await refresh_settings_from_db()

    # Store reference to prevent garbage collection
    task = asyncio.create_task(config_listener_task())
    app.state.background_tasks.add(task)
    task.add_done_callback(app.state.background_tasks.discard)

    yield
    # Shutdown
    await broker.shutdown()


app = FastAPI(title='Telegram Rutor Bot', lifespan=lifespan)
api_router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # For dev convenience
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@api_router.get('/api/searches', response_model=list[SearchResponse], dependencies=[Depends(get_current_admin_user)])
async def list_searches() -> list[Search]:
    """List all searches."""
    async with get_async_session() as session:
        return await get_searches(session, show_empty=True)


@api_router.post('/api/searches', response_model=StatusResponse, dependencies=[Depends(get_current_admin_user)])
async def create_search(
    url: Annotated[str, Form()],
    cron: Annotated[str, Form()],
    chat_id: Annotated[int | None, Form()] = None,
    new_chat_id: Annotated[int | None, Form()] = None,
    category: Annotated[str | None, Form()] = None,
    quality_filters: Annotated[str | None, Form()] = None,
    translation_filters: Annotated[str | None, Form()] = None,
    is_series: Annotated[bool, Form()] = False,
) -> StatusResponse:
    """Create a new search."""
    target_chat_id = chat_id if chat_id else new_chat_id
    if not target_chat_id:
        raise HTTPException(status_code=400, detail='Chat ID is required')

    async with get_async_session() as session:
        try:
            user = await get_or_create_user_by_chat_id(session, target_chat_id)
            search_id = await add_search_to_db(session, url, cron, user.id, category, is_series=is_series)
            if quality_filters or translation_filters:
                await update_search(
                    session,
                    search_id,
                    quality_filters=quality_filters or None,
                    translation_filters=translation_filters or None,
                )
            await subscribe(session, search_id, user.id)
            return StatusResponse(status='ok', id=search_id)
        except Exception as e:
            log.error('Failed to add search: %s', e)
            raise HTTPException(status_code=400, detail=str(e)) from e


@api_router.patch(
    '/api/searches/{search_id}', response_model=StatusResponse, dependencies=[Depends(get_current_admin_user)]
)
async def update_search_api(
    search_id: int,
    url: Annotated[str | None, Form()] = None,
    cron: Annotated[str | None, Form()] = None,
    category: Annotated[str | None, Form()] = None,
    quality_filters: Annotated[str | None, Form()] = None,
    translation_filters: Annotated[str | None, Form()] = None,
    is_series: Annotated[bool | None, Form()] = None,
) -> StatusResponse:
    """Update a search."""
    async with get_async_session() as session:
        try:
            updated = await update_search(
                session,
                search_id,
                url=url,
                cron=cron,
                category=category,
                quality_filters=quality_filters,
                translation_filters=translation_filters,
                is_series=is_series,
            )
            if not updated:
                raise HTTPException(status_code=404, detail='Search not found')
            return StatusResponse(status='ok')
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e


@api_router.delete(
    '/api/searches/{search_id}', response_model=StatusResponse, dependencies=[Depends(get_current_admin_user)]
)
async def delete_search_api(search_id: int) -> StatusResponse:
    """Delete a search."""
    async with get_async_session() as session:
        await delete_search(session, search_id)
    return StatusResponse(status='ok')


@api_router.post(
    '/api/searches/{search_id}/execute', response_model=StatusResponse, dependencies=[Depends(get_current_admin_user)]
)
async def execute_search_api(
    search_id: int,
    chat_id: Annotated[int, Form()],
    notify: Annotated[bool, Form()] = True,
) -> StatusResponse:
    """Execute a search."""
    async with get_async_session() as session:
        # Check for running or pending tasks
        stmt = select(TaskExecution).where(
            TaskExecution.search_id == search_id, TaskExecution.status.in_(['running', 'pending'])
        )
        if (await session.execute(stmt)).scalars().first():
            raise HTTPException(status_code=409, detail='Search is currently running or pending')

        # Create pending task
        task = TaskExecution(search_id=search_id, status='pending')
        session.add(task)
        await session.commit()

    try:
        await execute_search.kiq(search_id, chat_id if notify else None, task.id)
        return StatusResponse(status='ok')
    except Exception as e:
        log.error('Failed to enqueue search %s: %s', search_id, e)
        async with get_async_session() as session:
            # Mark task as failed so it doesn't block future runs
            # We need to re-fetch or merge because session was closed?
            # get_async_session yields a session. The previous with block closed it.
            # So 'task' is detached.
            # Easiest is to update by ID.
            await session.execute(
                update(TaskExecution)
                .where(TaskExecution.id == task.id)
                .values(status='failed', result=f'Failed to enqueue: {e!s}', end_time=datetime.now(UTC))
            )
            await session.commit()
        raise HTTPException(status_code=500, detail=str(e)) from e


@api_router.get(
    '/api/searches/{search_id}/subscribers',
    response_model=list[UserResponse],
    dependencies=[Depends(get_current_admin_user)],
)
async def list_search_subscribers(search_id: int) -> list[User]:
    """List search subscribers."""
    async with get_async_session() as session:
        return await get_search_subscribers(session, search_id)


@api_router.post(
    '/api/searches/{search_id}/subscribers',
    response_model=StatusResponse,
    dependencies=[Depends(get_current_admin_user)],
)
async def add_search_subscriber(search_id: int, chat_id: Annotated[int, Form()]) -> StatusResponse:
    """Add a subscriber."""
    log.info('Adding subscriber: search_id=%s, chat_id=%s', search_id, chat_id)
    async with get_async_session() as session:
        try:
            await get_or_create_user_by_chat_id(session, chat_id)
            success, msg = await subscribe(session, search_id, chat_id)
            if not success:
                raise HTTPException(status_code=400, detail=msg)
            return StatusResponse(status='ok')
        except Exception as e:
            log.exception('Error adding subscriber')
            raise HTTPException(status_code=400, detail=str(e)) from e


@api_router.delete(
    '/api/searches/{search_id}/subscribers/{user_id}',
    response_model=StatusResponse,
    dependencies=[Depends(get_current_admin_user)],
)
async def remove_search_subscriber(search_id: int, user_id: int) -> StatusResponse:
    """Remove a subscriber."""
    async with get_async_session() as session:
        await unsubscribe(session, search_id, user_id)
    return StatusResponse(status='ok')


@api_router.get(
    '/api/torrents', response_model=PaginatedTorrentResponse, dependencies=[Depends(get_current_admin_user)]
)
async def list_torrents(q: str | None = None, limit: int = 50, offset: int = 0) -> PaginatedTorrentResponse:
    """List torrents with server-side pagination and search."""
    async with get_async_session() as session:
        total = await count_torrents(session, query=q)
        if q:
            torrents = await search_torrents(session, q, limit=limit, offset=offset)
        else:
            torrents = await get_torrents(session, limit=limit, offset=offset)
        return PaginatedTorrentResponse(
            items=[TorrentResponse.model_validate(t) for t in torrents],
            total=total,
        )


@api_router.post('/api/films/{film_id}/search', response_model=StatusResponse)
async def search_film_rutor(
    film_id: int, query: str | None = None, user: User = Depends(get_current_user)
) -> StatusResponse:
    """Search for torrents for a specific film on Rutor URL"""
    async with get_async_session() as session:
        film = await session.get(Film, film_id)
        if not film:
            raise HTTPException(status_code=404, detail='Film not found')

        search_query = query or film.name
        if film.year and str(film.year) not in search_query:
            search_query += f' {film.year}'

    # Enqueue task
    await search_film_on_rutor.kiq(film_id, search_query, requester_chat_id=user.chat_id)

    return StatusResponse(status='search_started')


@api_router.post(
    '/api/torrents/{torrent_id}/download', response_model=StatusResponse, dependencies=[Depends(get_current_admin_user)]
)
async def download_torrent_api(torrent_id: int) -> StatusResponse:
    """Download a torrent."""
    async with get_async_session() as session:
        torrent = await get_torrent_by_id(session, torrent_id)
        if not torrent:
            raise HTTPException(status_code=404, detail='Torrent not found')

        try:
            await download_torrent(torrent)

            # Mark as downloaded in DB?
            # The download_torrent function might eventually do this,
            # but currently it just sends to client.
            # We can update the 'downloaded' flag if we want.
            torrent.downloaded = True
            await session.commit()

            return StatusResponse(status='ok')
        except Exception as e:
            log.error('Failed to download torrent %s: %s', torrent_id, e)
            raise HTTPException(status_code=500, detail=str(e)) from e


@api_router.delete(
    '/api/torrents/{torrent_id}', response_model=StatusResponse, dependencies=[Depends(get_current_admin_user)]
)
async def delete_torrent_api(torrent_id: int) -> StatusResponse:
    """Delete a torrent."""
    async with get_async_session() as session:
        await session.execute(delete(Torrent).where(Torrent.id == torrent_id))
        await session.commit()
    return StatusResponse(status='ok')


@api_router.get('/api/films', response_model=list[FilmResponse], dependencies=[Depends(get_current_admin_user)])
async def list_films(q: str | None = None, category_id: int | None = None, limit: int = 50) -> list[Film]:
    """List films with optional filtering."""
    async with get_async_session() as session:
        if q:
            return await search_films(session, q, limit=limit, category_id=category_id)
        return await get_films(session, limit=limit, category_id=category_id)


@api_router.put('/api/films/{film_id}', response_model=StatusResponse, dependencies=[Depends(get_current_admin_user)])
async def update_film(
    film_id: int,
    user_rating: Annotated[int | None, Form()] = None,
) -> StatusResponse:
    """Update a film."""
    async with get_async_session() as session:
        # Check if film exists
        stmt = select(Film).where(Film.id == film_id)
        film = (await session.execute(stmt)).scalars().first()
        if not film:
            raise HTTPException(status_code=404, detail='Film not found')

        if user_rating is not None:
            film.user_rating = user_rating

        await session.commit()
        return StatusResponse(status='ok')


@api_router.get('/api/users', response_model=list[UserResponse], dependencies=[Depends(get_current_admin_user)])
async def list_users() -> list[User]:
    """List all users."""
    async with get_async_session() as session:
        return await get_all_users(session)


@api_router.patch(
    '/api/users/{user_id}/status', response_model=StatusResponse, dependencies=[Depends(get_current_admin_user)]
)
async def update_user_status(
    user_id: int,
    is_authorized: Annotated[bool | None, Form()] = None,
    is_admin: Annotated[bool | None, Form()] = None,
    is_tfa_enabled: Annotated[bool | None, Form()] = None,
    password: Annotated[str | None, Form()] = None,
    language: Annotated[str | None, Form()] = None,
) -> StatusResponse:
    """Update user status."""
    async with get_async_session() as session:
        user = await get_user(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail='User not found')

        if is_authorized is not None:
            user.is_authorized = is_authorized
        if is_admin is not None:
            user.is_admin = is_admin
        if is_tfa_enabled is not None:
            user.is_tfa_enabled = is_tfa_enabled
        if password is not None:
            user.password = password
        if language is not None:
            user.language = language

        await session.commit()
        return StatusResponse(status='ok', user=user)


@api_router.get(
    '/api/categories', response_model=list[CategoryResponse], dependencies=[Depends(get_current_admin_user)]
)
async def list_categories() -> list[Category]:
    """List all categories."""
    async with get_async_session() as session:
        return await get_categories(session)


@api_router.post('/api/categories', response_model=StatusResponse, dependencies=[Depends(get_current_admin_user)])
async def create_category_api(
    name: Annotated[str, Form()],
    icon: Annotated[str | None, Form()] = None,
    folder: Annotated[str | None, Form()] = None,
) -> StatusResponse:
    """Create a new category."""
    async with get_async_session() as session:
        try:
            category = await create_category(session, name, icon, folder)
            return StatusResponse(status='ok', category=category)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e


@api_router.patch(
    '/api/categories/{category_id}', response_model=StatusResponse, dependencies=[Depends(get_current_admin_user)]
)
async def update_category_api(
    category_id: int,
    name: Annotated[str | None, Form()] = None,
    icon: Annotated[str | None, Form()] = None,
    folder: Annotated[str | None, Form()] = None,
    active: Annotated[bool | None, Form()] = None,
) -> StatusResponse:
    """Update an existing category."""
    async with get_async_session() as session:
        try:
            category = await update_category(session, category_id, name, icon, folder, active)
            if not category:
                raise HTTPException(status_code=404, detail='Category not found')
            return StatusResponse(status='ok', category=category)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e


@api_router.delete(
    '/api/categories/{category_id}', response_model=StatusResponse, dependencies=[Depends(get_current_admin_user)]
)
async def delete_category_api(category_id: int) -> StatusResponse:
    """Delete a category."""
    async with get_async_session() as session:
        await delete_category(session, category_id)
    return StatusResponse(status='ok')


@api_router.get(
    '/api/tasks', response_model=list[TaskExecutionResponse], dependencies=[Depends(get_current_admin_user)]
)
async def list_tasks(limit: int = 50) -> list[TaskExecution]:
    """List recent task executions."""
    async with get_async_session() as session:
        stmt = (
            select(TaskExecution)
            .options(joinedload(TaskExecution.search).joinedload(Search.category_rel))
            .order_by(TaskExecution.start_time.desc())
            .limit(limit)
        )
        return list((await session.execute(stmt)).scalars().all())


@api_router.get('/api/downloads', dependencies=[Depends(get_current_admin_user)])
async def get_downloads() -> list[dict[str, Any]]:
    """Get active downloads from torrent client"""
    try:
        client = get_torrent_client()
        await client.connect()
        try:
            return await client.list_torrents()
        finally:
            await client.disconnect()
    except Exception as e:
        log.error('Failed to fetch downloads: %s', e)
        raise HTTPException(status_code=500, detail=f'Failed to fetch downloads: {e}') from e


async def _execute_torrent_action(
    action_fn: Callable[[TorrentClient], Any], torrent_hash: str, action_name: str
) -> dict[str, str]:
    """Helper to execute an action on a torrent client."""
    try:
        client = get_torrent_client()
        await client.connect()
        try:
            await action_fn(client)
            return {'status': 'ok', 'hash': torrent_hash}
        finally:
            await client.disconnect()
    except Exception as e:
        log.error('Failed to %s download %s: %s', action_name, torrent_hash, e)
        raise HTTPException(status_code=500, detail=f'Failed to {action_name} download: {e}') from e


@api_router.delete('/api/downloads/{torrent_hash}', dependencies=[Depends(get_current_admin_user)])
async def delete_download(torrent_hash: str) -> dict[str, str]:
    """Delete a torrent and its files."""
    return await _execute_torrent_action(
        lambda client: client.remove_torrent(torrent_hash, delete_files=True), torrent_hash, 'delete'
    )


@api_router.post('/api/downloads/{torrent_hash}/pause', dependencies=[Depends(get_current_admin_user)])
async def pause_download(torrent_hash: str) -> dict[str, str]:
    """Pause a torrent."""
    return await _execute_torrent_action(lambda client: client.pause_torrent(torrent_hash), torrent_hash, 'pause')


@api_router.post('/api/downloads/{torrent_hash}/resume', dependencies=[Depends(get_current_admin_user)])
async def resume_download(torrent_hash: str) -> dict[str, str]:
    """Resume a torrent."""
    return await _execute_torrent_action(lambda client: client.resume_torrent(torrent_hash), torrent_hash, 'resume')


@app.get('/api/health')
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    health_status = {'status': 'ok', 'postgres': 'ok', 'redis': 'ok', 'qbittorrent': 'ok'}
    try:
        async with get_async_session() as session:
            await session.execute(select(1))
    except Exception as e:
        log.error('Health check failed (Postgres): %s', e)
        health_status['status'] = 'error'
        health_status['postgres'] = 'error'

    try:
        await broker.startup()  # Ensure broker is ready
        # Simplified redis check via broker or direct if possible.
        # Since broker handles connection, if startup worked it's likely ok,
        # but let's assume if we can't connect, broker.startup might have failed earlier or we check connectivity here?
        # A simple ping if we had a redis client would be better.
        # But for now, let's trust the app startup or just return ok for redis if no specific check.
        # Check broker status?
        if not broker.is_worker_process:  # Checking if we can ping?
            # TaskIQ doesn't expose simple ping easily without a task.
            pass
    except Exception as e:
        log.error('Health check failed (Redis): %s', e)
        health_status['status'] = 'error'
        health_status['redis'] = 'error'

    # Check qBittorrent
    try:
        client = get_torrent_client()
        await client.connect()
        await client.disconnect()
    except Exception as e:
        log.error('Health check failed (qBittorrent): %s', e)
        health_status['status'] = 'error'
        health_status['qbittorrent'] = 'error'

    return health_status


# Mount routers unconditionally (Protected by Auth Dependencies)
app.include_router(auth.router)
app.include_router(api_router)
app.include_router(discovery.router)

# Always mount config API to allow checks and re-configuration (if auth permits)
app.include_router(config_api.router)


# Serve React App (only if frontend is built)
_frontend_assets_path = Path('frontend/dist/assets')
if _frontend_assets_path.exists():
    app.mount('/assets', StaticFiles(directory=_frontend_assets_path), name='assets')


def _handle_static_file(base_dir: Path, full_path: str) -> FileResponse | None:
    """Attempt to serve a static file."""
    file_path = (base_dir / full_path).resolve()

    # Prevent path traversal
    if not str(file_path).startswith(str(base_dir)):
        raise HTTPException(status_code=400, detail='Invalid path')

    if file_path.exists() and file_path.is_file():
        if full_path == 'wizard.html' and settings.is_configured:
            raise HTTPException(status_code=404, detail='Not Found')
        return FileResponse(file_path)
    return None


def _serve_wizard() -> FileResponse:
    """Serve the setup wizard."""
    wizard_path = Path('frontend/dist/wizard.html')
    if not wizard_path.exists():
        wizard_path = Path('frontend/public/wizard.html')

    if wizard_path.exists():
        response = FileResponse(wizard_path)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response
    raise HTTPException(status_code=404, detail='Wizard not found')


@app.get('/{full_path:path}', response_model=None)
async def serve_spa(full_path: str) -> FileResponse | HTMLResponse:
    """Serve Single Page Application or Wizard."""
    if full_path.startswith('api'):
        raise HTTPException(status_code=404, detail='API endpoint not found')

    base_dir = Path('frontend/dist').resolve()
    static_resp = _handle_static_file(base_dir, full_path)
    if static_resp:
        return static_resp

    is_wizard_request = full_path in ('wizard', 'wizard.html')

    if settings.is_configured:
        if is_wizard_request:
            raise HTTPException(status_code=404, detail='Not Found')
    else:
        return _serve_wizard()

    index_path = Path('frontend/dist/index.html')
    if index_path.exists():
        response = FileResponse(index_path)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response

    return HTMLResponse('Frontend not built.', status_code=500)
