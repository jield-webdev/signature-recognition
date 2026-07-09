import json

from aruco.slots import MAX_SLOTS_PER_PAGE
from boxes.box_id import MAX_BOX_ID


def _boxes(box_id: int = 1, page: int = 0, x: float = 50, y: float = 400,
           width: float = 250, height: float = 80) -> str:
    return json.dumps(
        [{"box_id": box_id, "page": page, "x": x, "y": y, "width": width, "height": height}]
    )


def test_returns_marked_pdf(client, pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
        data={"boxes": _boxes()},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_marks_boxes_on_several_pages(client, pdf_bytes):
    boxes = json.dumps(
        [
            {"box_id": 1, "page": 0, "x": 50, "y": 400, "width": 250, "height": 80},
            {"box_id": 2, "page": 1, "x": 50, "y": 700, "width": 250, "height": 80},
        ]
    )
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=2), "application/pdf")},
        data={"boxes": boxes},
    )

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")


def test_rejects_box_id_below_range(client, pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
        data={"boxes": _boxes(box_id=0)},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid boxes:")


def test_rejects_box_id_beyond_range(client, pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
        data={"boxes": _boxes(box_id=MAX_BOX_ID + 1)},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid boxes:")


def test_accepts_max_box_id(client, pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
        data={"boxes": _boxes(box_id=MAX_BOX_ID)},
    )

    assert response.status_code == 200


def test_rejects_missing_boxes(client, pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
    )

    assert response.status_code == 422


def test_rejects_malformed_boxes_json(client, pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
        data={"boxes": "not json"},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid boxes:")


def test_rejects_empty_boxes_list(client, pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
        data={"boxes": "[]"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "At least one box is required."


def test_rejects_box_too_small(client, pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
        data={"boxes": _boxes(width=30, height=10)},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid boxes:")


def test_rejects_page_out_of_range(client, pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
        data={"boxes": _boxes(page=5)},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Page 5 does not exist. The PDF has 1 page(s)."


def test_rejects_box_outside_page_bounds(client, pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
        data={"boxes": _boxes(x=500, y=400)},  # 500 + 250 > 595 pt page width
    )

    assert response.status_code == 400
    assert "does not fit inside page" in response.json()["detail"]


def test_rejects_too_many_boxes_on_one_page(client, pdf_bytes):
    boxes = json.dumps(
        [
            {"box_id": i + 1, "page": 0, "x": 50, "y": 100, "width": 250, "height": 80}
            for i in range(MAX_SLOTS_PER_PAGE + 1)
        ]
    )
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
        data={"boxes": boxes},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        f"Page 0 has {MAX_SLOTS_PER_PAGE + 1} boxes. "
        f"A page can hold at most {MAX_SLOTS_PER_PAGE}."
    )


def test_rejects_empty_file(client):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", b"", "application/pdf")},
        data={"boxes": _boxes()},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File is empty."


def test_rejects_wrong_content_type(client):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.txt", b"hello", "text/plain")},
        data={"boxes": _boxes()},
    )

    assert response.status_code == 415


def test_rejects_malformed_pdf(client):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", b"not a pdf", "application/pdf")},
        data={"boxes": _boxes()},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Pdf Error"


def test_rejects_zero_page_pdf(client, zero_page_pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", zero_page_pdf_bytes, "application/pdf")},
        data={"boxes": _boxes()},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "PDF has no pages."


def test_rejects_encrypted_pdf(client, encrypted_pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", encrypted_pdf_bytes(), "application/pdf")},
        data={"boxes": _boxes()},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "PDF is encrypted."


def test_returns_500_when_marking_fails_unexpectedly(client, pdf_bytes, monkeypatch):
    async def boom(_doc, _boxes):
        raise RuntimeError("simulated mark_pdf failure")

    monkeypatch.setattr("handlers.mark_pdf.mark_pdf", boom)

    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
        data={"boxes": _boxes()},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to process PDF."
