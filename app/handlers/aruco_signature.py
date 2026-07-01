from fastapi import UploadFile, HTTPException, status
from fastapi.responses import Response

from aruco.mark_pdf import mark_pdf
from file.errors import InvalidPdfError, EmptyFileError, UnsupportedContentTypeError
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

    marked_pdf = await mark_pdf(pdf)

    return Response(content=marked_pdf.convert_to_pdf(), media_type="application/pdf")
