import cv2
import fitz
import numpy as np
import zxingcpp

from aruco.dictionary import ARUCO_DICT
from aruco.mark_pdf import mark_pdf


def _rasterize(page: fitz.Page, zoom: int = 6) -> np.ndarray:
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csGRAY)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)


async def test_inserts_marker_pair_and_datamatrix_on_first_page(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes(pages=1), filetype="pdf")

    marked = await mark_pdf(doc, box_id=1)

    assert marked is doc
    assert len(marked[0].get_images()) == 3


async def test_only_marks_the_first_page(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes(pages=3), filetype="pdf")

    await mark_pdf(doc, box_id=1)

    assert len(doc[0].get_images()) == 3
    assert len(doc[1].get_images()) == 0
    assert len(doc[2].get_images()) == 0


async def test_stamped_page_decodes_back(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes(pages=1), filetype="pdf")

    await mark_pdf(doc, box_id=250000)
    image = _rasterize(doc[0])

    detector = cv2.aruco.ArucoDetector(ARUCO_DICT, cv2.aruco.DetectorParameters())
    _, ids, _ = detector.detectMarkers(image)
    assert ids is not None and sorted(ids.flatten().tolist()) == [0, 1]

    result = zxingcpp.read_barcode(image, formats=zxingcpp.BarcodeFormat.DataMatrix)
    assert result is not None and result.text == "250000"
