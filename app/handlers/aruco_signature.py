from fastapi import UploadFile, HTTPException, status
from fastapi.responses import Response

from aruco.mark_pdf import mark_pdf
from file.errors import (
    EmptyFileError,
    EmptyPdfError,
    EncryptedPdfError,
    InvalidPdfError,
    UnsupportedContentTypeError,
)
from file.read_pdf import read_pdf


async def aruco_signature_handler(file: UploadFile):
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
        marked_pdf = await mark_pdf(pdf)
        content = marked_pdf.convert_to_pdf()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process PDF.",
        ) from error

    return Response(content=content, media_type="application/pdf")
