from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from apps.api.src.services.image_processing import ProcessedImage, process_image

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_BYTES = 10 * 1024 * 1024
_CHUNK_SIZE = 64 * 1024


def validate_extension(filename: str | None) -> str:
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Unsupported image format. Use jpg, png, or webp.")
    return ext


async def read_capped_image(file: UploadFile) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_BYTES:
            raise HTTPException(400, "File too large (max 10 MB).")
        chunks.append(chunk)

    data = b"".join(chunks)
    image_content_type(data, validate_extension(file.filename))
    return data


async def read_processed_image(file: UploadFile) -> ProcessedImage:
    data = await read_capped_image(file)
    return await run_in_threadpool(process_image, data)


def image_content_type(data: bytes, extension: str) -> str:
    if data.startswith(b"RIFF"):
        if len(data) >= 12 and data[8:12] == b"WEBP":
            detected_extension = ".webp"
            content_type = "image/webp"
        else:
            raise HTTPException(400, "File content is not a valid image.")
    elif data.startswith(b"\xff\xd8\xff"):
        detected_extension = ".jpg"
        content_type = "image/jpeg"
    elif data.startswith(b"\x89PNG\r\n\x1a\n"):
        detected_extension = ".png"
        content_type = "image/png"
    else:
        raise HTTPException(400, "File content is not a valid image.")
    normalized_extension = ".jpg" if extension == ".jpeg" else extension
    if normalized_extension != detected_extension:
        raise HTTPException(400, "File extension does not match the image content.")
    return content_type
