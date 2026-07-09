import cv2
import fitz
import numpy as np
import zxingcpp

from aruco.dictionary import ARUCO_DICT
from aruco.slots import markers_for_slot
from boxes.detect_boxes import detect_boxes
from boxes.placement import BoxPlacement
from image.rectify_box import PX_PER_PT
from layout.constants import DATAMATRIX_SIZE, GAP, MARGIN, MARKER_SIZE
from pdf.mark_pdf import mark_pdf

# Pixels per print point when composing synthetic photos.
PPP = 6


def _rasterize(page: fitz.Page, zoom: int = PPP) -> np.ndarray:
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csGRAY)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)


def _datamatrix_image(box_id: int, size_px: int) -> np.ndarray:
    barcode = zxingcpp.create_barcode(str(box_id), zxingcpp.BarcodeFormat.DataMatrix)
    img = np.array(zxingcpp.write_barcode_to_image(barcode, scale=10))
    return cv2.resize(img, (size_px, size_px), interpolation=cv2.INTER_NEAREST)


def _stamp_box(
    canvas: np.ndarray,
    slot: int,
    box_id: int,
    x: int,
    y: int,
    box_w_pt: int = 250,
    box_h_pt: int = 120,
    include_bottom_right: bool = True,
    signed: bool = False,
) -> None:
    """Stamp a full box (marker pair + DataMatrix) with mark_pdf's layout ratios."""
    marker_px = MARKER_SIZE * PPP
    box_w, box_h = box_w_pt * PPP, box_h_pt * PPP

    top_left_id, bottom_right_id = markers_for_slot(slot)
    tl = cv2.aruco.generateImageMarker(ARUCO_DICT, top_left_id, marker_px)
    canvas[y : y + marker_px, x : x + marker_px] = tl
    if include_bottom_right:
        br = cv2.aruco.generateImageMarker(ARUCO_DICT, bottom_right_id, marker_px)
        canvas[
            y + box_h - marker_px : y + box_h, x + box_w - marker_px : x + box_w
        ] = br

    dm = _datamatrix_image(box_id, DATAMATRIX_SIZE * PPP)
    dm_x = x + (MARKER_SIZE + GAP) * PPP
    canvas[y : y + dm.shape[0], dm_x : dm_x + dm.shape[1]] = dm

    if signed:
        squiggle = np.array(
            [
                [x + int(box_w * 0.2), y + int(box_h * 0.8)],
                [x + int(box_w * 0.35), y + int(box_h * 0.55)],
                [x + int(box_w * 0.5), y + int(box_h * 0.85)],
                [x + int(box_w * 0.65), y + int(box_h * 0.55)],
                [x + int(box_w * 0.8), y + int(box_h * 0.8)],
            ]
        )
        cv2.polylines(canvas, [squiggle], isClosed=False, color=0, thickness=6)


def _cast_shadow(canvas: np.ndarray, value: int = 140) -> np.ndarray:
    """Overlay a soft horizontal shadow band crossing the first box's interior."""
    shade = np.full_like(canvas, 255)
    shade[400:700, :] = value
    shade = cv2.GaussianBlur(shade, (151, 151), 0)
    return cv2.min(canvas, shade)


def _assert_crop_size(crop: np.ndarray, box_w_pt: float, box_h_pt: float) -> None:
    """The rectified crop should measure box size in print points times PX_PER_PT."""
    expected_w, expected_h = box_w_pt * PX_PER_PT, box_h_pt * PX_PER_PT
    h, w = crop.shape[:2]
    assert abs(w - expected_w) <= expected_w * 0.02
    assert abs(h - expected_h) <= expected_h * 0.02


async def test_detects_single_box_from_marked_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes(pages=1), filetype="pdf")
    page_w, page_h = doc[0].rect.width, doc[0].rect.height
    placement = BoxPlacement(
        box_id=250000,
        page=0,
        x=MARGIN,
        y=MARGIN,
        width=page_w - 2 * MARGIN,
        height=page_h - 2 * MARGIN,
    )
    await mark_pdf(doc, [placement])

    boxes = await detect_boxes(_rasterize(doc[0]))

    assert len(boxes) == 1
    assert boxes[0]["box_id"] == 250000
    assert boxes[0]["is_signed"] is False
    _assert_crop_size(boxes[0]["image"], page_w - 2 * MARGIN, page_h - 2 * MARGIN)


