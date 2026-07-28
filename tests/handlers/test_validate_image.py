import base64

import cv2
import fitz
import numpy as np

import file.read_image as read_image
from boxes.placement import BoxPlacement
from pdf.mark_pdf import mark_pdf


def _page_placement(page: fitz.Page, box_id: int, margin: float = 8) -> BoxPlacement:
    """A single box spanning the whole page except for a small margin."""
    return BoxPlacement(
        box_id=box_id,
        page=0,
        x=margin,
        y=margin,
        width=page.rect.width - 2 * margin,
        height=page.rect.height - 2 * margin,
    )


async def test_returns_detected_boxes_with_cropped_images(client, pdf_bytes):
    doc = fitz.open(stream=pdf_bytes(pages=1), filetype="pdf")
    await mark_pdf(doc, [_page_placement(doc[0], box_id=123)])
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(6, 6), colorspace=fitz.csGRAY)
    image = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)
    success, encoded_image = cv2.imencode(".png", image)

    assert success

    response = client.post(
        "/validate-image",
        files={"file": ("photo.png", encoded_image.tobytes(), "image/png")},
    )

    assert response.status_code == 200
    boxes = response.json()["boxes"]
    assert len(boxes) == 1
    assert boxes[0]["box_id"] == 123
    assert boxes[0]["is_signed"] is False
    decoded = base64.b64decode(boxes[0]["image"])
    assert decoded.startswith(b"RIFF")
    assert decoded[8:12] == b"WEBP"


async def test_reports_signed_box(client, pdf_bytes):
    doc = fitz.open(stream=pdf_bytes(pages=1), filetype="pdf")
    await mark_pdf(doc, [_page_placement(doc[0], box_id=123)])
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(6, 6), colorspace=fitz.csGRAY)
    image = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width).copy()
    h, w = image.shape
    squiggle = np.array(
        [
            [int(w * 0.2), int(h * 0.6)],
            [int(w * 0.35), int(h * 0.4)],
            [int(w * 0.5), int(h * 0.65)],
            [int(w * 0.65), int(h * 0.4)],
            [int(w * 0.8), int(h * 0.6)],
        ]
    )
    cv2.polylines(image, [squiggle], isClosed=False, color=0, thickness=6)
    success, encoded_image = cv2.imencode(".png", image)

    assert success

    response = client.post(
        "/validate-image",
        files={"file": ("photo.png", encoded_image.tobytes(), "image/png")},
    )

    assert response.status_code == 200
    boxes = response.json()["boxes"]
    assert len(boxes) == 1
    assert boxes[0]["box_id"] == 123
    assert boxes[0]["is_signed"] is True


def test_returns_no_boxes_for_unmarked_image(client):
    image = np.full((64, 64, 3), 255, dtype=np.uint8)
    success, encoded_image = cv2.imencode(".png", image)

    assert success

    response = client.post(
        "/validate-image",
        files={"file": ("photo.png", encoded_image.tobytes(), "image/png")},
    )

    assert response.status_code == 200
    assert response.json() == {"boxes": []}


def test_rejects_empty_file(client):
    response = client.post(
        "/validate-image",
        files={"file": ("signature.png", b"", "image/png")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File is empty."


def test_rejects_wrong_content_type(client):
    response = client.post(
        "/validate-image",
        files={"file": ("signature.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 415


def test_rejects_malformed_image(client):
    response = client.post(
        "/validate-image",
        files={"file": ("signature.png", b"not an image", "image/png")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File content does not match declared content type."


def test_rejects_image_larger_than_upload_limit(client, monkeypatch):
    monkeypatch.setattr(read_image, "MAX_UPLOAD_BYTES", 4, raising=False)

    response = client.post(
        "/validate-image",
        files={"file": ("signature.png", b"12345", "image/png")},
    )

    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"]
