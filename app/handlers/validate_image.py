import base64

import numpy as np
from fastapi import HTTPException, UploadFile, status

from boxes import detect_boxes
from file.errors import (
    EmptyFileError,
    InputTooLargeError,
    InvalidImageError,
    UnsupportedContentTypeError,
)
from file.read_image import parse_image
from opencv_config import cv2


WEBP_QUALITY = 80


def _encode_webp(crop: np.ndarray) -> str:
    ok, buf = cv2.imencode(".webp", crop, [cv2.IMWRITE_WEBP_QUALITY, WEBP_QUALITY])
    if not ok:
        raise RuntimeError("Failed to encode box crop.")
    return base64.b64encode(buf.tobytes()).decode()


async def validate_image_handler(file: UploadFile):
    try:
        image = await parse_image(file)
    except EmptyFileError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except InputTooLargeError as error:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(error),
        ) from error
    except UnsupportedContentTypeError as error:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(error),
        ) from error
    except InvalidImageError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    try:
        boxes = await detect_boxes(image)
    except InputTooLargeError as error:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(error),
        ) from error

    return {
        "boxes": [
            {
                "box_id": box["box_id"],
                "image": _encode_webp(box["image"]),
                "is_signed": box["is_signed"],
            }
            for box in boxes
        ]
    }