async def test_reports_signed_and_unsigned_boxes():
    canvas = np.full((2000, 2200), 255, dtype=np.uint8)
    _stamp_box(canvas, slot=0, box_id=11, x=100, y=100, signed=True)
    _stamp_box(canvas, slot=1, box_id=22, x=100, y=1000)

    boxes = await detect_boxes(canvas)

    assert [box["box_id"] for box in boxes] == [11, 22]
    assert boxes[0]["is_signed"] is True
    assert boxes[1]["is_signed"] is False


async def test_shadowed_unsigned_box_is_not_signed():
    canvas = np.full((2000, 2200), 255, dtype=np.uint8)
    _stamp_box(canvas, slot=0, box_id=11, x=100, y=100)

    boxes = await detect_boxes(_cast_shadow(canvas))

    assert [box["box_id"] for box in boxes] == [11]
    assert boxes[0]["is_signed"] is False


async def test_shadowed_signed_box_stays_signed():
    canvas = np.full((2000, 2200), 255, dtype=np.uint8)
    _stamp_box(canvas, slot=0, box_id=11, x=100, y=100, signed=True)

    boxes = await detect_boxes(_cast_shadow(canvas))

    assert [box["box_id"] for box in boxes] == [11]
    assert boxes[0]["is_signed"] is True


async def test_detects_multiple_boxes_each_cropped_independently():
    canvas = np.full((3400, 2600), 255, dtype=np.uint8)
    _stamp_box(canvas, slot=0, box_id=11, x=100, y=100, box_w_pt=250, box_h_pt=120)
    _stamp_box(canvas, slot=1, box_id=22, x=100, y=900, box_w_pt=180, box_h_pt=90)
    _stamp_box(canvas, slot=2, box_id=333333, x=100, y=1700, box_w_pt=320, box_h_pt=60)
    _stamp_box(canvas, slot=3, box_id=44, x=600, y=2400, box_w_pt=250, box_h_pt=150)

    boxes = await detect_boxes(canvas)

    assert [box["box_id"] for box in boxes] == [11, 22, 333333, 44]
    _assert_crop_size(boxes[0]["image"], 250, 120)
    _assert_crop_size(boxes[1]["image"], 180, 90)
    _assert_crop_size(boxes[2]["image"], 320, 60)
    _assert_crop_size(boxes[3]["image"], 250, 150)


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

    assert [box["box_id"] for box in boxes] == [11, 22]
    for box in boxes:
        _assert_crop_size(box["image"], 250, 120)


async def test_reports_null_id_when_datamatrix_is_unreadable():
    canvas = np.full((1200, 2200), 255, dtype=np.uint8)
    _stamp_box(canvas, slot=0, box_id=11, x=100, y=100)
    dm_x = 100 + (MARKER_SIZE + GAP) * PPP
    dm_px = DATAMATRIX_SIZE * PPP
    canvas[100 : 100 + dm_px, dm_x : dm_x + dm_px] = 255

    boxes = await detect_boxes(canvas)

    assert len(boxes) == 1
    assert boxes[0]["box_id"] is None
    _assert_crop_size(boxes[0]["image"], 250, 120)


async def test_ignores_box_with_missing_bottom_right_marker():
    canvas = np.full((1800, 2200), 255, dtype=np.uint8)
    _stamp_box(canvas, slot=0, box_id=11, x=100, y=100, include_bottom_right=False)
    _stamp_box(canvas, slot=1, box_id=22, x=100, y=900)

    boxes = await detect_boxes(canvas)

    assert [box["box_id"] for box in boxes] == [22]


async def test_returns_empty_list_for_blank_image():
    canvas = np.full((800, 800), 255, dtype=np.uint8)

    assert await detect_boxes(canvas) == []
