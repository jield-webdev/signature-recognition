import base64

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile, status

from aruco.detect_boxes import detect_boxes
from file.errors import EmptyFileError, InvalidImageError, UnsupportedContentTypeError
from file.read_image import parse_image


def _encode_png(crop: np.ndarray) -> str:
    ok, buf = cv2.imencode(".png", crop)
    return base64.b64encode(buf.tobytes()).decode()


async def validate_image_handler(file: UploadFile):
    try:
        image = await parse_image(file)
    except EmptyFileError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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

    boxes = await detect_boxes(image)

    return {
        "boxes": [
            {"box_id": box["box_id"], "image": _encode_png(box["image"])}
            for box in boxes
        ]
    }
