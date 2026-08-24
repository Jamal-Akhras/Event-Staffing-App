from __future__ import annotations

from functools import lru_cache

from botocore.config import Config

from apps.api.src.storage.config import get_storage_settings
from apps.api.src.storage.local_object_storage import LocalObjectStorage
from apps.api.src.storage.object_storage import ObjectStorage
from apps.api.src.storage.s3_object_storage import S3ObjectStorage


@lru_cache(maxsize=1)
def get_object_storage() -> ObjectStorage:
    settings = get_storage_settings()
    if settings.backend == "local":
        return LocalObjectStorage(settings.local_directory)

    import boto3

    client = boto3.client(
        "s3",
        endpoint_url=settings.endpoint_url or None,
        region_name=settings.region or None,
        aws_access_key_id=settings.access_key_id,
        aws_secret_access_key=settings.secret_access_key,
        config=Config(signature_version="s3v4"),
    )
    return S3ObjectStorage(client, settings.bucket, settings.public_base_url)
