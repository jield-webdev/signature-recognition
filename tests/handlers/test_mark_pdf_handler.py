from aruco.utils import MAX_BOX_ID


def test_returns_marked_pdf(client, pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
        data={"box_id": "1"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_rejects_box_id_below_range(client, pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
        data={"box_id": "0"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == f"Box id 0 is not valid. Must be between 1 and {MAX_BOX_ID}."


def test_rejects_box_id_beyond_range(client, pdf_bytes):
    invalid_id = MAX_BOX_ID + 1
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
        data={"box_id": str(invalid_id)},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == f"Box id {invalid_id} is not valid. Must be between 1 and {MAX_BOX_ID}."


def test_accepts_max_box_id(client, pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
        data={"box_id": str(MAX_BOX_ID)},
    )

    assert response.status_code == 200


def test_rejects_missing_box_id(client, pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
    )

    assert response.status_code == 422


def test_rejects_empty_file(client):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", b"", "application/pdf")},
        data={"box_id": "1"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File is empty."


def test_rejects_wrong_content_type(client):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.txt", b"hello", "text/plain")},
        data={"box_id": "1"},
    )

    assert response.status_code == 415


def test_rejects_malformed_pdf(client):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", b"not a pdf", "application/pdf")},
        data={"box_id": "1"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Pdf Error"


def test_rejects_zero_page_pdf(client, zero_page_pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", zero_page_pdf_bytes, "application/pdf")},
        data={"box_id": "1"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "PDF has no pages."


def test_rejects_encrypted_pdf(client, encrypted_pdf_bytes):
    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", encrypted_pdf_bytes(), "application/pdf")},
        data={"box_id": "1"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "PDF is encrypted."


def test_returns_500_when_marking_fails_unexpectedly(client, pdf_bytes, monkeypatch):
    async def boom(_doc, _box_id):
        raise RuntimeError("simulated mark_pdf failure")

    monkeypatch.setattr("handlers.mark_pdf.mark_pdf", boom)

    response = client.post(
        "/mark-pdf",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
        data={"box_id": "1"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to process PDF."
