"""Amazon S3 connector implementation."""

import os
from typing import Optional, Callable

import boto3
from botocore.exceptions import ClientError

from .base import BaseConnector, RemoteFile


class S3Connector(BaseConnector):
    """Amazon S3 connector."""

    def __init__(self):
        self._s3 = None
        self._bucket: Optional[str] = None
        self._current_path = ""
        self._region = "us-east-1"

    def connect(
        self,
        access_key: str = "",
        secret_key: str = "",
        region: str = "us-east-1",
        bucket: str = "",
        **kwargs
    ) -> bool:
        try:
            if access_key and secret_key:
                self._s3 = boto3.client(
                    "s3",
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region
                )
            else:
                self._s3 = boto3.client("s3", region_name=region)

            self._bucket = bucket
            self._region = region
            self._current_path = ""

            if bucket:
                self._s3.head_bucket(Bucket=bucket)

            return True
        except ClientError as e:
            raise ConnectionError(f"S3 bağlantı hatası: {e.response['Error']['Message']}")
        except Exception as e:
            raise ConnectionError(f"S3 bağlantı hatası: {str(e)}")

    def disconnect(self) -> None:
        self._s3 = None
        self._bucket = None
        self._current_path = ""

    def is_connected(self) -> bool:
        return self._s3 is not None and self._bucket is not None

    def _normalize_path(self, path: str) -> str:
        path = path.strip("/")
        return path + "/" if path else ""

    def list_directory(self, path: str = "/") -> list[RemoteFile]:
        if not self._s3 or not self._bucket:
            return []

        prefix = self._normalize_path(path) if path else self._current_path

        try:
            paginator = self._s3.get_paginator("list_objects_v2")
            files = []
            seen_dirs = set()

            for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix, Delimiter="/"):
                for obj in page.get("CommonPrefixes", []):
                    dir_path = obj["Prefix"]
                    dir_name = dir_path.rstrip("/").split("/")[-1]
                    if dir_name and dir_path not in seen_dirs:
                        seen_dirs.add(dir_path)
                        files.append(RemoteFile(
                            name=dir_name + "/",
                            path=dir_path,
                            size=0,
                            is_directory=True,
                            modified=None
                        ))

                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key == prefix or key.endswith("/"):
                        continue
                    name = key.split("/")[-1]
                    files.append(RemoteFile(
                        name=name,
                        path=key,
                        size=obj.get("Size", 0),
                        is_directory=False,
                        modified=obj.get("LastModified", "").strftime("%Y-%m-%d %H:%M") if obj.get("LastModified") else None
                    ))

            return sorted(files, key=lambda x: (not x.is_directory, x.name.lower()))
        except ClientError as e:
            raise RuntimeError(f"S3 listeleme hatası: {e.response['Error']['Message']}")

    def download_file(
        self,
        remote_path: str,
        local_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        if not self._s3 or not self._bucket:
            return False

        try:
            response = self._s3.get_object(Bucket=self._bucket, Key=remote_path)
            total_size = response["ContentLength"]
            body = response["Body"]
            downloaded = 0

            os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)

            with open(local_path, "wb") as f:
                for chunk in body.iter_chunks(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size)
            return True
        except ClientError as e:
            raise RuntimeError(f"İndirme hatası: {e.response['Error']['Message']}")

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        if not self._s3 or not self._bucket:
            return False

        try:
            size = os.path.getsize(local_path)

            def upload_callback(bytes_transferred):
                if progress_callback:
                    progress_callback(bytes_transferred, size)

            self._s3.upload_file(
                local_path,
                self._bucket,
                remote_path,
                Callback=upload_callback
            )
            if progress_callback:
                progress_callback(size, size)
            return True
        except ClientError as e:
            raise RuntimeError(f"Yükleme hatası: {e.response['Error']['Message']}")

    def delete(self, path: str) -> bool:
        if not self._s3 or not self._bucket:
            return False

        try:
            self._s3.delete_object(Bucket=self._bucket, Key=path.rstrip("/"))
            return True
        except ClientError:
            return False

    def create_directory(self, path: str) -> bool:
        if not self._s3 or not self._bucket:
            return False

        path = path.rstrip("/") + "/"
        try:
            self._s3.put_object(Bucket=self._bucket, Key=path, Body=b"")
            return True
        except ClientError:
            return False

    def get_current_path(self) -> str:
        return self._current_path

    def set_current_path(self, path: str) -> None:
        self._current_path = self._normalize_path(path)

    def list_buckets(self) -> list[str]:
        """List available S3 buckets."""
        if not self._s3:
            return []
        try:
            response = self._s3.list_buckets()
            return [b["Name"] for b in response.get("Buckets", [])]
        except ClientError:
            return []
