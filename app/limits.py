import os


def _positive_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        limit = int(value)
    except ValueError as error:
        raise RuntimeError(f"{name} must be a positive integer.") from error
    if limit <= 0:
        raise RuntimeError(f"{name} must be a positive integer.")
    return limit


MAX_UPLOAD_BYTES = _positive_int("MAX_UPLOAD_BYTES", 20 * 1024 * 1024)
MAX_REQUEST_BYTES = _positive_int("MAX_REQUEST_BYTES", MAX_UPLOAD_BYTES + 1024 * 1024)
MAX_IMAGE_PIXELS = _positive_int("MAX_IMAGE_PIXELS", 50_000_000)
MAX_PDF_PAGES = _positive_int("MAX_PDF_PAGES", 100)
MAX_BOXES_JSON_BYTES = _positive_int("MAX_BOXES_JSON_BYTES", 1024 * 1024)
MAX_BOXES_PER_REQUEST = _positive_int("MAX_BOXES_PER_REQUEST", 100)
MAX_RECTIFIED_BOX_PIXELS = _positive_int("MAX_RECTIFIED_BOX_PIXELS", 16_000_000)
MAX_TOTAL_RECTIFIED_PIXELS = _positive_int(
    "MAX_TOTAL_RECTIFIED_PIXELS", MAX_IMAGE_PIXELS
)
