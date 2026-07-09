import cv2
import numpy as np
from cv2.typing import MatLike

from layout.constants import MARKER_SIZE

# Resolution of the rectified crop: 4 px per print point (a 250 pt wide box
# comes out 1000 px wide).
PX_PER_PT = 4


def _marker_destination(x: float, y: float, size: float) -> np.ndarray:
    """Corner coordinates (TL, TR, BR, BL) of a square marker placed at (x, y)."""
    return np.array(
        [[x, y], [x + size, y], [x + size, y + size], [x, y + size]],
        dtype=np.float32,
    )


def rectify_box(
    image: MatLike,
    top_left_corners: np.ndarray,
    bottom_right_corners: np.ndarray,
) -> np.ndarray | None:
    """Crop the box delimited by its diagonal marker pair, perspective removed.

    The box's size isn't known in advance: the plane is rectified from the
    top-left marker alone, and measuring where the bottom-right marker lands
    in that frame yields the box dimensions. The final warp then uses all
    8 corners for accuracy. Returns ``None`` when the markers aren't in the
    expected diagonal arrangement.
    """
    marker_px = MARKER_SIZE * PX_PER_PT

    plane = cv2.getPerspectiveTransform(
        top_left_corners.astype(np.float32), _marker_destination(0, 0, marker_px)
    )
    projected = cv2.perspectiveTransform(
        bottom_right_corners.astype(np.float32).reshape(-1, 1, 2), plane
    ).reshape(4, 2)
    box_w, box_h = projected[2]  # the BR marker's BR corner = the box's BR corner
    if box_w <= marker_px or box_h <= marker_px:
        return None

    src = np.vstack([top_left_corners, bottom_right_corners]).astype(np.float32)
    dst = np.vstack(
        [
            _marker_destination(0, 0, marker_px),
            _marker_destination(box_w - marker_px, box_h - marker_px, marker_px),
        ]
    )
    homography, _ = cv2.findHomography(src, dst)
    return cv2.warpPerspective(
        image, homography, (round(box_w), round(box_h)), borderValue=255
    )
