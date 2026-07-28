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
    InputTooLargeError,
    InvalidPdfError,
    SignedPdfError,
    UnsupportedContentTypeError,
)
from file.read_pdf import read_pdf
from layout.constants import QUIET_ZONE
from limits import MAX_BOXES_JSON_BYTES, MAX_BOXES_PER_REQUEST
from pdf.mark_pdf import mark_pdf, symbol_rects

_placements_adapter = TypeAdapter(list[BoxPlacement])


def _rects_overlap(first, second) -> bool:
    return not (
        first.x1 <= second.x0
        or first.x0 >= second.x1
        or first.y1 <= second.y0
        or first.y0 >= second.y1
    )


async def mark_pdf_handler(file: UploadFile, boxes: str):
    if len(boxes.encode()) > MAX_BOXES_JSON_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Boxes JSON exceeds {MAX_BOXES_JSON_BYTES} byte limit.",
        )

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
    if len(placements) > MAX_BOXES_PER_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Boxes exceed {MAX_BOXES_PER_REQUEST} placement limit.",
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
    except InputTooLargeError as error:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(error),
        ) from error
    except SignedPdfError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    try:
        symbol_regions_by_page = {}
        for placement in placements:
            if placement.page >= len(pdf):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Page {placement.page} does not exist. "
                    f"The PDF has {len(pdf)} page(s).",
                )
            page_rect = pdf[placement.page].rect
            if (
                placement.x < QUIET_ZONE
                or placement.y < QUIET_ZONE
                or placement.x + placement.width + QUIET_ZONE > page_rect.width
                or placement.y + placement.height + QUIET_ZONE > page_rect.height
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Box {placement.box_id} does not fit inside page "
                    f"{placement.page} with its quiet zone "
                    f"({page_rect.width} x {page_rect.height} pt).",
                )

            regions = symbol_regions_by_page.setdefault(placement.page, [])
            for rect in symbol_rects(placement):
                if any(_rects_overlap(rect, existing) for existing in regions):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Box {placement.box_id} symbol regions overlap on page "
                        f"{placement.page}.",
                    )
            regions.extend(symbol_rects(placement))

        marked_pdf = await mark_pdf(pdf, placements)
        content = marked_pdf.tobytes(garbage=3, deflate=True)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process PDF.",
        ) from error
    finally:
        pdf.close()

    return Response(content=content, media_type="application/pdf")
