from collections import defaultdict

import cv2
import fitz

from aruco.dictionary import ARUCO_DICT
from aruco.slots import markers_for_slot
from boxes.placement import BoxPlacement
from datamatrix.encode_datamatrix import encode_datamatrix
from layout.constants import DATAMATRIX_SIZE, GAP, MARKER_SIZE, QUIET_ZONE


def _stamp_box(page: fitz.Page, slot: int, box: BoxPlacement) -> None:
    top_left_id, bottom_right_id = markers_for_slot(slot)
    datamatrix_x = box.x + MARKER_SIZE + GAP
    symbols = [
        (
            cv2.aruco.generateImageMarker(ARUCO_DICT, top_left_id, 600),
            fitz.Rect(box.x, box.y, box.x + MARKER_SIZE, box.y + MARKER_SIZE),
        ),
        (
            cv2.aruco.generateImageMarker(ARUCO_DICT, bottom_right_id, 600),
            fitz.Rect(
                box.x + box.width - MARKER_SIZE,
                box.y + box.height - MARKER_SIZE,
                box.x + box.width,
                box.y + box.height,
            ),
        ),
        (
            encode_datamatrix(str(box.box_id)),
            fitz.Rect(
                datamatrix_x,
                box.y,
                datamatrix_x + DATAMATRIX_SIZE,
                box.y + DATAMATRIX_SIZE,
            ),
        ),
    ]

    # Every patch goes down before any symbol: neighbouring quiet zones
    # overlap, and a patch drawn later would paint over its neighbour.
    for _, rect in symbols:
        page.draw_rect(
            rect + (-QUIET_ZONE, -QUIET_ZONE, QUIET_ZONE, QUIET_ZONE),
            color=None,
            fill=(1, 1, 1),
        )

    for image, rect in symbols:
        ok, buf = cv2.imencode(".png", image)
        page.insert_image(rect, stream=buf.tobytes())


async def mark_pdf(file: fitz.Document, boxes: list[BoxPlacement]) -> fitz.Document:
    # Slots (and thus marker ids) restart on every page: detection works on a
    # photo of a single page, so ids only need to be unique within one.
    boxes_by_page: dict[int, list[BoxPlacement]] = defaultdict(list)
    for box in boxes:
        boxes_by_page[box.page].append(box)

    for page_index, page_boxes in boxes_by_page.items():
        page = file[page_index]
        for slot, box in enumerate(page_boxes):
            _stamp_box(page, slot, box)

    return file
