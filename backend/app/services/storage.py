from __future__ import annotations

import uuid
from typing import List

from minio import Minio

from ..core.config import get_settings

settings = get_settings()

_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=False,
)


def ensure_bucket(bucket: str) -> None:
    """Create bucket if missing."""
    if not _client.bucket_exists(bucket):
        _client.make_bucket(bucket)


def init_multipart_upload(filename: str, content_type: str) -> tuple[str, str]:
    """Start a multipart upload and return (upload_id, object_name).

    For MVP we emulate multipart with a single presigned PUT; the client can still
    split payloads if desired by reusing the signed URL per chunk.
    """
    ensure_bucket(settings.minio_bucket_raw)
    object_name = f"raw/{uuid.uuid4()}/{filename}"
    upload_id = str(uuid.uuid4())
    return upload_id, object_name


def get_presigned_parts(object_name: str, upload_id: str, total_size: int) -> List[dict]:
    """Generate pre-signed URLs for each part."""
    url = _client.presigned_put_object(
        bucket_name=settings.minio_bucket_raw,
        object_name=object_name,
        expires=settings.upload_url_expiry_seconds,
    )
    return [{"partNumber": 1, "uploadUrl": url}]


def complete_multipart_upload(object_name: str, upload_id: str, etags: List[str]) -> str:
    """Finalize multipart upload and return object storage key."""
    ensure_bucket(settings.minio_bucket_raw)
    # MinIO handles the PUT automatically; nothing to finalize in the emulated flow.
    return object_name


def build_signed_url(object_name: str, bucket: str | None = None, expires: int = 3600) -> str:
    """Return a signed download URL for an object."""
    if object_name.startswith("http") or object_name.startswith("/"):
        return object_name
    bucket_name = bucket or settings.minio_bucket_public
    ensure_bucket(bucket_name)
    return _client.get_presigned_url(
        method="GET",
        bucket_name=bucket_name,
        object_name=object_name,
        expires=expires or settings.download_url_expiry_seconds,
    )
