"""Storage connectors for FTP, SFTP, and S3."""

from .base import BaseConnector, RemoteFile
from .ftp_connector import FTPConnector
from .s3_connector import S3Connector

try:
    from .sftp_connector import SFTPConnector
    HAS_SFTP = True
except ImportError:
    SFTPConnector = None
    HAS_SFTP = False

__all__ = ["BaseConnector", "RemoteFile", "FTPConnector", "SFTPConnector", "S3Connector", "HAS_SFTP"]
