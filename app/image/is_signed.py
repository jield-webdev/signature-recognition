import numpy as np
from cv2.typing import MatLike

from layout.constants import DATAMATRIX_SIZE, GAP, MARKER_SIZE
from image.rectify_box import PX_PER_PT

# Rectification is not pixel-perfect: antialiased symbol edges smear a few
# pixels past their nominal rectangles. 8 px of padding absorbs that and also
# closes the 16 px gap between the top-left marker and the DataMatrix.
MASK_PADDING_PX = 8

# Boxes are often drawn on the form as an outlined rectangle (or a table
# cell), so the printed border runs right along the crop edge and reads as
# ink. Ignoring a 6 pt band around the crop drops it, along with the few
# pixels of it that rectification slop drags further inside. Signatures don't
# reach that far: on the sample photos the inset leaves unsigned boxes below
# 0.0002 ink and signed ones above 0.0028.
BORDER_INSET_PX = 6 * PX_PER_PT

# A pixel counts as ink when darker than the paper background by this much.
INK_DELTA = 60

# Fraction of analyzable interior pixels that must be ink to call a box signed.
# Tuned so a 1 pt pen stroke still clears it on a page-spanning box (~0.002),
# while speckle noise stays an order of magnitude below.
INK_RATIO_THRESHOLD = 0.001


def is_signed(crop: MatLike) -> bool:
    """Decide whether a rectified box crop contains ink (a signature).

    The markers and DataMatrix sit at fixed positions in the rectified crop,
    so their (padded) rectangles are masked out from the layout constants, as
    is a band around the crop edge where the box's own printed outline runs.
    The paper brightness is the median of the remaining interior — robust
    because even a heavy signature covers a few percent of it — and the box
    is signed when enough interior pixels are darker than that background.
    """
    h, w = crop.shape[:2]
    marker = MARKER_SIZE * PX_PER_PT
    dm_left = (MARKER_SIZE + GAP) * PX_PER_PT
    dm_right = dm_left + DATAMATRIX_SIZE * PX_PER_PT
    pad = MASK_PADDING_PX
    inset = BORDER_INSET_PX

    mask = np.ones((h, w), dtype=bool)
    mask[: marker + pad, : marker + pad] = False
    mask[: marker + pad, dm_left - pad : dm_right + pad] = False
    mask[max(h - marker - pad, 0) :, max(w - marker - pad, 0) :] = False
    mask[:inset, :] = False
    mask[max(h - inset, 0) :, :] = False
    mask[:, :inset] = False
    mask[:, max(w - inset, 0) :] = False

    interior = crop[mask]
    if interior.size == 0:
        return False

    background = float(np.median(interior))
    ink_pixels = np.count_nonzero(interior < background - INK_DELTA)
    return bool(ink_pixels / interior.size >= INK_RATIO_THRESHOLD)
