"""SFTP (SSH File Transfer Protocol) connector."""

import os
from typing import Optional, Callable

import paramiko

from .base import BaseConnector, RemoteFile


class SFTPConnector(BaseConnector):
    """SFTP protocol connector."""

    def __init__(self):
        self._client: Optional[paramiko.SSHClient] = None
        self._sftp: Optional[paramiko.SFTPClient] = None
        self._current_path = "/"

    def connect(
        self,
        host: str,
        port: int = 22,
        username: str = "",
        password: str = "",
        **kwargs
    ) -> bool:
        try:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._client.connect(
                hostname=host,
                port=port,
                username=username or "anonymous",
                password=password or "",
                timeout=30,
            )
            self._sftp = self._client.open_sftp()
            self._current_path = self._sftp.normalize(".")
            return True
        except Exception as e:
            raise ConnectionError(f"SFTP bağlantı hatası: {str(e)}")

    def disconnect(self) -> None:
        if self._sftp:
            try:
                self._sftp.close()
            except Exception:
                pass
            self._sftp = None
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
        self._current_path = "/"

    def is_connected(self) -> bool:
        return self._sftp is not None

    def list_directory(self, path: str = "/") -> list[RemoteFile]:
        if not self._sftp:
            return []

        try:
            if path and path != self._current_path:
                self._sftp.chdir(path)
                self._current_path = path

            files = []
            for entry in self._sftp.listdir_attr(self._current_path):
                if entry.filename in (".", ".."):
                    continue
                full_path = os.path.join(self._current_path, entry.filename).replace("\\", "/")
                is_dir = entry.st_mode and (entry.st_mode & 0o170000) == 0o040000
                mod_time = None
                if hasattr(entry, "st_mtime"):
                    from datetime import datetime
                    mod_time = datetime.fromtimestamp(entry.st_mtime).strftime("%Y-%m-%d %H:%M")

                files.append(RemoteFile(
                    name=entry.filename,
                    path=full_path,
                    size=entry.st_size if not is_dir else 0,
                    is_directory=is_dir,
                    modified=mod_time
                ))

            return sorted(files, key=lambda x: (not x.is_directory, x.name.lower()))
        except Exception as e:
            raise RuntimeError(f"Dizin listelenemedi: {str(e)}")

    def download_file(
        self,
        remote_path: str,
        local_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        if not self._sftp:
            return False

        try:
            size = self._sftp.stat(remote_path).st_size
            downloaded = [0]

            def callback(transferred, total):
                downloaded[0] = transferred
                if progress_callback:
                    progress_callback(transferred, total)

            self._sftp.get(remote_path, local_path, callback=callback)
            if progress_callback:
                progress_callback(size, size)
            return True
        except Exception as e:
            raise RuntimeError(f"İndirme hatası: {str(e)}")

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        if not self._sftp:
            return False

        try:
            size = os.path.getsize(local_path)
            uploaded = [0]

            def callback(transferred, total):
                uploaded[0] = transferred
                if progress_callback:
                    progress_callback(transferred, total)

            self._sftp.put(local_path, remote_path, callback=callback)
            if progress_callback:
                progress_callback(size, size)
            return True
        except Exception as e:
            raise RuntimeError(f"Yükleme hatası: {str(e)}")

    def delete(self, path: str) -> bool:
        if not self._sftp:
            return False
        try:
            try:
                self._sftp.remove(path)
            except IOError:
                self._sftp.rmdir(path)
            return True
        except Exception:
            return False

    def create_directory(self, path: str) -> bool:
        if not self._sftp:
            return False
        try:
            self._sftp.mkdir(path)
            return True
        except Exception:
            return False

    def get_current_path(self) -> str:
        if self._sftp:
            try:
                self._current_path = self._sftp.normalize(".")
            except Exception:
                pass
        return self._current_path
