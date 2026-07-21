import cv2
import numpy as np
from cv2.typing import MatLike

from layout.constants import MARKER_SIZE

# Resolution of the rectified crop: 4 px per print point (a 250 pt wide box
# comes out 1000 px wide).
PX_PER_PT = 4

# Levenberg-Marquardt schedule for the joint homography + box-size fit.
LM_MAX_ITERATIONS = 80
LM_INITIAL_DAMPING = 1e-3
LM_COST_EPSILON = 1e-16


def _marker_destination(x: float, y: float, size: float) -> np.ndarray:
    """Corner coordinates (TL, TR, BR, BL) of a square marker placed at (x, y)."""
    return np.array(
        [[x, y], [x + size, y], [x + size, y + size], [x, y + size]],
        dtype=np.float32,
    )


def _plane_corners(box_w: float, box_h: float, marker_px: float) -> np.ndarray:
    """The 8 marker corners in the rectified frame for a box of the given size."""
    return np.vstack(
        [
            _marker_destination(0, 0, marker_px),
            _marker_destination(box_w - marker_px, box_h - marker_px, marker_px),
        ]
    ).astype(np.float64)


def _project(homography: np.ndarray, points: np.ndarray) -> np.ndarray:
    homogeneous = np.hstack([points, np.ones((len(points), 1))]) @ homography.T
    return homogeneous[:, :2] / homogeneous[:, 2:3]


def _estimate_box_size(
    top_left_corners: np.ndarray,
    bottom_right_corners: np.ndarray,
    marker_px: float,
) -> tuple[float, float] | None:
    """Box size in rectified pixels, fitted jointly with the page homography.

    Both markers are known equal squares on the page plane, so the 8 detected
    corners give 16 equations for 10 unknowns: the plane-to-image homography
    (8 params) plus the box width and height. Estimating everything jointly
    lets the bottom-right marker's rectified shape constrain the perspective
    terms across the whole box, instead of extrapolating them from the
    sub-pixel distortion of the top-left marker alone — which amplifies
    corner noise quadratically with the marker distance and produced badly
    sheared crops on tilted photos.

    Solved with Levenberg-Marquardt on the image-space reprojection error
    (numeric Jacobian; the problem is only 16x10). Returns ``None`` when the
    markers aren't in the expected diagonal arrangement.
    """
    image_corners = np.vstack([top_left_corners, bottom_right_corners]).astype(
        np.float64
    )

    # Initial guess: rectify from the top-left marker alone and read the box
    # size off where the bottom-right marker's BR corner lands.
    plane_from_image = cv2.getPerspectiveTransform(
        top_left_corners.astype(np.float32), _marker_destination(0, 0, marker_px)
    )
    projected = cv2.perspectiveTransform(
        bottom_right_corners.astype(np.float32).reshape(-1, 1, 2), plane_from_image
    ).reshape(4, 2)
    box_w, box_h = projected[2]  # the BR marker's BR corner = the box's BR corner
    if box_w <= marker_px or box_h <= marker_px:
        return None

    homography, _ = cv2.findHomography(
        _plane_corners(box_w, box_h, marker_px), image_corners
    )
    if homography is None:
        return None
    theta = np.concatenate([homography.flatten()[:8], [box_w, box_h]])

    def residual(params: np.ndarray) -> np.ndarray:
        h_matrix = np.append(params[:8], 1).reshape(3, 3)
        plane = _plane_corners(params[8], params[9], marker_px)
        return (_project(h_matrix, plane) - image_corners).ravel()

    damping = LM_INITIAL_DAMPING
    residuals = residual(theta)
    cost = residuals @ residuals
    for _ in range(LM_MAX_ITERATIONS):
        jacobian = np.empty((16, 10))
        for j in range(10):
            delta = np.zeros(10)
            delta[j] = 1e-6 * max(1, abs(theta[j]))
            jacobian[:, j] = (residual(theta + delta) - residuals) / delta[j]

        normal = jacobian.T @ jacobian
        improved = False
        for _ in range(10):
            try:
                step = np.linalg.solve(
                    normal + damping * np.diag(np.diag(normal) + 1e-12),
                    -jacobian.T @ residuals,
                )
            except np.linalg.LinAlgError:
                damping *= 10
                continue
            candidate = theta + step
            candidate_residuals = residual(candidate)
            candidate_cost = candidate_residuals @ candidate_residuals
            if candidate_cost < cost:
                theta, residuals, cost = candidate, candidate_residuals, candidate_cost
                damping = max(damping / 3, 1e-9)
                improved = True
                break
            damping *= 10
        if not improved or cost < LM_COST_EPSILON:
            break

    box_w, box_h = theta[8], theta[9]
    if box_w <= marker_px or box_h <= marker_px:
        return None
    return float(box_w), float(box_h)


def rectify_box(
    image: MatLike,
    top_left_corners: np.ndarray,
    bottom_right_corners: np.ndarray,
) -> np.ndarray | None:
    """Crop the box delimited by its diagonal marker pair, perspective removed.

    The box's size isn't known in advance: it is fitted jointly with the page
    homography from both markers' corners (see ``_estimate_box_size``), and
    the final warp uses all 8 corners, which are consistent with the fitted
    size by construction. Returns ``None`` when the markers aren't in the
    expected diagonal arrangement.
    """
    marker_px = MARKER_SIZE * PX_PER_PT

    box_size = _estimate_box_size(top_left_corners, bottom_right_corners, marker_px)
    if box_size is None:
        return None
    box_w, box_h = box_size

    src = np.vstack([top_left_corners, bottom_right_corners]).astype(np.float32)
    dst = _plane_corners(box_w, box_h, marker_px).astype(np.float32)
    homography, _ = cv2.findHomography(src, dst)
    return cv2.warpPerspective(
        image, homography, (round(box_w), round(box_h)), borderValue=255
    )
