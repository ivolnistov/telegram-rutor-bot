"""SQLAlchemy ORM models for the database."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TypedDict

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""


subscribes_table = Table(
    'subscribes',
    Base.metadata,
    Column('search_id', Integer, ForeignKey('searches.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
)


class Film(Base):
    """Film model representing movie information."""

    __tablename__ = 'films'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    blake: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    ru_name: Mapped[str | None] = mapped_column(String, nullable=True)
    original_title: Mapped[str | None] = mapped_column(String, nullable=True)
    poster: Mapped[str | None] = mapped_column(String, nullable=True)
    country: Mapped[str | None] = mapped_column(String, nullable=True)
    rating: Mapped[str | None] = mapped_column(String, nullable=True)
    kp_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    user_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('categories.id'), nullable=True)
    tmdb_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tmdb_media_type: Mapped[str | None] = mapped_column(String, default='movie', nullable=True)
    genres: Mapped[str | None] = mapped_column(String, nullable=True)  # Comma-separated list
    monitored: Mapped[bool] = mapped_column(Boolean, default=False)
    last_search: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Watchlist fields
    watch_status: Mapped[str | None] = mapped_column(String, default='none')  # none, watching, downloaded
    voiceover_filter: Mapped[str | None] = mapped_column(String, nullable=True)
    target_size_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_size_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_size_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    notified: Mapped[bool] = mapped_column(Boolean, default=False)

    torrents: Mapped[list[Torrent]] = relationship('Torrent', back_populates='film')
    category_rel: Mapped[Category | None] = relationship('Category')


# ... (skipping Torrent, User, Category, Search, TaskExecution models) ...


class Torrent(Base):
    """Torrent model representing torrent information."""

    __tablename__ = 'torrents'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    film_id: Mapped[int] = mapped_column(Integer, ForeignKey('films.id'), nullable=False)
    blake: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    magnet: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    created: Mapped[datetime] = mapped_column(Date, nullable=False)
    link: Mapped[str] = mapped_column(String, nullable=False)
    sz: Mapped[int] = mapped_column(BigInteger, nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    downloaded: Mapped[bool] = mapped_column(Boolean, default=False)
    seeds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    film: Mapped[Film] = relationship('Film', back_populates='torrents')

    @property
    def size(self) -> int:
        """Get torrent size in bytes."""
        return self.sz

    @size.setter
    def size(self, value: int) -> None:
        self.sz = value

    def __str__(self) -> str:
        return self.name

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Torrent):
            return self.size < other.size
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        if isinstance(other, Torrent):
            return self.size > other.size
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Torrent):
            return self.id == other.id
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.id)


class User(Base):
    """User model representing Telegram users."""

    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    password: Mapped[str | None] = mapped_column(String, nullable=True)
    is_authorized: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_tfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    language: Mapped[str] = mapped_column(String, default='en')

    created_searches: Mapped[list[Search]] = relationship('Search', back_populates='creator')
    subscribed_searches: Mapped[list[Search]] = relationship(
        'Search', secondary=subscribes_table, back_populates='subscribers'
    )


class Category(Base):
    """Category model for grouping searches."""

    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    icon: Mapped[str | None] = mapped_column(String, nullable=True)
    folder: Mapped[str | None] = mapped_column(String, nullable=True)

    searches: Mapped[list[Search]] = relationship('Search', back_populates='category_rel')


class Search(Base):
    """Search model representing scheduled searches."""

    __tablename__ = 'searches'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    cron: Mapped[str] = mapped_column(String, nullable=False)
    last_success: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    creator_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    query: Mapped[str | None] = mapped_column(String, nullable=True)
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('categories.id'), nullable=True)
    is_series: Mapped[bool] = mapped_column(Boolean, default=False)
    quality_filters: Mapped[str | None] = mapped_column(String, nullable=True)
    translation_filters: Mapped[str | None] = mapped_column(String, nullable=True)

    creator: Mapped[User | None] = relationship('User', back_populates='created_searches')
    category_rel: Mapped[Category | None] = relationship('Category', back_populates='searches')
    subscribers: Mapped[list[User]] = relationship(
        'User', secondary=subscribes_table, back_populates='subscribed_searches'
    )

    @property
    def category(self) -> str | None:
        """Get category name."""
        return self.category_rel.name if self.category_rel else None

    @property
    def cron_tuple(self) -> tuple[str, ...]:
        """Get cron string as tuple."""
        cron_parts = tuple(self.cron.split(' '))
        if len(cron_parts) != 5:
            raise ValueError('Invalid cron')
        return cron_parts

    def __str__(self) -> str:
        return self.url or self.query or ''

    def last_success_from_now(self) -> int | None:
        """Get minutes since last successful search."""
        if self.last_success:
            return int((datetime.now(UTC) - self.last_success).total_seconds())
        return None


class TaskExecution(Base):
    """Task execution model for tracking search jobs."""

    __tablename__ = 'task_executions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    search_id: Mapped[int] = mapped_column(Integer, ForeignKey('searches.id'), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default='pending')  # pending, running, success, failed
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON or text result summary
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    search: Mapped[Search] = relationship('Search')


class AppConfigUpdate(TypedDict, total=False):
    """TypedDict for AppConfig updates."""

    is_configured: bool
    telegram_token: str | None
    unauthorized_message: str | None
    torrent_client: str
    qbittorrent_host: str
    qbittorrent_port: int
    qbittorrent_username: str
    qbittorrent_password: str | None
    transmission_host: str
    transmission_port: int
    transmission_username: str | None
    transmission_password: str | None
    proxy: str | None
    tmdb_api_key: str | None
    tmdb_session_id: str | None
    search_quality_filters: str | None
    search_translation_filters: str | None
    seed_ratio_limit: float
    seed_time_limit: int
    inactive_seeding_time_limit: int


class AppConfig(Base):
    """Application configuration model."""

    __tablename__ = 'config'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Singleton: always ID=1

    # General
    is_configured: Mapped[bool] = mapped_column(Boolean, default=False)

    # Telegram
    telegram_token: Mapped[str | None] = mapped_column(String, nullable=True)
    unauthorized_message: Mapped[str | None] = mapped_column(String, nullable=True)

    # Torrent Client
    torrent_client: Mapped[str] = mapped_column(String, default='qbittorrent')

    # qBittorrent
    qbittorrent_host: Mapped[str] = mapped_column(String, default='localhost')
    qbittorrent_port: Mapped[int] = mapped_column(Integer, default=8080)
    qbittorrent_username: Mapped[str] = mapped_column(String, default='admin')
    qbittorrent_password: Mapped[str | None] = mapped_column(String, default='adminadmin')

    # Transmission
    transmission_host: Mapped[str] = mapped_column(String, default='localhost')
    transmission_port: Mapped[int] = mapped_column(Integer, default=9091)
    transmission_username: Mapped[str | None] = mapped_column(String, nullable=True)
    transmission_password: Mapped[str | None] = mapped_column(String, nullable=True)

    # Secret
    proxy: Mapped[str | None] = mapped_column(String, nullable=True)
    tmdb_api_key: Mapped[str | None] = mapped_column(String, nullable=True)
    tmdb_session_id: Mapped[str | None] = mapped_column(String, nullable=True)

    # Search Filters
    search_quality_filters: Mapped[str | None] = mapped_column(String, nullable=True)
    search_translation_filters: Mapped[str | None] = mapped_column(String, nullable=True)

    # Seed limits
    seed_ratio_limit: Mapped[float] = mapped_column(Float, default=1.0)
    seed_time_limit: Mapped[int] = mapped_column(Integer, default=2880)  # Minutes (48h)
    inactive_seeding_time_limit: Mapped[int] = mapped_column(Integer, default=0)  # Minutes (0 = disabled)
