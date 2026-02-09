"""Configuration management using pydantic-settings"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Unpack

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

if TYPE_CHECKING:
    from telegram_rutor_bot.db.models import AppConfigUpdate


class SearchConfig(BaseModel):
    """Configuration for a system-defined search"""

    name: str = Field(description='Human-readable name for the search')
    url: str = Field(description='Rutor search URL')
    cron: str = Field(default='*/30 * * * *', description='Cron schedule for the search')


class Settings(BaseSettings):
    """Application settings loaded from environment and config.toml"""

    model_config = SettingsConfigDict(
        toml_file='config.toml',
        env_prefix='RUTOR_BOT_',
        case_sensitive=False,
        extra='ignore',
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            TomlConfigSettingsSource(settings_cls),
        )

    # General settings
    is_configured: bool = Field(default=False, description='Whether the application has been configured')

    # Telegram settings
    telegram_token: str | None = Field(default=None, description='Telegram bot API token')
    unauthorized_message: str = Field(
        default='Unauthorized user, please contact my master', description='Message shown to unauthorized users'
    )
    notification_cron: str = Field(default='0 21 * * *', description='Cron schedule for digest notifications')

    # qBittorrent settings
    qbittorrent_host: str = Field(default='localhost', description='qBittorrent Web UI host')
    qbittorrent_port: int = Field(default=8080, description='qBittorrent Web UI port')
    qbittorrent_username: str = Field(default='admin', description='qBittorrent Web UI username')
    qbittorrent_password: str = Field(default='adminadmin', description='qBittorrent Web UI password')

    # Proxy settings
    proxy: str | None = Field(default=None, description='Proxy URL (e.g., socks5://host:port)')

    # Logging settings
    log_prefix: str = Field(default='rutorbot', description='Log prefix for logger names')
    log_level: int = Field(default=logging.INFO, description='Logging level')

    # Database settings
    database_path: Path = Field(
        default=Path('var/rutor.db'), description='Path to SQLite database file (for local development)'
    )
    database_url: str | None = Field(
        default=None, description='PostgreSQL database URL (e.g., postgresql://user:password@host:5432/dbname)'
    )
    run_migrations: bool = Field(default=False, description='Run database migrations on startup (only for bot mode)')

    # Parser settings
    timeout: int = Field(default=60, description='Request timeout in seconds')
    size_limit: int = Field(default=0, description='Torrent size limit (0 = unlimited)')

    # TaskIQ settings
    redis_url: str | None = Field(default=None, description='Redis URL for TaskIQ broker (e.g., redis://host:6379)')
    secret_key: str = Field(default='rutor-bot-secret-key-change-me', description='Secret key for JWT')

    # TMDB settings
    tmdb_api_key: str | None = Field(default=None, description='TMDB API Key')
    tmdb_session_id: str | None = Field(default=None, description='TMDB Session ID')
    tmdb_language: str = Field(default='ru-RU', description='Language for TMDB results')

    # Genre to category mapping
    genre_mapping: dict[str, list[str]] = Field(
        default_factory=lambda: {
            'CARTOONS': ['мультфильм', 'мультсериал', 'анимация', 'animation', 'аниме', 'anime'],
            'TVSHOWS': ['сериал', 'series', 'tv show', 'тв-шоу'],
        },
        description='Map genres to qBittorrent categories',
    )

    # Title pattern to category mapping
    title_patterns: dict[str, list[str]] = Field(
        default_factory=lambda: {
            'TVSHOWS': ['s01', 's02', 's03', 's04', 's05', 'season', 'сезон', 'серия', 'серии'],
            'CARTOONS': ['мультфильм', 'мультсериал', 'animation', 'cartoon', 'аниме', 'anime'],
        },
        description='Title patterns that indicate category',
    )

    @field_validator('database_path', mode='before')
    @classmethod
    def resolve_database_path(cls, v: str | Path) -> Path:
        """Resolve database path relative to project root"""
        path = Path(v)
        if not path.is_absolute():
            # Make path relative to project root (3 levels up from this file)
            project_root = Path(__file__).parent.parent.parent
            path = project_root / path
        return path

    @field_validator('log_level', mode='before')
    @classmethod
    def parse_log_level(cls, v: str | int) -> int:
        """Parse log level from string or int"""
        if isinstance(v, str):
            return getattr(logging, v.upper(), logging.INFO)
        return v

    def refresh(self, **data: Unpack[AppConfigUpdate]) -> None:
        """Update settings in-place from dictionary."""
        # Filter valid keys to avoid errors
        model_fields = self.model_fields.keys()
        valid_data = {k: v for k, v in data.items() if k in model_fields}

        # Pydantic v2 usually recommends model_copy(update=data) but for in-place we must iterate
        # Or better: create a new instance and copy values?
        # But we want to keep the Reference to 'settings'
        for key, value in valid_data.items():
            setattr(self, key, value)

        # Re-evaluate is_configured logic if needed, but it's a field now.

    # System Searches
    searches: list[SearchConfig] = Field(default_factory=list, description='List of system-defined searches')


# Global settings instance
settings = Settings()


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get global settings instance."""
    return settings
