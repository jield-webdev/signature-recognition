import cv2
import numpy as np

from image.remove_shadows import remove_shadows

PAPER = 230
SHADOW = 60


def _paper_bgr(w: int = 400, h: int = 300) -> np.ndarray:
    return np.full((h, w, 3), PAPER, dtype=np.uint8)


def _cast_shadow(image: np.ndarray) -> np.ndarray:
    """Darken the left half with a soft penumbra, like a real cast shadow."""
    shaded = image.copy()
    shaded[:, : image.shape[1] // 2] = SHADOW
    return cv2.GaussianBlur(shaded, (51, 51), 0)


def test_output_keeps_shape_and_dtype():
    image = _cast_shadow(_paper_bgr())

    result = remove_shadows(image)

    assert result.shape == image.shape
    assert result.dtype == np.uint8


def test_grayscale_input_keeps_shape_and_dtype():
    image = _cast_shadow(np.full((300, 400), PAPER, dtype=np.uint8))

    result = remove_shadows(image)

    assert result.shape == image.shape
    assert result.dtype == np.uint8


def test_shadowed_region_is_lifted():
    image = _cast_shadow(_paper_bgr())

    result = remove_shadows(image)

    interior = (slice(None), slice(20, 140))  # well inside the shadow half
    before = float(image[interior].mean())
    after = float(result[interior].mean())
    assert after > before + 20


def test_shadow_free_image_stays_unchanged():
    image = _paper_bgr()

    result = remove_shadows(image)

    diff = np.abs(result.astype(np.int16) - image.astype(np.int16))
    assert diff.max() <= 3
