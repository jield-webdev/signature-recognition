import cv2
import fitz
import numpy as np
import zxingcpp

from aruco.dictionary import ARUCO_DICT
from boxes.placement import BoxPlacement
from pdf.mark_pdf import mark_pdf


def _rasterize(page: fitz.Page, zoom: int = 6) -> np.ndarray:
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csGRAY)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)


def _placement(box_id: int = 1, page: int = 0, x: float = 50, y: float = 400) -> BoxPlacement:
    return BoxPlacement(box_id=box_id, page=page, x=x, y=y, width=250, height=80)


async def test_inserts_marker_pair_and_datamatrix_per_placement(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes(pages=1), filetype="pdf")

    marked = await mark_pdf(doc, [_placement()])

    assert marked is doc
    assert len(marked[0].get_images()) == 3


async def test_only_marks_the_requested_pages(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes(pages=3), filetype="pdf")

    await mark_pdf(doc, [_placement(box_id=1, page=0), _placement(box_id=2, page=2)])

    assert len(doc[0].get_images()) == 3
    assert len(doc[1].get_images()) == 0
    assert len(doc[2].get_images()) == 3


async def test_stamped_page_decodes_back(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes(pages=1), filetype="pdf")

    await mark_pdf(doc, [_placement(box_id=250000)])
    image = _rasterize(doc[0])

    detector = cv2.aruco.ArucoDetector(ARUCO_DICT, cv2.aruco.DetectorParameters())
    _, ids, _ = detector.detectMarkers(image)
    assert ids is not None and sorted(ids.flatten().tolist()) == [0, 1]

    result = zxingcpp.read_barcode(image, formats=zxingcpp.BarcodeFormat.DataMatrix)
    assert result is not None and result.text == "250000"


async def test_slots_advance_per_box_and_restart_per_page(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes(pages=2), filetype="pdf")

    await mark_pdf(
        doc,
        [
            _placement(box_id=1, page=0, y=100),
            _placement(box_id=2, page=0, y=400),
            _placement(box_id=3, page=1, y=100),
        ],
    )

    detector = cv2.aruco.ArucoDetector(ARUCO_DICT, cv2.aruco.DetectorParameters())
    _, first_page_ids, _ = detector.detectMarkers(_rasterize(doc[0]))
    assert sorted(first_page_ids.flatten().tolist()) == [0, 1, 2, 3]

    _, second_page_ids, _ = detector.detectMarkers(_rasterize(doc[1]))
    assert sorted(second_page_ids.flatten().tolist()) == [0, 1]
