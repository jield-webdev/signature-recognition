import cv2
import numpy as np
from cv2.typing import MatLike

from fastapi import UploadFile

from file.errors import EmptyFileError, InvalidImageError, UnsupportedContentTypeError

SUPPORTED_IMAGE_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/bmp",
    "image/tiff",
    "image/webp",
}


async def parse_image(file: UploadFile) -> MatLike:
    if file.size is not None and file.size <= 0:
        raise EmptyFileError("File is empty.")

    if file.content_type not in SUPPORTED_IMAGE_CONTENT_TYPES:
        raise UnsupportedContentTypeError(
            f"Unsupported content type '{file.content_type}'. "
            f"Expected one of: {', '.join(sorted(SUPPORTED_IMAGE_CONTENT_TYPES))}."
        )

    contents = await file.read()
    if not contents:
        raise EmptyFileError("File is empty.")

    image_array = np.frombuffer(contents, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise InvalidImageError("Invalid image file.")

    if len(image.shape) == 2:  # Grayscale image
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif image.shape[2] == 4:  # RGBA image
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)

    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    return image
