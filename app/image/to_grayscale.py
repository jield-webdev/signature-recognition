import cv2
from cv2.typing import MatLike


def to_grayscale(image: MatLike) -> MatLike:
    """Convert a BGR image to single-channel grayscale.

    Images that are already single-channel are returned unchanged.
    """
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
