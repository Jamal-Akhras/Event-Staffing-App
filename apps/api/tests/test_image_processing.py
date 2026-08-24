from __future__ import annotations

import struct
import zlib
from io import BytesIO

import pytest
from fastapi import HTTPException
from PIL import Image

from apps.api.src.services.image_processing import (
    MAX_OUTPUT_EDGE,
    MAX_SOURCE_PIXELS,
    process_image,
)


def _encode(image: Image.Image, image_format: str, **options) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format=image_format, **options)
    return buffer.getvalue()


def _png_header_claiming(width: int, height: int) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    chunk = b"IHDR" + ihdr
    return (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", len(ihdr))
        + chunk
        + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)
    )


def test_jpeg_is_reencoded_without_exif_metadata() -> None:
    exif = Image.Exif()
    exif[0x010F] = "SecretCamera"
    exif[0x0112] = 6
    source = _encode(Image.new("RGB", (40, 20), (10, 20, 30)), "JPEG", exif=exif.tobytes())

    processed = process_image(source)

    output = Image.open(BytesIO(processed.data))
    assert processed.content_type == "image/jpeg"
    assert processed.extension == ".jpg"
    assert output.getexif().get(0x010F) is None
    assert (processed.width, processed.height) == (20, 40)


def test_png_keeps_alpha_and_drops_text_chunks() -> None:
    from PIL import PngImagePlugin

    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Comment", "private note")
    source = _encode(Image.new("RGBA", (16, 16), (0, 0, 0, 0)), "PNG", pnginfo=metadata)

    processed = process_image(source)

    output = Image.open(BytesIO(processed.data))
    assert processed.content_type == "image/png"
    assert output.mode == "RGBA"
    assert "Comment" not in output.info


def test_webp_roundtrip() -> None:
    processed = process_image(_encode(Image.new("RGB", (12, 12), (1, 2, 3)), "WEBP"))

    assert processed.content_type == "image/webp"
    assert processed.extension == ".webp"
    assert Image.open(BytesIO(processed.data)).format == "WEBP"


def test_oversized_image_is_downscaled_to_max_edge() -> None:
    processed = process_image(_encode(Image.new("RGB", (3000, 1500)), "JPEG"))

    assert processed.width == MAX_OUTPUT_EDGE
    assert processed.height == MAX_OUTPUT_EDGE // 2


def test_valid_magic_bytes_with_garbage_body_are_rejected() -> None:
    with pytest.raises(HTTPException) as excinfo:
        process_image(b"\xff\xd8\xff" + b"not-really-a-jpeg" * 10)

    assert excinfo.value.status_code == 400


def test_decompression_bomb_header_is_rejected_before_decode() -> None:
    edge = int(MAX_SOURCE_PIXELS**0.5) + 100
    with pytest.raises(HTTPException) as excinfo:
        process_image(_png_header_claiming(edge, edge))

    assert excinfo.value.status_code == 400


def test_unsupported_format_is_rejected() -> None:
    with pytest.raises(HTTPException) as excinfo:
        process_image(_encode(Image.new("RGB", (4, 4)), "BMP"))

    assert excinfo.value.status_code == 400
