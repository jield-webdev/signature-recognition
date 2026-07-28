import numpy as np
from fastapi import UploadFile

from file.errors import (
    EmptyFileError,
    InputTooLargeError,
    InvalidImageError,
    UnsupportedContentTypeError,
)
from limits import MAX_IMAGE_PIXELS, MAX_UPLOAD_BYTES
from opencv_config import cv2
from cv2.typing import MatLike

SUPPORTED_IMAGE_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/bmp",
    "image/tiff",
    "image/webp",
}


def _matches_declared_type(contents: bytes, content_type: str) -> bool:
    if content_type == "image/png":
        return contents.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/jpeg":
        return contents.startswith(b"\xff\xd8\xff")
    if content_type == "image/bmp":
        return contents.startswith(b"BM")
    if content_type == "image/tiff":
        return contents.startswith((b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"))
    return len(contents) >= 12 and contents[:4] == b"RIFF" and contents[8:12] == b"WEBP"


async def parse_image(file: UploadFile) -> MatLike:
    if file.size is not None and file.size <= 0:
        raise EmptyFileError("File is empty.")
    if file.size is not None and file.size > MAX_UPLOAD_BYTES:
        raise InputTooLargeError(f"File exceeds {MAX_UPLOAD_BYTES} byte limit.")

    if file.content_type not in SUPPORTED_IMAGE_CONTENT_TYPES:
        raise UnsupportedContentTypeError(
            f"Unsupported content type '{file.content_type}'. "
            f"Expected one of: {', '.join(sorted(SUPPORTED_IMAGE_CONTENT_TYPES))}."
        )

    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    if not contents:
        raise EmptyFileError("File is empty.")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise InputTooLargeError(f"File exceeds {MAX_UPLOAD_BYTES} byte limit.")
    if not _matches_declared_type(contents, file.content_type):
        raise InvalidImageError("File content does not match declared content type.")

    image_array = np.frombuffer(contents, dtype=np.uint8)
    try:
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    except cv2.error as error:
        raise InvalidImageError("Invalid image file.") from error

    if image is None:
        raise InvalidImageError("Invalid image file.")
    if image.shape[0] * image.shape[1] > MAX_IMAGE_PIXELS:
        raise InputTooLargeError(f"Image exceeds {MAX_IMAGE_PIXELS} pixel limit.")

    return image
