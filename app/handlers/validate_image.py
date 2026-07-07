from fastapi import HTTPException, UploadFile, status

from aruco.detect_boxes import detect_boxes
from file.errors import EmptyFileError, InvalidImageError, UnsupportedContentTypeError
from file.read_image import parse_image


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

    return {"boxes": boxes}
