import cv2
import numpy as np


def test_returns_validated_image(client):
    image = np.full((8, 8, 3), 255, dtype=np.uint8)
    success, encoded_image = cv2.imencode(".png", image)

    assert success

    response = client.post(
        "/validate-image",
        files={"file": ("signature.png", encoded_image.tobytes(), "image/png")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


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
