"""Pydantic schemas for API responses and data models."""

from datetime import date as dt_date
from datetime import datetime
from typing import Literal, TypedDict

from pydantic import BaseModel, ConfigDict
from telegram import InlineKeyboardMarkup


class Notification(TypedDict):
    """TypedDict for notification objects sent to Telegram"""

    type: Literal['photo', 'text']
    media: bytes | str | None
    caption: str
    reply_markup: InlineKeyboardMarkup


class UserResponse(BaseModel):
    """User response model"""

    id: int
    chat_id: int
    name: str | None
    username: str | None
    is_authorized: bool
    is_admin: bool
    is_tfa_enabled: bool
    password: str | None
    language: str

    model_config = ConfigDict(from_attributes=True)


class StatusResponse(BaseModel):
    """Simple status response"""

    status: str
    id: int | None = None
    user: UserResponse | None = None
    category: CategoryResponse | None = None


class CategoryResponse(BaseModel):
    """Category response model"""

    id: int
    name: str
    active: bool
    icon: str | None
    folder: str | None

    model_config = ConfigDict(from_attributes=True)


class SearchResponse(BaseModel):
    """Search response model"""

    id: int
    url: str
    cron: str
    last_success: datetime | None = None
    creator_id: int | None
    query: str | None
    category_id: int | None
    category: str | None

    model_config = ConfigDict(from_attributes=True)


class FilmSummaryResponse(BaseModel):
    """Film summary response model (no torrents)"""

    id: int
    blake: str
    year: int
    name: str
    ru_name: str | None
    poster: str | None
    rating: str | None
    user_rating: int | None = None
    category_id: int | None

    model_config = ConfigDict(from_attributes=True)


class TorrentResponse(BaseModel):
    """Torrent response model"""

    id: int
    film_id: int
    blake: str
    name: str
    magnet: str
    created: dt_date
    link: str
    sz: int
    approved: bool
    downloaded: bool
    seeds: int | None
    date: datetime | None

    film: FilmSummaryResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class FilmResponse(FilmSummaryResponse):
    """Film response model (with torrents)"""

    torrents: list[TorrentResponse] = []


class TaskExecutionResponse(BaseModel):
    """Task execution response model"""

    id: int
    search_id: int
    status: str
    start_time: datetime
    end_time: datetime | None = None
    result: str | None = None
    progress: int = 0
    search: SearchResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# Solve circular dependencies
FilmResponse.model_rebuild()


class RutorTorrentResponse(BaseModel):
    """Result from live Rutor search"""

    name: str
    size: int
    date: str
    magnet: str
    link: str
    year: str


class TorrentCreateRequest(BaseModel):
    """Request to add a torrent from magnet"""

    magnet: str
    category_id: int | None = None
    film_title: str | None = None
    film_year: int | None = None
    tmdb_id: int | None = None
    torrent_name: str | None = None
    torrent_size: int | None = None
    torrent_link: str | None = None
