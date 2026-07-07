from fastapi import UploadFile, HTTPException, status
from fastapi.responses import Response

from aruco.mark_pdf import mark_pdf
from aruco.utils import MAX_BOX_ID, is_valid_box_id
from file.errors import (
    EmptyFileError,
    EmptyPdfError,
    EncryptedPdfError,
    InvalidPdfError,
    UnsupportedContentTypeError,
)
from file.read_pdf import read_pdf


async def mark_pdf_handler(file: UploadFile, box_id: int):
    if not is_valid_box_id(box_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Box id {box_id} is not valid. Must be between 1 and {MAX_BOX_ID}.",
        )

    try:
        pdf = await read_pdf(file)
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
    except InvalidPdfError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except EncryptedPdfError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except EmptyPdfError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    try:
        marked_pdf = await mark_pdf(pdf, box_id)
        content = marked_pdf.convert_to_pdf()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process PDF.",
        ) from error

    return Response(content=content, media_type="application/pdf")
