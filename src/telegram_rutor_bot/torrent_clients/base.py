"""Base torrent client interface"""

from abc import ABC, abstractmethod
from typing import Any, Protocol


class TorrentInfo(Protocol):
    """Protocol for torrent information"""

    id: str | int
    name: str
    size: int
    progress: float
    status: str
    download_rate: int
    upload_rate: int


class TorrentClientError(Exception):
    """Base exception for torrent client errors"""


class TorrentClient(ABC):
    """Abstract base class for torrent clients"""

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the torrent client"""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the torrent client"""

    @abstractmethod
    async def add_torrent(
        self,
        magnet_link: str,
        download_dir: str | None = None,
        category: str | None = None,
        rename: str | None = None,
        ratio_limit: float | None = None,
        seed_time_limit: int | None = None,
        inactive_seeding_time_limit: int | None = None,
    ) -> dict[str, Any]:
        """Add a torrent by magnet link

        Args:
            magnet_link: Magnet link to add
            download_dir: Optional download directory
            category: Optional category for organizing torrents
            rename: Optional name to rename the torrent to
            ratio_limit: Ratio limit to stop seeding
            seed_time_limit: Time limit to stop seeding (minutes)
            inactive_seeding_time_limit: Inactive time limit to stop seeding (minutes)

        Returns:
            Dictionary with torrent info (id, name, etc.)
        """

    @abstractmethod
    async def get_torrent(self, torrent_id: str | int) -> dict[str, Any] | None:
        """Get information about a specific torrent

        Args:
            torrent_id: ID of the torrent

        Returns:
            Dictionary with torrent info or None if not found
        """

    @abstractmethod
    async def list_torrents(self) -> list[dict[str, Any]]:
        """List all torrents

        Returns:
            List of dictionaries with torrent info
        """

    @abstractmethod
    async def remove_torrent(self, torrent_id: str | int, delete_files: bool = False) -> bool:
        """Remove a torrent

        Args:
            torrent_id: ID of the torrent to remove
            delete_files: Whether to delete downloaded files

        Returns:
            True if successful, False otherwise
        """

    @abstractmethod
    async def pause_torrent(self, torrent_id: str | int) -> bool:
        """Pause a torrent

        Args:
            torrent_id: ID of the torrent to pause

        Returns:
            True if successful, False otherwise
        """

    @abstractmethod
    async def resume_torrent(self, torrent_id: str | int) -> bool:
        """Resume a torrent

        Args:
            torrent_id: ID of the torrent to resume

        Returns:
            True if successful, False otherwise
        """

    @abstractmethod
    async def get_app_preferences(self) -> dict[str, Any]:
        """Get application preferences (qBittorrent specific)"""

    @abstractmethod
    async def set_app_preferences(self, prefs: dict[str, Any]) -> None:
        """Set application preferences (qBittorrent specific)"""
