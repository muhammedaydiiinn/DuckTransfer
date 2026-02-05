"""FTP connector implementation."""

import ftplib
import os
from typing import Optional, Callable

from .base import BaseConnector, RemoteFile


class FTPConnector(BaseConnector):
    """FTP protocol connector. use_ssl=True for FTP-SSL (Explicit AUTH TLS)."""

    def __init__(self):
        self._ftp: Optional[ftplib.FTP] = None
        self._current_path = "/"

    def connect(
        self,
        host: str,
        port: int = 21,
        username: str = "",
        password: str = "",
        use_ssl: bool = False,
        **kwargs
    ) -> bool:
        try:
            if use_ssl:
                self._ftp = ftplib.FTP_TLS()
                self._ftp.connect(host, port, timeout=30)
                self._ftp.auth()
                self._ftp.login(username or "anonymous", password or "anonymous@")
                self._ftp.prot_p()
            else:
                self._ftp = ftplib.FTP()
                self._ftp.connect(host, port, timeout=30)
                self._ftp.login(username or "anonymous", password or "anonymous@")
            self._ftp.encoding = "utf-8"
            self._current_path = self._ftp.pwd()
            return True
        except Exception as e:
            raise ConnectionError(f"FTP bağlantı hatası: {str(e)}")

    def disconnect(self) -> None:
        if self._ftp:
            try:
                self._ftp.quit()
            except Exception:
                pass
            self._ftp = None
        self._current_path = "/"

    def is_connected(self) -> bool:
        return self._ftp is not None

    def _parse_mlsd(self, line: str) -> Optional[RemoteFile]:
        """Parse MLSD response line."""
        try:
            facts, name = line.split(" ", 1)
            name = name.strip()
            if name in (".", ".."):
                return None

            facts_dict = {}
            for fact in facts.split(";"):
                if "=" in fact:
                    k, v = fact.split("=", 1)
                    facts_dict[k.lower()] = v

            is_dir = facts_dict.get("type", "").upper() == "DIR"
            size = int(facts_dict.get("size", 0))
            modify = facts_dict.get("modify", "")

            return RemoteFile(
                name=name,
                path=os.path.join(self._current_path, name).replace("\\", "/"),
                size=size,
                is_directory=is_dir,
                modified=modify[:8] + " " + modify[8:10] + ":" + modify[10:12] + ":" + modify[12:14] if len(modify) >= 14 else None
            )
        except Exception:
            return None

    def list_directory(self, path: str = "/") -> list[RemoteFile]:
        if not self._ftp:
            return []

        try:
            if path and path != self._current_path:
                self._ftp.cwd(path)
                self._current_path = path

            files = []
            try:
                for line in self._ftp.mlsd():
                    if line[0] in (".", ".."):
                        continue
                    name, facts = line
                    is_dir = facts.get("type", "").upper() == "DIR"
                    size = int(facts.get("size", 0))
                    modify = facts.get("modify", "")
                    if len(modify) >= 14:
                        mod_str = f"{modify[6:8]}.{modify[4:6]}.{modify[:4]} {modify[8:10]}:{modify[10:12]}:{modify[12:14]}"
                    else:
                        mod_str = None

                    files.append(RemoteFile(
                        name=name,
                        path=os.path.join(self._current_path, name).replace("\\", "/"),
                        size=size,
                        is_directory=is_dir,
                        modified=mod_str
                    ))
            except ftplib.error_perm:
                for line in self._ftp.nlst():
                    if line in (".", ".."):
                        continue
                    full_path = os.path.join(self._current_path, line).replace("\\", "/")
                    try:
                        self._ftp.cwd(line)
                        self._ftp.cwd("..")
                        is_dir = True
                    except Exception:
                        is_dir = False
                    files.append(RemoteFile(
                        name=line,
                        path=full_path,
                        size=0,
                        is_directory=is_dir,
                        modified=None
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
        if not self._ftp:
            return False

        try:
            size = self._ftp.size(remote_path)
        except Exception:
            size = 0

        downloaded = [0]

        def callback(data: bytes):
            downloaded[0] += len(data)
            if progress_callback and size > 0:
                progress_callback(downloaded[0], size)

        with open(local_path, "wb") as f:
            def write_and_cb(d):
                f.write(d)
                if progress_callback:
                    callback(d)
            self._ftp.retrbinary(f"RETR {remote_path}", write_and_cb)
        return True

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        if not self._ftp:
            return False

        size = os.path.getsize(local_path)
        uploaded = [0]

        def callback(data: bytes):
            uploaded[0] += len(data)
            if progress_callback:
                progress_callback(uploaded[0], size)

        with open(local_path, "rb") as f:
            self._ftp.storbinary(
                f"STOR {remote_path}",
                f,
                blocksize=8192,
                callback=callback if progress_callback else None
            )
        return True

    def delete(self, path: str) -> bool:
        if not self._ftp:
            return False
        try:
            try:
                self._ftp.delete(path)
            except ftplib.error_perm:
                self._ftp.rmd(path)
            return True
        except Exception:
            return False

    def create_directory(self, path: str) -> bool:
        if not self._ftp:
            return False
        try:
            self._ftp.mkd(path)
            return True
        except Exception:
            return False

    def get_current_path(self) -> str:
        if self._ftp:
            try:
                self._current_path = self._ftp.pwd()
            except Exception:
                pass
        return self._current_path
