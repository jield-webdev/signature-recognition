import cv2
import numpy as np
import zxingcpp
from cv2.typing import MatLike

from aruco.detect_markers import detect_markers
from aruco.layout import DATAMATRIX_SIZE, GAP, MARKER_SIZE
from aruco.rectify_box import rectify_box
from aruco.utils import is_valid_box_id

# Side of the canonical (rectified) marker square, in pixels. The stamped
# DataMatrix is 10 modules plus quiet zone at the same print size, so this
# leaves ~10 px per module after rectification.
CANONICAL_MARKER_PX = 120

# A few extra rectified pixels around the DataMatrix crop act as quiet zone.
CROP_PADDING_PX = 8


def _decode_datamatrix(image: MatLike, marker_corners: np.ndarray) -> int | None:
    """Rectify the neighborhood of a top-left marker and decode its DataMatrix.

    The marker's 4 detected corners define the local perspective of the page
    plane; the DataMatrix sits at a known offset in print units, so its
    position in the rectified view follows from the print-size ratios.
    """
    scale = CANONICAL_MARKER_PX / MARKER_SIZE
    dm_left = (MARKER_SIZE + GAP) * scale
    dm_right = (MARKER_SIZE + GAP + DATAMATRIX_SIZE) * scale

    canonical = np.array(
        [
            [0, 0],
            [CANONICAL_MARKER_PX, 0],
            [CANONICAL_MARKER_PX, CANONICAL_MARKER_PX],
            [0, CANONICAL_MARKER_PX],
        ],
        dtype=np.float32,
    )
    # Shift the target frame so the warp canvas has room for the padding on
    # every side of the DataMatrix without negative coordinates.
    offset = np.array([CROP_PADDING_PX - dm_left, CROP_PADDING_PX], dtype=np.float32)
    homography = cv2.getPerspectiveTransform(
        marker_corners.astype(np.float32), canonical + offset
    )

    width = int(dm_right - dm_left) + 2 * CROP_PADDING_PX
    height = CANONICAL_MARKER_PX + 2 * CROP_PADDING_PX
    crop = cv2.warpPerspective(
        image, homography, (width, height), borderValue=255
    )

    result = zxingcpp.read_barcode(crop, formats=zxingcpp.BarcodeFormat.DataMatrix)
    if result is None or not result.text.isdigit():
        return None
    box_id = int(result.text)
    return box_id if is_valid_box_id(box_id) else None


async def detect_boxes(image: MatLike) -> list[dict]:
    """Find every signature box in a photo, crop it, and decode its id.

    Each box is delimited by its own marker pair (even id = top-left, odd id
    = bottom-right) and rectified independently, so boxes never distort each
    other. A box is ignored entirely unless both of its markers are detected.
    A box whose DataMatrix cannot be decoded is reported with ``box_id: None``
    so the caller can request a retake instead of silently dropping it.
    """
    corners_by_id = dict(await detect_markers(image))

    boxes = []
    for top_left_id in sorted(marker_id for marker_id in corners_by_id if marker_id % 2 == 0):
        top_left = corners_by_id[top_left_id]
        bottom_right = corners_by_id.get(top_left_id + 1)
        if bottom_right is None:
            continue  # incomplete pair -> ignore the whole box

        crop = rectify_box(image, top_left, bottom_right)
        if crop is None:
            continue  # both markers found but not in a valid diagonal arrangement

        boxes.append(
            {
                "box_id": _decode_datamatrix(image, top_left),
                "image": crop,
            }
        )
    return boxes
