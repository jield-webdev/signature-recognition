import cv2
import numpy as np

from aruco.dictionary import ARUCO_DICT
from aruco.slots import markers_for_slot
from image.rectify_box import PX_PER_PT, rectify_box
from layout.constants import MARKER_SIZE

# Pixels per print point when composing synthetic photos.
PPP = 6


def _square(x: float, y: float, size: float) -> np.ndarray:
    """Corner coordinates (TL, TR, BR, BL) of an axis-aligned square."""
    return np.float32([[x, y], [x + size, y], [x + size, y + size], [x, y + size]])


def _detect_ids(crop: np.ndarray) -> list[int]:
    # The markers sit flush against the crop edges, so give them back the
    # white quiet zone the detector needs.
    padded = cv2.copyMakeBorder(
        crop, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255
    )
    detector = cv2.aruco.ArucoDetector(ARUCO_DICT, cv2.aruco.DetectorParameters())
    _, ids, _ = detector.detectMarkers(padded)
    return sorted(ids.flatten().tolist()) if ids is not None else []


def _canvas_with_pair(x: int, y: int, box_w: int, box_h: int):
    """White canvas with a marker pair stamped on the box diagonal.

    Returns the canvas plus the exact corner arrays of both markers, so
    rectify_box can be exercised without running the detector.
    """
    marker_px = MARKER_SIZE * PPP
    canvas = np.full((y + box_h + 100, x + box_w + 100), 255, dtype=np.uint8)

    top_left_id, bottom_right_id = markers_for_slot(0)
    tl = cv2.aruco.generateImageMarker(ARUCO_DICT, top_left_id, marker_px)
    br = cv2.aruco.generateImageMarker(ARUCO_DICT, bottom_right_id, marker_px)
    canvas[y : y + marker_px, x : x + marker_px] = tl
    canvas[y + box_h - marker_px : y + box_h, x + box_w - marker_px : x + box_w] = br

    top_left_corners = _square(x, y, marker_px)
    bottom_right_corners = _square(
        x + box_w - marker_px, y + box_h - marker_px, marker_px
    )
    return canvas, top_left_corners, bottom_right_corners


def test_crop_has_box_size_in_print_points():
    box_w_pt, box_h_pt = 250, 120
    canvas, tl, br = _canvas_with_pair(100, 100, box_w_pt * PPP, box_h_pt * PPP)

    crop = rectify_box(canvas, tl, br)

    assert crop is not None
    assert crop.shape == (box_h_pt * PX_PER_PT, box_w_pt * PX_PER_PT)


def test_crop_contains_both_markers_upright():
    canvas, tl, br = _canvas_with_pair(100, 100, 250 * PPP, 120 * PPP)

    crop = rectify_box(canvas, tl, br)

    assert _detect_ids(crop) == [0, 1]


def test_removes_perspective():
    canvas, tl, br = _canvas_with_pair(100, 100, 250 * PPP, 120 * PPP)
    h, w = canvas.shape
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[80, 50], [w - 40, 0], [w, h], [0, h - 60]])
    perspective = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(canvas, perspective, (w, h), borderValue=255)
    warped_tl = cv2.perspectiveTransform(tl.reshape(-1, 1, 2), perspective).reshape(4, 2)
    warped_br = cv2.perspectiveTransform(br.reshape(-1, 1, 2), perspective).reshape(4, 2)

    crop = rectify_box(warped, warped_tl, warped_br)

    assert crop is not None
    expected_h, expected_w = 120 * PX_PER_PT, 250 * PX_PER_PT
    assert abs(crop.shape[0] - expected_h) <= expected_h * 0.02
    assert abs(crop.shape[1] - expected_w) <= expected_w * 0.02

    assert _detect_ids(crop) == [0, 1]


def test_rejects_markers_not_on_a_diagonal():
    canvas, tl, br = _canvas_with_pair(100, 100, 250 * PPP, 120 * PPP)
    to_the_left = _square(0, 100, MARKER_SIZE * PPP)

    assert rectify_box(canvas, tl, to_the_left) is None
