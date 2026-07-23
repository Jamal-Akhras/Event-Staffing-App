from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_CHUNK_SIZE = 64 * 1024

_MAGIC_PREFIXES: tuple[bytes, ...] = (
    b"\xff\xd8\xff",  # JPEG
    b"\x89PNG\r\n\x1a\n",  # PNG
    b"RIFF",  # WEBP container (RIFF....WEBP)
)


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
    _validate_image_magic_bytes(data)
    return data


def _validate_image_magic_bytes(data: bytes) -> None:
    if data.startswith(b"RIFF"):
        if len(data) >= 12 and data[8:12] == b"WEBP":
            return
        raise HTTPException(400, "File content is not a valid image.")
    if any(data.startswith(prefix) for prefix in _MAGIC_PREFIXES):
        return
    raise HTTPException(400, "File content is not a valid image.")
