"""SQLAlchemy ORM models for the database."""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Table
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
    poster: Mapped[str | None] = mapped_column(String, nullable=True)
    rating: Mapped[str | None] = mapped_column(String, nullable=True)

    torrents: Mapped[list['Torrent']] = relationship('Torrent', back_populates='film')

    def __str__(self) -> str:
        return self.name


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
    sz: Mapped[int] = mapped_column(Integer, nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    downloaded: Mapped[bool] = mapped_column(Boolean, default=False)
    seeds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    film: Mapped['Film'] = relationship('Film', back_populates='torrents')

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
    chat_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)

    created_searches: Mapped[list['Search']] = relationship('Search', back_populates='creator')
    subscribed_searches: Mapped[list['Search']] = relationship(
        'Search', secondary=subscribes_table, back_populates='subscribers'
    )


class Search(Base):
    """Search model representing scheduled searches."""

    __tablename__ = 'searches'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    cron: Mapped[str] = mapped_column(String, nullable=False)
    last_success: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    creator_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    query: Mapped[str | None] = mapped_column(String, nullable=True)

    creator: Mapped[Optional['User']] = relationship('User', back_populates='created_searches')
    subscribers: Mapped[list['User']] = relationship(
        'User', secondary=subscribes_table, back_populates='subscribed_searches'
    )

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
