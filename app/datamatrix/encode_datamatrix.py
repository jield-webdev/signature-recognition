import numpy as np
import zxingcpp

# Rendered resolution in pixels per module; callers scale the image to its
# final print size, so this only needs to be comfortably high.
SCALE = 40


def encode_datamatrix(text: str) -> np.ndarray:
    barcode = zxingcpp.create_barcode(text, zxingcpp.BarcodeFormat.DataMatrix)
    return np.array(zxingcpp.write_barcode_to_image(barcode, scale=SCALE))
