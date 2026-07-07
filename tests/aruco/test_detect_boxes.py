import cv2
import fitz
import numpy as np
import zxingcpp

from aruco.detect_boxes import detect_boxes
from aruco.dictionary import ARUCO_DICT
from aruco.layout import DATAMATRIX_SIZE, GAP, MARKER_SIZE
from aruco.mark_pdf import mark_pdf
from aruco.utils import markers_for_slot

# Pixels per print point when composing synthetic photos.
PPP = 6


def _rasterize(page: fitz.Page, zoom: int = PPP) -> np.ndarray:
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csGRAY)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)


def _datamatrix_image(box_id: int, size_px: int) -> np.ndarray:
    barcode = zxingcpp.create_barcode(str(box_id), zxingcpp.BarcodeFormat.DataMatrix)
    img = np.array(zxingcpp.write_barcode_to_image(barcode, scale=10))
    return cv2.resize(img, (size_px, size_px), interpolation=cv2.INTER_NEAREST)


def _stamp_box(canvas: np.ndarray, slot: int, box_id: int, x: int, y: int) -> None:
    """Stamp a full box (marker pair + DataMatrix) with mark_pdf's layout ratios."""
    marker_px = MARKER_SIZE * PPP
    box_w, box_h = 250 * PPP, 120 * PPP

    top_left_id, bottom_right_id = markers_for_slot(slot)
    tl = cv2.aruco.generateImageMarker(ARUCO_DICT, top_left_id, marker_px)
    br = cv2.aruco.generateImageMarker(ARUCO_DICT, bottom_right_id, marker_px)
    canvas[y : y + marker_px, x : x + marker_px] = tl
    canvas[
        y + box_h - marker_px : y + box_h, x + box_w - marker_px : x + box_w
    ] = br

    dm = _datamatrix_image(box_id, DATAMATRIX_SIZE * PPP)
    dm_x = x + (MARKER_SIZE + GAP) * PPP
    canvas[y : y + dm.shape[0], dm_x : dm_x + dm.shape[1]] = dm


async def test_detects_single_box_from_marked_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes(pages=1), filetype="pdf")
    await mark_pdf(doc, box_id=250000)

    boxes = await detect_boxes(_rasterize(doc[0]))

    assert boxes == [{"box_id": 250000}]


async def test_detects_multiple_boxes_ordered_by_slot():
    canvas = np.full((3400, 2200), 255, dtype=np.uint8)
    _stamp_box(canvas, slot=0, box_id=11, x=100, y=100)
    _stamp_box(canvas, slot=1, box_id=22, x=100, y=900)
    _stamp_box(canvas, slot=2, box_id=333333, x=100, y=1700)
    _stamp_box(canvas, slot=3, box_id=44, x=600, y=2400)

    boxes = await detect_boxes(canvas)

    assert boxes == [
        {"box_id": 11},
        {"box_id": 22},
        {"box_id": 333333},
        {"box_id": 44},
    ]


async def test_detects_boxes_under_perspective():
    canvas = np.full((2000, 2200), 255, dtype=np.uint8)
    _stamp_box(canvas, slot=0, box_id=11, x=100, y=100)
    _stamp_box(canvas, slot=1, box_id=22, x=100, y=1000)

    h, w = canvas.shape
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[60, 40], [w - 30, 0], [w, h], [0, h - 50]])
    warped = cv2.warpPerspective(
        canvas, cv2.getPerspectiveTransform(src, dst), (w, h), borderValue=255
    )

    boxes = await detect_boxes(warped)

    assert boxes == [{"box_id": 11}, {"box_id": 22}]


async def test_reports_null_id_when_datamatrix_is_unreadable():
    canvas = np.full((1200, 2200), 255, dtype=np.uint8)
    _stamp_box(canvas, slot=0, box_id=11, x=100, y=100)
    dm_x = 100 + (MARKER_SIZE + GAP) * PPP
    dm_px = DATAMATRIX_SIZE * PPP
    canvas[100 : 100 + dm_px, dm_x : dm_x + dm_px] = 255

    boxes = await detect_boxes(canvas)

    assert boxes == [{"box_id": None}]


async def test_returns_empty_list_for_blank_image():
    canvas = np.full((800, 800), 255, dtype=np.uint8)

    assert await detect_boxes(canvas) == []
