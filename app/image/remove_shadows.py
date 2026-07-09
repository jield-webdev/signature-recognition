import cv2
import numpy as np
from cv2.typing import MatLike

# Blend weight between the original lightness and its retinex estimate inside
# shadowed areas (0 = keep the shadow, 1 = replace it entirely).
STRENGTH = 0.83

# Scales the lightness threshold below which a low-saturation pixel counts as
# shadow (threshold = 0.5 * SENSITIVITY on normalized lightness).
SENSITIVITY = 1.42

# Odd Gaussian kernel side (px) that feathers the shadow mask so the
# correction fades in instead of leaving a hard seam.
MASK_BLUR_PX = 31

# Gaussian scales (px) of the multiscale retinex illumination estimate.
_RETINEX_SCALES = (31, 101, 301)


def _multiscale_retinex(lightness: np.ndarray) -> np.ndarray:
    """Estimate reflectance by removing illumination at several scales."""
    retinex = np.zeros_like(lightness, dtype=np.float32)
    for scale in _RETINEX_SCALES:
        blur = cv2.GaussianBlur(lightness, (scale, scale), 0)
        retinex += np.log(lightness + 1) - np.log(blur + 1)
    retinex /= len(_RETINEX_SCALES)
    return cv2.normalize(retinex, retinex, 0, 255, cv2.NORM_MINMAX)


def _shadow_mask(
    lightness: np.ndarray, saturation: np.ndarray, sensitivity: float, blur_px: int
) -> np.ndarray:
    """Soft 0..1 mask of pixels that are both dark and desaturated."""
    shadow = ((lightness < 0.5 * sensitivity) & (saturation < 0.5)).astype(np.float32)
    return cv2.GaussianBlur(shadow, (blur_px, blur_px), 0)


def remove_shadows(
    image: MatLike,
    strength: float = STRENGTH,
    sensitivity: float = SENSITIVITY,
    mask_blur: int = MASK_BLUR_PX,
) -> np.ndarray:
    """Lift cast shadows from a photo of paper, preserving ink.

    Shadowed lightness is blended toward its retinex (illumination-free)
    estimate, and chroma inside the shadow toward the unshadowed background
    average, so gray shadow regions come back as paper. Accepts BGR or
    grayscale uint8 and returns the same layout.
    """
    grayscale = image.ndim == 2
    bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if grayscale else image

    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    lightness, a, b = cv2.split(lab)
    saturation = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[:, :, 1].astype(np.float32) / 255
    retinex = _multiscale_retinex(lightness)

    mask = _shadow_mask(lightness / 255, saturation, sensitivity, mask_blur)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.dilate(mask, kernel, iterations=1)
    mask = cv2.GaussianBlur(mask, (mask_blur, mask_blur), 0)
    mask = np.power(mask, 1.5)

    lightness_out = (1 - strength * mask) * lightness + strength * mask * retinex
    lightness_out = np.clip(lightness_out, 0, 255)

    # Pull the shadow's chroma toward the unshadowed background average so the
    # corrected area matches the paper instead of keeping the shadow's tint.
    unshadowed = 1 - mask
    a_bg = np.sum(a * unshadowed) / (np.sum(unshadowed) + 1e-6)
    b_bg = np.sum(b * unshadowed) / (np.sum(unshadowed) + 1e-6)
    a_out = (1 - strength * mask) * a + strength * mask * a_bg
    b_out = (1 - strength * mask) * b + strength * mask * b_bg

    lab_out = cv2.merge([lightness_out, a_out, b_out]).astype(np.uint8)
    result = cv2.cvtColor(lab_out, cv2.COLOR_LAB2BGR)
    return cv2.cvtColor(result, cv2.COLOR_BGR2GRAY) if grayscale else result
