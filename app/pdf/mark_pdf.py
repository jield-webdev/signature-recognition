from collections import defaultdict

import cv2
import fitz

from aruco.dictionary import ARUCO_DICT
from aruco.slots import markers_for_slot
from boxes.placement import BoxPlacement
from datamatrix.encode_datamatrix import encode_datamatrix
from layout.constants import DATAMATRIX_SIZE, GAP, MARKER_SIZE


def _stamp_box(page: fitz.Page, slot: int, box: BoxPlacement) -> None:
    top_left_id, bottom_right_id = markers_for_slot(slot)
    positions = {
        top_left_id: (box.x, box.y),
        bottom_right_id: (
            box.x + box.width - MARKER_SIZE,
            box.y + box.height - MARKER_SIZE,
        ),
    }

    for marker_id, (x, y) in positions.items():
        img = cv2.aruco.generateImageMarker(ARUCO_DICT, marker_id, 600)
        ok, buf = cv2.imencode(".png", img)
        rect = fitz.Rect(x, y, x + MARKER_SIZE, y + MARKER_SIZE)
        page.insert_image(rect, stream=buf.tobytes())

    dm_img = encode_datamatrix(str(box.box_id))
    ok, buf = cv2.imencode(".png", dm_img)
    x = box.x + MARKER_SIZE + GAP
    rect = fitz.Rect(x, box.y, x + DATAMATRIX_SIZE, box.y + DATAMATRIX_SIZE)
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
