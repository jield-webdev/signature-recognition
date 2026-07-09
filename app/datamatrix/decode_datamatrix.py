import zxingcpp
from cv2.typing import MatLike


def decode_datamatrix(image: MatLike) -> str | None:
    """Read a DataMatrix from an image, returning its text or None."""
    result = zxingcpp.read_barcode(image, formats=zxingcpp.BarcodeFormat.DataMatrix)
    return None if result is None else result.text
