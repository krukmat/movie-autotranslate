from __future__ import annotations

import io
from pathlib import Path

from minio import Minio

from ..config import get_settings

settings = get_settings()

_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=False,
)


def ensure_bucket(bucket: str) -> None:
    if not _client.bucket_exists(bucket):
        _client.make_bucket(bucket)


def download_to_path(bucket: str, object_name: str, destination: Path) -> Path:
    ensure_bucket(bucket)
    destination.parent.mkdir(parents=True, exist_ok=True)
    _client.fget_object(bucket, object_name, destination.as_posix())
    return destination


def upload_from_path(bucket: str, object_name: str, file_path: Path, content_type: str = "application/octet-stream") -> None:
    ensure_bucket(bucket)
    _client.fput_object(bucket, object_name, file_path.as_posix(), content_type=content_type)


def upload_bytes(bucket: str, object_name: str, payload: bytes, content_type: str) -> None:
    ensure_bucket(bucket)
    _client.put_object(
        bucket,
        object_name,
        io.BytesIO(payload),
        length=len(payload),
        content_type=content_type,
    )
