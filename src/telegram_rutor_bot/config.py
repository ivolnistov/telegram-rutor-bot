"""Configuration management using pydantic-settings"""

import logging
from pathlib import Path

import toml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and config.toml"""

    model_config = SettingsConfigDict(
        toml_file='config.toml',
        env_prefix='RUTOR_BOT_',
        case_sensitive=False,
        extra='ignore',
    )

    # Telegram settings
    telegram_token: str = Field(description='Telegram bot API token')
    unauthorized_message: str = Field(
        default='Unauthorized user, please contact my master', description='Message shown to unauthorized users'
    )
    users_white_list: list[int] = Field(default_factory=list, description='List of authorized Telegram user IDs')

    # Torrent client settings
    torrent_client: str = Field(default='qbittorrent', description='Torrent client to use: qbittorrent or transmission')

    # Transmission settings
    transmission_host: str = Field(default='localhost', description='Transmission RPC host')
    transmission_port: int = Field(default=9091, description='Transmission RPC port')
    transmission_username: str = Field(default='', description='Transmission RPC username')
    transmission_password: str = Field(default='', description='Transmission RPC password')

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

    # Parser settings
    timeout: int = Field(default=60, description='Request timeout in seconds')
    size_limit: int = Field(default=0, description='Torrent size limit (0 = unlimited)')

    # TaskIQ settings
    redis_url: str | None = Field(default=None, description='Redis URL for TaskIQ broker (e.g., redis://host:6379)')

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

    @classmethod
    def from_toml(cls, config_path: str | Path = 'config.toml') -> 'Settings':
        """Load settings from TOML file"""
        config_path = Path(config_path)
        if not config_path.is_absolute():
            # Look for config.toml in project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / config_path

        if config_path.exists():
            config_data = toml.load(config_path)
            return cls(**config_data)
        # If no config file, try to load from environment
        return cls()


# Global settings instance
settings = Settings.from_toml()
