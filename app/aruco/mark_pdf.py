import cv2
import fitz
import numpy as np
import zxingcpp

from aruco.dictionary import ARUCO_DICT
from aruco.layout import DATAMATRIX_SIZE, GAP, MARGIN, MARKER_SIZE
from aruco.utils import markers_for_slot

SLOT = 0  # single box per page for now


async def mark_pdf(file: fitz.Document, box_id: int) -> fitz.Document:
    page = file[0]
    W, H = page.rect.width, page.rect.height

    top_left_id, bottom_right_id = markers_for_slot(SLOT)
    positions = {
        top_left_id: (MARGIN, MARGIN),
        bottom_right_id: (W - MARGIN - MARKER_SIZE, H - MARGIN - MARKER_SIZE),
    }

    for marker_id, (x, y) in positions.items():
        img = cv2.aruco.generateImageMarker(ARUCO_DICT, marker_id, 600)
        ok, buf = cv2.imencode(".png", img)
        rect = fitz.Rect(x, y, x + MARKER_SIZE, y + MARKER_SIZE)
        page.insert_image(rect, stream=buf.tobytes())

    barcode = zxingcpp.create_barcode(str(box_id), zxingcpp.BarcodeFormat.DataMatrix)
    dm_img = np.array(zxingcpp.write_barcode_to_image(barcode, scale=40))
    ok, buf = cv2.imencode(".png", dm_img)
    x = MARGIN + MARKER_SIZE + GAP
    rect = fitz.Rect(x, MARGIN, x + DATAMATRIX_SIZE, MARGIN + DATAMATRIX_SIZE)
    page.insert_image(rect, stream=buf.tobytes())

    return file
