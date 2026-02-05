"""Base connector interface for remote storage backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class RemoteFile:
    """Represents a file or directory on remote storage."""
    name: str
    path: str
    size: int
    is_directory: bool
    modified: Optional[str] = None


class BaseConnector(ABC):
    """Abstract base class for FTP, S3, and other storage connectors."""

    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """Establish connection. Returns True on success."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is active."""
        pass

    @abstractmethod
    def list_directory(self, path: str = "/") -> list[RemoteFile]:
        """List files and directories at the given path."""
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: str, progress_callback=None) -> bool:
        """Download a file from remote to local."""
        pass

    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str, progress_callback=None) -> bool:
        """Upload a file from local to remote."""
        pass

    @abstractmethod
    def delete(self, path: str) -> bool:
        """Delete a file or empty directory."""
        pass

    @abstractmethod
    def create_directory(self, path: str) -> bool:
        """Create a new directory."""
        pass

    @abstractmethod
    def get_current_path(self) -> str:
        """Get current working directory/path."""
        pass
