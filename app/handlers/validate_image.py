import cv2

from fastapi import HTTPException, UploadFile, status

from file.read_image import (
    EmptyFileError,
    InvalidImageError,
    UnsupportedContentTypeError,
    read_image,
)


async def validate_image_handler(file: UploadFile):
    try:
        image = await read_image(file)
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

    img_type = file.content_type.split("/", maxsplit=1)[1]
    output_path = f"./tmp.{img_type}"
    grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if not cv2.imwrite(output_path, grayscale_image):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write grayscale image to {output_path}.",
        )

    return {"mime_type": file.content_type, "path": output_path}
