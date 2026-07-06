import cv2
from fastapi import HTTPException, UploadFile, status
from aruco.detect_markers import detect_markers
from file.errors import EmptyFileError, InvalidImageError, UnsupportedContentTypeError
from file.read_image import parse_image
from fastapi.responses import Response


IMAGE_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
    "image/webp": ".webp",
}


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

    content_type = file.content_type
    if content_type not in IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type '{content_type}'.",
        )

    aruco_id = await detect_markers(image)

    return aruco_id 
