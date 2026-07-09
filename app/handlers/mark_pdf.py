from collections import Counter

from fastapi import UploadFile, HTTPException, status
from fastapi.responses import Response
from pydantic import TypeAdapter, ValidationError

from aruco.slots import MAX_SLOTS_PER_PAGE
from boxes.placement import BoxPlacement
from file.errors import (
    EmptyFileError,
    EmptyPdfError,
    EncryptedPdfError,
    InvalidPdfError,
    UnsupportedContentTypeError,
)
from file.read_pdf import read_pdf
from pdf.mark_pdf import mark_pdf

_placements_adapter = TypeAdapter(list[BoxPlacement])


async def mark_pdf_handler(file: UploadFile, boxes: str):
    try:
        placements = _placements_adapter.validate_json(boxes)
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid boxes: {error}",
        ) from error

    if not placements:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one box is required.",
        )

    boxes_per_page = Counter(placement.page for placement in placements)
    for page_index, count in boxes_per_page.items():
        if count > MAX_SLOTS_PER_PAGE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Page {page_index} has {count} boxes. "
                f"A page can hold at most {MAX_SLOTS_PER_PAGE}.",
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

    for placement in placements:
        if placement.page >= len(pdf):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Page {placement.page} does not exist. "
                f"The PDF has {len(pdf)} page(s).",
            )
        page_rect = pdf[placement.page].rect
        if (
            placement.x + placement.width > page_rect.width
            or placement.y + placement.height > page_rect.height
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Box {placement.box_id} does not fit inside page "
                f"{placement.page} ({page_rect.width} x {page_rect.height} pt).",
            )

    try:
        marked_pdf = await mark_pdf(pdf, placements)
        content = marked_pdf.convert_to_pdf()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process PDF.",
        ) from error

    return Response(content=content, media_type="application/pdf")
