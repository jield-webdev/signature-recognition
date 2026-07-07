import cv2
import numpy as np
from cv2.typing import MatLike

from aruco.dictionary import ARUCO_DICT


async def detect_markers(image: MatLike) -> list[tuple[int, np.ndarray]]:
    """Detect ArUco markers, returning (id, corners) pairs.

    Corners are a 4x2 float array in TL, TR, BR, BL order, as reported by
    OpenCV. Returns an empty list when no marker is found.
    """
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(ARUCO_DICT, parameters)

    corners, ids, rejected = detector.detectMarkers(image)

    if ids is None:
        return []
    return [
        (int(marker_id), marker_corners.reshape(4, 2))
        for marker_id, marker_corners in zip(ids.flatten(), corners)
    ]
