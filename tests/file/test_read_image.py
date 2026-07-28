import cv2
import numpy as np
import pytest

import file.read_image as read_image
from file.read_image import parse_image


def _png_bytes(width: int = 2, height: int = 2) -> bytes:
    ok, encoded = cv2.imencode(
        ".png", np.full((height, width, 3), 255, dtype=np.uint8)
    )
    assert ok
    return encoded.tobytes()


async def test_rejects_upload_larger_than_limit_before_read(monkeypatch):
    class TrackingUpload:
        content_type = "image/png"
        size = 5
        read_called = False

        async def read(self, size: int = -1) -> bytes:
            self.read_called = True
            return _png_bytes()

    monkeypatch.setattr(read_image, "MAX_UPLOAD_BYTES", 4, raising=False)
    file = TrackingUpload()

    with pytest.raises(ValueError, match="exceeds"):
        await parse_image(file)

    assert file.read_called is False


async def test_rejects_image_larger_than_pixel_limit(upload_file_factory, monkeypatch):
    monkeypatch.setattr(read_image, "MAX_IMAGE_PIXELS", 1, raising=False)
    file = upload_file_factory(_png_bytes(), content_type="image/png")

    with pytest.raises(ValueError, match="pixel"):
        await parse_image(file)


async def test_rejects_content_that_does_not_match_declared_type(upload_file_factory):
    file = upload_file_factory(_png_bytes(), content_type="image/jpeg")

    with pytest.raises(ValueError, match="does not match"):
        await parse_image(file)


@pytest.mark.parametrize(
    ("extension", "content_type"),
    [
        (".jpg", "image/jpeg"),
        (".bmp", "image/bmp"),
        (".tiff", "image/tiff"),
        (".webp", "image/webp"),
    ],
)
async def test_accepts_each_supported_image_format(
    upload_file_factory, extension, content_type
):
    ok, encoded = cv2.imencode(
        extension, np.full((2, 2, 3), 255, dtype=np.uint8)
    )
    assert ok

    image = await parse_image(
        upload_file_factory(encoded.tobytes(), content_type=content_type)
    )

    assert image.shape == (2, 2, 3)
