from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_SOURCE_PIXELS = 40_000_000
MAX_OUTPUT_EDGE = 2048
LOSSY_QUALITY = 85

Image.MAX_IMAGE_PIXELS = MAX_SOURCE_PIXELS

_OUTPUT_TARGETS = {
    "JPEG": (".jpg", "image/jpeg"),
    "PNG": (".png", "image/png"),
    "WEBP": (".webp", "image/webp"),
}
_ALPHA_MODES = {"RGBA", "LA", "PA"}


@dataclass(frozen=True)
class ProcessedImage:
    data: bytes
    extension: str
    content_type: str
    width: int
    height: int


def process_image(data: bytes) -> ProcessedImage:
    try:
        with Image.open(BytesIO(data)) as source:
            source_format = source.format
            if source_format not in _OUTPUT_TARGETS:
                raise HTTPException(400, "Unsupported image format. Use jpg, png, or webp.")
            width, height = source.size
            if width * height > MAX_SOURCE_PIXELS:
                raise HTTPException(400, "Image dimensions are too large.")
            oriented = ImageOps.exif_transpose(source)
            oriented.load()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError) as exc:
        raise HTTPException(400, "File content is not a valid image.") from exc

    oriented.thumbnail((MAX_OUTPUT_EDGE, MAX_OUTPUT_EDGE), Image.Resampling.LANCZOS)
    extension, content_type = _OUTPUT_TARGETS[source_format]
    encoded = _encode(oriented, source_format)
    return ProcessedImage(encoded, extension, content_type, oriented.width, oriented.height)


def _encode(image: Image.Image, output_format: str) -> bytes:
    buffer = BytesIO()
    if output_format == "JPEG":
        image.convert("RGB").save(buffer, format="JPEG", quality=LOSSY_QUALITY, optimize=True)
    elif output_format == "PNG":
        _flatten_mode(image).save(buffer, format="PNG", optimize=True)
    else:
        _flatten_mode(image).save(buffer, format="WEBP", quality=LOSSY_QUALITY, method=4)
    return buffer.getvalue()


def _flatten_mode(image: Image.Image) -> Image.Image:
    has_alpha = image.mode in _ALPHA_MODES or (image.mode == "P" and "transparency" in image.info)
    return image.convert("RGBA" if has_alpha else "RGB")
