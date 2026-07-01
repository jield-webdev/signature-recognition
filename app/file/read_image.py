import cv2
import numpy as np
from cv2.typing import MatLike

from fastapi import UploadFile

from file.errors import EmptyFileError, InvalidImageError, UnsupportedContentTypeError


async def read_image(file: UploadFile) -> MatLike:
    if file.size is not None and file.size <= 0:
        raise EmptyFileError("File is empty.")

    if file.content_type != "image/png":
        raise UnsupportedContentTypeError(
            f"Unsupported content type '{file.content_type}'. Expected 'image/png'."
        )

    contents = await file.read()
    if not contents:
        raise EmptyFileError("File is empty.")

    image_array = np.frombuffer(contents, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise InvalidImageError("Invalid image file.")

    return image
