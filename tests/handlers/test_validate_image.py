import base64

import cv2
import fitz
import numpy as np

from aruco.mark_pdf import mark_pdf


async def test_returns_detected_boxes_with_cropped_images(client, pdf_bytes):
    doc = fitz.open(stream=pdf_bytes(pages=1), filetype="pdf")
    await mark_pdf(doc, box_id=123)
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
    assert base64.b64decode(boxes[0]["image"]).startswith(b"\x89PNG")


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
    assert response.json()["detail"] == "Invalid image file."
