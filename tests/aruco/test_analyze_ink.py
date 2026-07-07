import cv2
import numpy as np

from aruco.analyze_ink import is_signed
from aruco.layout import DATAMATRIX_SIZE, GAP, MARKER_SIZE
from aruco.rectify_box import PX_PER_PT


def _blank_crop(
    box_w_pt: int = 250, box_h_pt: int = 120, background: int = 255
) -> np.ndarray:
    return np.full(
        (box_h_pt * PX_PER_PT, box_w_pt * PX_PER_PT), background, dtype=np.uint8
    )


def _paint_symbols(crop: np.ndarray, bleed_px: int = 0) -> None:
    """Blacken the marker/DataMatrix regions where rectify_box places them.

    ``bleed_px`` grows each region, simulating the antialiased edges an
    imperfect rectification smears past the nominal rectangles.
    """
    h, w = crop.shape
    marker = MARKER_SIZE * PX_PER_PT
    dm_left = (MARKER_SIZE + GAP) * PX_PER_PT
    dm_right = dm_left + DATAMATRIX_SIZE * PX_PER_PT

    crop[: marker + bleed_px, : marker + bleed_px] = 0
    crop[: marker + bleed_px, dm_left - bleed_px : dm_right + bleed_px] = 0
    crop[h - marker - bleed_px :, w - marker - bleed_px :] = 0


def _draw_signature(crop: np.ndarray, color: int = 40) -> None:
    points = np.array([[200, 300], [350, 180], [500, 340], [650, 200], [800, 320]])
    cv2.polylines(crop, [points], isClosed=False, color=color, thickness=4)


def test_blank_box_is_not_signed():
    crop = _blank_crop()
    _paint_symbols(crop)

    assert is_signed(crop) is False


def test_squiggle_is_signed():
    crop = _blank_crop()
    _paint_symbols(crop)
    _draw_signature(crop)

    assert is_signed(crop) is True


def test_symbol_bleed_does_not_count_as_ink():
    crop = _blank_crop()
    _paint_symbols(crop, bleed_px=6)

    assert is_signed(crop) is False


def test_signed_on_darker_paper():
    crop = _blank_crop(background=180)
    _paint_symbols(crop)
    _draw_signature(crop, color=60)

    assert is_signed(crop) is True


def test_sparse_speckle_is_not_signed():
    crop = _blank_crop()
    _paint_symbols(crop)
    rng = np.random.default_rng(seed=7)
    for _ in range(30):
        row = rng.integers(100, crop.shape[0] - 100)
        col = rng.integers(200, crop.shape[1] - 100)
        crop[row, col] = 0

    assert is_signed(crop) is False


def test_fully_masked_tiny_crop_is_not_signed():
    crop = np.zeros((80, 80), dtype=np.uint8)

    assert is_signed(crop) is False
