from collections import defaultdict

import fitz

from aruco.dictionary import ARUCO_DICT
from aruco.slots import markers_for_slot
from boxes.placement import BoxPlacement
from datamatrix.encode_datamatrix import encode_datamatrix
from layout.constants import DATAMATRIX_SIZE, GAP, MARKER_SIZE, QUIET_ZONE
from opencv_config import cv2


def symbol_rects(box: BoxPlacement) -> tuple[fitz.Rect, fitz.Rect, fitz.Rect]:
    datamatrix_x = box.x + MARKER_SIZE + GAP
    return (
        fitz.Rect(box.x, box.y, box.x + MARKER_SIZE, box.y + MARKER_SIZE),
        fitz.Rect(
            box.x + box.width - MARKER_SIZE,
            box.y + box.height - MARKER_SIZE,
            box.x + box.width,
            box.y + box.height,
        ),
        fitz.Rect(
            datamatrix_x,
            box.y,
            datamatrix_x + DATAMATRIX_SIZE,
            box.y + DATAMATRIX_SIZE,
        ),
    )


def _box_symbols(slot: int, box: BoxPlacement):
    top_left_id, bottom_right_id = markers_for_slot(slot)
    top_left, bottom_right, datamatrix = symbol_rects(box)
    return (
        (
            cv2.aruco.generateImageMarker(ARUCO_DICT, top_left_id, 600),
            top_left,
        ),
        (
            cv2.aruco.generateImageMarker(ARUCO_DICT, bottom_right_id, 600),
            bottom_right,
        ),
        (
            encode_datamatrix(str(box.box_id)),
            datamatrix,
        ),
    )


def _stamp_page(page: fitz.Page, page_boxes: list[BoxPlacement]) -> None:
    symbols = [
        (image, rect * page.derotation_matrix)
        for slot, box in enumerate(page_boxes)
        for image, rect in _box_symbols(slot, box)
    ]

    for _, rect in symbols:
        page.draw_rect(
            rect + (-QUIET_ZONE, -QUIET_ZONE, QUIET_ZONE, QUIET_ZONE),
            color=None,
            fill=(1, 1, 1),
        )

    for image, rect in symbols:
        ok, buf = cv2.imencode(".png", image)
        if not ok:
            raise RuntimeError("Failed to encode marker image.")
        page.insert_image(rect, stream=buf.tobytes())


async def mark_pdf(file: fitz.Document, boxes: list[BoxPlacement]) -> fitz.Document:
    # Slots (and thus marker ids) restart on every page: detection works on a
    # photo of a single page, so ids only need to be unique within one.
    boxes_by_page: dict[int, list[BoxPlacement]] = defaultdict(list)
    for box in boxes:
        boxes_by_page[box.page].append(box)

    for page_index, page_boxes in boxes_by_page.items():
        _stamp_page(file[page_index], page_boxes)

    return file
